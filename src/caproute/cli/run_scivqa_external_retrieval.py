from __future__ import annotations

import argparse
import io
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sentence_transformers import MultiVectorEncoder
from transformers import AutoModel, AutoTokenizer

from caproute.cli.run_qasper_dense import encode
from caproute.cli.run_spiqa_clip_preflight import score_features
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen SciVQA caption-vs-ColSmol external retrieval")
    parser.add_argument("--config", default="configs/r3_scivqa_external_retrieval.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    manifest_path = Path(config["dataset"]["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    corpus = manifest["corpus"]
    queries = manifest["queries"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

    caption_config = config["caption_model"]
    tokenizer = AutoTokenizer.from_pretrained(caption_config["local_path"], local_files_only=True)
    caption_model = AutoModel.from_pretrained(caption_config["local_path"], local_files_only=True).to(device).eval()
    strong_config = config["strong_model"]
    strong_model = MultiVectorEncoder(
        strong_config["id"], cache_folder=strong_config["cache_folder"],
        local_files_only=bool(strong_config["local_files_only"]), device=str(device),
    )

    with zipfile.ZipFile(config["dataset"]["images_zip"]) as archive:
        images = []
        for row in corpus:
            raw = archive.read(row["archive_path"])
            with Image.open(io.BytesIO(raw)) as image:
                images.append(image.convert("RGB"))

    started = time.perf_counter()
    caption_embeddings = encode(
        [row["caption"] for row in corpus], tokenizer, caption_model, device,
        int(caption_config["batch_size"]), int(caption_config["max_length"]),
    )
    document_embeddings = strong_model.encode_document(
        images, batch_size=int(strong_config["document_batch_size"]),
        show_progress_bar=True, device=str(device),
    )
    if device.type == "cuda":
        torch.cuda.synchronize()
    indexing_seconds = time.perf_counter() - started

    output_root = Path(config["outputs"]["root"])
    embedding_root = output_root / "embeddings"
    embedding_root.mkdir(parents=True, exist_ok=True)
    arrays = {f"image_{index}": embedding.detach().float().cpu().numpy()
              for index, embedding in enumerate(document_embeddings)}
    np.savez_compressed(embedding_root / "colsmol_documents.npz", **arrays)
    np.savez_compressed(embedding_root / "caption_documents.npz", embeddings=caption_embeddings)

    started = time.perf_counter()
    question_texts = [row["question"] for row in queries]
    caption_queries = encode(
        [caption_config["query_prefix"] + text for text in question_texts], tokenizer, caption_model,
        device, int(caption_config["batch_size"]), int(caption_config["max_length"]),
    )
    strong_queries = strong_model.encode_query(
        question_texts, batch_size=int(strong_config["query_batch_size"]),
        show_progress_bar=True, device=str(device),
    )
    details = []
    similarity_batch_size = int(strong_config["similarity_batch_size"])
    for start in range(0, len(queries), similarity_batch_size):
        stop = min(start + similarity_batch_size, len(queries))
        strong_scores_batch = strong_model.similarity(
            strong_queries[start:stop], document_embeddings
        )
        if torch.is_tensor(strong_scores_batch):
            strong_scores_batch = strong_scores_batch.detach().float().cpu().numpy()
        for offset, row in enumerate(queries[start:stop]):
            index = start + offset
            caption_scores = caption_embeddings @ caption_queries[index]
            strong_scores = np.asarray(strong_scores_batch[offset])
            caption_ranking = np.argsort(-caption_scores, kind="stable").tolist()
            strong_ranking = np.argsort(-strong_scores, kind="stable").tolist()
            relevant = {int(value) for value in row.get("relevant_indices", [row.get("relevant_index")])}
            relevant.discard(None)
            caption_metrics = retrieval_metrics(caption_ranking, relevant)
            strong_metrics = retrieval_metrics(strong_ranking, relevant)
            oracle_ranking = caption_ranking if caption_metrics["mrr"] >= strong_metrics["mrr"] else strong_ranking
            details.append({
                **row,
                "content_type": "figure",
                "candidate_images": len(corpus),
                "caption": caption_metrics,
                "colsmol": strong_metrics,
                "oracle_selective": retrieval_metrics(oracle_ranking, relevant),
                "caption_signal": score_features(caption_scores),
                "colsmol_signal": score_features(strong_scores),
                "caption_top": caption_ranking[:10],
                "colsmol_top": strong_ranking[:10],
            })
    if device.type == "cuda":
        torch.cuda.synchronize()
    query_seconds = time.perf_counter() - started

    methods = {name: mean_metrics([row[name] for row in details])
               for name in ("caption", "colsmol", "oracle_selective")}
    visual_rows = [row for row in details if row["qa_pair_type"].endswith(" visual")]
    nonvisual_rows = [row for row in details if row["qa_pair_type"].endswith(" non-visual")]
    by_question_signal = {
        "visual": {name: mean_metrics([row[name] for row in visual_rows]) for name in methods},
        "non_visual": {name: mean_metrics([row[name] for row in nonvisual_rows]) for name in methods},
    }
    gate = config["gate"]
    best_baseline = max(methods["caption"]["recall_at_1"], methods["colsmol"]["recall_at_1"])
    summary = {
        "questions": len(details),
        "papers": manifest["contract"]["papers"],
        "images_indexed": len(corpus),
        "indexing_seconds": indexing_seconds,
        "query_seconds": query_seconds,
        "peak_vram_allocated_bytes": torch.cuda.max_memory_allocated() if device.type == "cuda" else None,
        "compressed_document_index_bytes": sum(path.stat().st_size for path in embedding_root.glob("*.npz")),
        "methods": methods,
        "by_question_signal": by_question_signal,
    }
    summary["gate_passed"] = (
        len(details) >= int(gate["min_questions"])
        and max(methods["caption"]["recall_at_5"], methods["colsmol"]["recall_at_5"]) >= float(gate["min_recall_at_5"])
        and methods["oracle_selective"]["recall_at_1"] - best_baseline >= float(gate["min_oracle_recall_at_1_gain"])
        and (summary["peak_vram_allocated_bytes"] or 0) <= int(gate["max_peak_vram_bytes"])
    )
    output = {
        "config": config,
        "config_sha256": config_hash(config),
        "manifest_sha256": sha256_file(manifest_path),
        "summary": summary,
        "questions": details,
    }
    target = output_root / "results.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
