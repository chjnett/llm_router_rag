from __future__ import annotations

import argparse
import time
from pathlib import Path

import torch
import pymupdf
from PIL import Image
from transformers import AutoImageProcessor, TableTransformerForObjectDetection

from caproute.benchmark.harness import percentile
from caproute.core.config import config_hash, load_config
from caproute.core.io import write_json, write_jsonl
from caproute.datasets.pubtables import load_pubtables_subset


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--config", default="configs/tatr_detection_preflight.yaml")
    args = cli.parse_args()
    config_path = Path(args.config).resolve()
    root, cfg = config_path.parent.parent, load_config(config_path)
    dataset, model_cfg = cfg["dataset"], cfg["model"]
    resolve = lambda value: (root / value).resolve()
    samples = load_pubtables_subset(
        resolve(dataset["annotations"]), resolve(dataset["split_file"]),
        resolve(dataset["image_root"]), resolve(dataset["pdf_root"]),
        int(dataset["sample_size"]), int(cfg["seed"]), True,
        set(dataset.get("exclude_document_ids", [])),
    )
    device = torch.device(model_cfg["device"] if torch.cuda.is_available() else "cpu")
    processor = AutoImageProcessor.from_pretrained(model_cfg["id"])
    model = TableTransformerForObjectDetection.from_pretrained(model_cfg["id"], use_safetensors=True).to(device).eval()
    torch.cuda.reset_peak_memory_stats() if device.type == "cuda" else None
    rows, latencies = [], []
    with torch.inference_mode():
        for sample in samples:
            if sample.image_path.exists():
                image = Image.open(sample.image_path).convert("RGB")
            else:
                with pymupdf.open(sample.item.source_path) as pdf:
                    pixmap = pdf[sample.item.page_index or 0].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            inputs = {key: value.to(device) for key, value in processor(images=image, return_tensors="pt").items()}
            if device.type == "cuda": torch.cuda.synchronize()
            started = time.perf_counter()
            outputs = model(**inputs)
            if device.type == "cuda": torch.cuda.synchronize()
            latency = 1000 * (time.perf_counter() - started)
            target = torch.tensor([[image.height, image.width]], device=device)
            result = processor.post_process_object_detection(outputs, threshold=float(model_cfg["threshold"]), target_sizes=target)[0]
            predicted = len(result["scores"])
            expected = len(sample.ground_truth.get("table_boxes_xyxy", []))
            score = 1.0 if predicted == expected else (2 * min(predicted, expected) / (predicted + expected) if predicted + expected else 1.0)
            rows.append({"document_id": sample.item.document_id, "page_index": sample.item.page_index,
                         "expected_tables": expected, "predicted_tables": predicted,
                         "table_count_f1_proxy": score, "latency_ms": latency})
            latencies.append(latency)
    summary = {
        "config_hash": config_hash(cfg), "model": model_cfg["id"], "threshold": model_cfg["threshold"],
        "completed": len(rows), "table_count_f1_proxy_mean": sum(row["table_count_f1_proxy"] for row in rows) / len(rows),
        "latency_ms_p50": percentile(latencies, 0.5), "latency_ms_p95": percentile(latencies, 0.95),
        "peak_vram_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else 0,
    }
    output = resolve(cfg["outputs"]["root"])
    write_json(output / "summary.json", summary)
    write_jsonl(output / "predictions.jsonl", rows)
    print(summary)


if __name__ == "__main__":
    main()
