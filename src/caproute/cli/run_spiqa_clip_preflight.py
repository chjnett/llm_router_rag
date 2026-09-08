from __future__ import annotations

import argparse
import io
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as functional
from PIL import Image
from transformers import AutoModel, AutoTokenizer, CLIPModel, CLIPProcessor

from caproute.cli.run_qasper_dense import encode
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def score_features(scores: np.ndarray) -> dict[str, float]:
    ordered = np.sort(np.asarray(scores, dtype=np.float64))[::-1]
    shifted = ordered - ordered.max()
    probabilities = np.exp(shifted) / np.exp(shifted).sum()
    entropy = -float(np.sum(probabilities * np.log(probabilities + 1e-12)))
    return {
        "top_score": float(ordered[0]),
        "top_margin": float(ordered[0] - ordered[1]) if len(ordered) > 1 else 0.0,
        "normalized_entropy": entropy / float(np.log(len(ordered))) if len(ordered) > 1 else 0.0,
    }


def freeze_balanced_sample(
    dataset: dict,
    archive_names: set[str],
    table_count: int,
    figure_count: int,
    excluded_paper_ids: set[str] | None = None,
) -> list[dict]:
    excluded_paper_ids = excluded_paper_ids or set()
    selected = {"table": [], "figure": []}
    for paper_id in sorted(dataset):
        if paper_id in excluded_paper_ids:
            continue
        paper = dataset[paper_id]
        for qa_index, qa in enumerate(paper["qa"]):
            reference = qa["reference"]
            metadata = paper["all_figures"].get(reference)
            if metadata is None:
                continue
            kind = metadata.get("content_type")
            archive_path = f"SPIQA_testA_Images_224px/{paper_id}/{reference}"
            limit = table_count if kind == "table" else figure_count if kind == "figure" else 0
            if limit and len(selected[kind]) < limit and archive_path in archive_names:
                selected[kind].append({"paper_id": paper_id, "qa_index": qa_index, "question": qa["question"],
                                       "reference": reference, "content_type": kind})
    return selected["table"] + selected["figure"]


def clip_image_embeddings(images: list[Image.Image], processor, model, device, batch_size: int) -> np.ndarray:
    rows = []
    for start in range(0, len(images), batch_size):
        inputs = processor(images=images[start:start + batch_size], return_tensors="pt")
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.inference_mode():
            output = functional.normalize(model.get_image_features(**inputs), p=2, dim=1)
        rows.append(output.cpu().numpy())
    return np.concatenate(rows)


def clip_text_embedding(text: str, processor, model, device) -> np.ndarray:
    inputs = processor(text=[text], padding=True, truncation=True, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items() if key in {"input_ids", "attention_mask"}}
    with torch.inference_mode():
        output = functional.normalize(model.get_text_features(**inputs), p=2, dim=1)
    return output[0].cpu().numpy()


