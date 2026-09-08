from __future__ import annotations

import argparse
import time
from pathlib import Path

import pymupdf
import torch
from PIL import Image
from transformers import AutoImageProcessor, TableTransformerForObjectDetection

from caproute.benchmark.harness import percentile
from caproute.core.config import config_hash, load_config
from caproute.core.io import write_json, write_jsonl
from caproute.datasets.pubtables import load_pubtables_subset
from caproute.evaluation.grits import grits_loc, grits_top
from caproute.evaluation.structure_shape import _normalize_cells, ground_truth_cells, structure_files_for_page


def detections(processor, model, image, threshold, device):
    inputs = {key: value.to(device) for key, value in processor(images=image, return_tensors="pt").items()}
    outputs = model(**inputs)
    target = torch.tensor([[image.height, image.width]], device=device)
    result = processor.post_process_object_detection(outputs, threshold=threshold, target_sizes=target)[0]
    return [(model.config.id2label[int(label)], [float(v) for v in box])
            for label, box in zip(result["labels"], result["boxes"])]


def grid_cells(items, offset_x=0.0, offset_y=0.0):
    rows = sorted((box for label, box in items if label == "table row"), key=lambda box: box[1])
    columns = sorted((box for label, box in items if label == "table column"), key=lambda box: box[0])
    cells = []
    for row_index, row in enumerate(rows):
        for column_index, column in enumerate(columns):
            box = [column[0] + offset_x, row[1] + offset_y, column[2] + offset_x, row[3] + offset_y]
            cells.append({"row_nums": [row_index], "column_nums": [column_index], "bbox": box})
    return _normalize_cells(cells)


def render_page(sample):
    if sample.image_path.exists():
        return Image.open(sample.image_path).convert("RGB")
    with pymupdf.open(sample.item.source_path) as pdf:
        pixmap = pdf[sample.item.page_index or 0].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--config", default="configs/tatr_structure_preflight.yaml")
    args = cli.parse_args()
    config_path = Path(args.config).resolve()
    root, cfg = config_path.parent.parent, load_config(config_path)
    data, model_cfg = cfg["dataset"], cfg["models"]
    resolve = lambda value: (root / value).resolve()
    samples = load_pubtables_subset(resolve(data["annotations"]), resolve(data["split_file"]),
        resolve(data["image_root"]), resolve(data["pdf_root"]), int(data["sample_size"]),
        int(cfg["seed"]), True, set(data.get("exclude_document_ids", [])))
    device = torch.device(model_cfg["device"] if torch.cuda.is_available() else "cpu")
    det_processor = AutoImageProcessor.from_pretrained(model_cfg["detection"], use_fast=False)
    str_processor = AutoImageProcessor.from_pretrained(model_cfg["structure"], use_fast=False)
    det_model = TableTransformerForObjectDetection.from_pretrained(model_cfg["detection"], use_safetensors=True).to(device).eval()
    str_model = TableTransformerForObjectDetection.from_pretrained(model_cfg["structure"], use_safetensors=True).to(device).eval()
    torch.cuda.reset_peak_memory_stats() if device.type == "cuda" else None
    rows, latencies, tops, locs = [], [], [], []
    with torch.inference_mode():
        for sample in samples:
            if device.type == "cuda": torch.cuda.synchronize()
            started = time.perf_counter()
            image = render_page(sample)
            tables = sorted((box for label, box in detections(det_processor, det_model, image,
                            float(model_cfg["detection_threshold"]), device) if label in {"table", "table rotated"}), key=lambda b: (b[1], b[0]))
            predictions = []
            padding = int(model_cfg["crop_padding"])
            for box in tables:
                x0, y0 = max(0, int(box[0]) - padding), max(0, int(box[1]) - padding)
                x1, y1 = min(image.width, int(box[2]) + padding), min(image.height, int(box[3]) + padding)
                crop = image.crop((x0, y0, x1, y1))
                items = detections(str_processor, str_model, crop, float(model_cfg["structure_threshold"]), device)
                predictions.append(grid_cells(items, x0, y0))
            if device.type == "cuda": torch.cuda.synchronize()
            latency = 1000 * (time.perf_counter() - started)
            paths = structure_files_for_page(resolve(data["detection_root"]), resolve(data["structure_root"]),
                                             sample.item.document_id, int(sample.item.page_index or 0))
            truths = [ground_truth_cells(path) for path in paths if path.exists()]
            page_top, page_loc = [], []
            for index in range(max(len(truths), len(predictions))):
                truth = truths[index] if index < len(truths) else []
                prediction = predictions[index] if index < len(predictions) else []
                page_top.append(grits_top(truth, prediction)[0]); page_loc.append(grits_loc(truth, prediction)[0])
            top = sum(page_top) / len(page_top) if page_top else 0.0
            loc = sum(page_loc) / len(page_loc) if page_loc else 0.0
            tops.append(top); locs.append(loc); latencies.append(latency)
            rows.append({"document_id": sample.item.document_id, "page_index": sample.item.page_index,
                         "truth_tables": len(truths), "predicted_tables": len(predictions),
                         "grits_top": top, "grits_loc": loc, "latency_ms": latency})
    summary = {"config_hash": config_hash(cfg), "completed": len(rows),
        "exact_table_count_rate": sum(r["truth_tables"] == r["predicted_tables"] for r in rows) / len(rows),
        "grits_top_mean": sum(tops) / len(tops), "grits_loc_mean": sum(locs) / len(locs),
        "latency_ms_p50": percentile(latencies, .5), "latency_ms_p95": percentile(latencies, .95),
        "peak_vram_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else 0}
    checks = {"grits_top": summary["grits_top_mean"] >= cfg["gate"]["min_grits_top"],
              "grits_loc": summary["grits_loc_mean"] >= cfg["gate"]["min_grits_loc"],
              "latency": summary["latency_ms_p50"] < cfg["gate"]["max_latency_ms_p50"]}
    summary.update({"gate_checks": checks, "gate": "PASS" if all(checks.values()) else "FAIL"})
    output = resolve(cfg["outputs"]["root"]); write_json(output / "summary.json", summary); write_jsonl(output / "predictions.jsonl", rows)
    print(summary)


if __name__ == "__main__": main()