def main() -> None:
    parser = argparse.ArgumentParser(description="SPIQA caption-vs-CLIP visual retrieval signal preflight")
    parser.add_argument("--config", default="configs/p1v_spiqa_clip_preflight.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    dataset = json.loads(Path(config["dataset"]["json"]).read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

    caption_config = config["caption_model"]
    caption_tokenizer = AutoTokenizer.from_pretrained(caption_config["local_path"], local_files_only=True)
    caption_model = AutoModel.from_pretrained(caption_config["local_path"], local_files_only=True).to(device).eval()
    visual_config = config["visual_model"]
    visual_processor = CLIPProcessor.from_pretrained(visual_config["local_path"], local_files_only=True)
    visual_model = CLIPModel.from_pretrained(visual_config["local_path"], local_files_only=True).to(device).eval()

    details = []
    paper_cache = {}
    indexing_seconds = 0.0
    query_seconds = 0.0
    with zipfile.ZipFile(config["dataset"]["images_zip"]) as archive:
        archive_names = set(archive.namelist())
        frozen_manifest = config["selection"].get("sample_manifest")
        if frozen_manifest:
            sample = json.loads(Path(frozen_manifest).read_text(encoding="utf-8"))
        else:
            excluded_paper_ids = set()
            excluded_manifest = config["selection"].get("excluded_manifest")
            if excluded_manifest:
                excluded_rows = json.loads(Path(excluded_manifest).read_text(encoding="utf-8"))
                excluded_paper_ids = {row["paper_id"] for row in excluded_rows}
            sample = freeze_balanced_sample(dataset, archive_names, int(config["selection"]["table_questions"]),
                                            int(config["selection"]["figure_questions"]), excluded_paper_ids)
        for row in sample:
            paper_id = row["paper_id"]
            if paper_id not in paper_cache:
                references = [name for name in sorted(dataset[paper_id]["all_figures"])
                              if f"SPIQA_testA_Images_224px/{paper_id}/{name}" in archive_names]
                captions = [dataset[paper_id]["all_figures"][name].get("caption", "") for name in references]
                images = []
                for reference in references:
                    raw = archive.read(f"SPIQA_testA_Images_224px/{paper_id}/{reference}")
                    with Image.open(io.BytesIO(raw)) as image:
                        images.append(image.convert("RGB"))
                started = time.perf_counter()
                caption_embeddings = encode(captions, caption_tokenizer, caption_model, device,
                                            int(caption_config["batch_size"]), int(caption_config["max_length"]))
                image_embeddings = clip_image_embeddings(images, visual_processor, visual_model, device,
                                                         int(visual_config["batch_size"]))
                if device.type == "cuda":
                    torch.cuda.synchronize()
                indexing_seconds += time.perf_counter() - started
                paper_cache[paper_id] = references, caption_embeddings, image_embeddings
            references, caption_embeddings, image_embeddings = paper_cache[paper_id]
            relevant = {references.index(row["reference"])}
            started = time.perf_counter()
            caption_query = encode([caption_config["query_prefix"] + row["question"]], caption_tokenizer,
                                   caption_model, device, 1, int(caption_config["max_length"]))[0]
            visual_query = clip_text_embedding(row["question"], visual_processor, visual_model, device)
            if device.type == "cuda":
                torch.cuda.synchronize()
            query_seconds += time.perf_counter() - started
            caption_scores = caption_embeddings @ caption_query
            visual_scores = image_embeddings @ visual_query
            caption_ranking = np.argsort(-caption_scores, kind="stable").tolist()
            visual_ranking = np.argsort(-visual_scores, kind="stable").tolist()
            caption_metrics = retrieval_metrics(caption_ranking, relevant)
            visual_metrics = retrieval_metrics(visual_ranking, relevant)
            oracle_ranking = caption_ranking if caption_metrics["mrr"] >= visual_metrics["mrr"] else visual_ranking
            details.append({**row, "candidate_images": len(references), "caption": caption_metrics,
                            "visual": visual_metrics, "oracle_selective": retrieval_metrics(oracle_ranking, relevant),
                            "caption_signal": score_features(caption_scores),
                            "visual_signal": score_features(visual_scores),
                            "caption_top": [references[index] for index in caption_ranking[:5]],
                            "visual_top": [references[index] for index in visual_ranking[:5]]})

    methods = {method: mean_metrics([row[method] for row in details]) for method in ("caption", "visual", "oracle_selective")}
    by_type = {kind: {method: mean_metrics([row[method] for row in details if row["content_type"] == kind])
                      for method in methods} for kind in ("table", "figure")}
    baseline_best = max(methods["caption"]["recall_at_1"], methods["visual"]["recall_at_1"])
    gate = config["gate"]
    summary = {
        "questions": len(details), "papers": len(paper_cache),
        "reference_image_coverage": len(details) / len(sample) if sample else 0.0,
        "images_indexed": sum(len(value[0]) for value in paper_cache.values()),
        "indexing_seconds": indexing_seconds, "query_seconds": query_seconds,
        "peak_vram_allocated_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else None,
        "methods": methods, "by_type": by_type,
    }
    summary["gate_passed"] = (
        summary["questions"] >= int(gate["min_questions"])
        and summary["reference_image_coverage"] >= float(gate["min_reference_image_coverage"])
        and max(methods["visual"]["recall_at_5"], methods["oracle_selective"]["recall_at_5"]) >= float(gate["min_recall_at_5"])
        and methods["oracle_selective"]["recall_at_1"] - baseline_best >= float(gate["min_oracle_recall_at_1_gain"])
        and (summary["peak_vram_allocated_bytes"] or 0) <= int(gate["max_peak_vram_bytes"])
    )
    output = {"config": config, "config_sha256": config_hash(config),
              "dataset_sha256": sha256_file(config["dataset"]["json"]),
              "images_zip_sha256": sha256_file(config["dataset"]["images_zip"]),
              "summary": summary, "questions": details}
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    (target.parent / "sample_manifest.json").write_text(json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
