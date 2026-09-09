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

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics
from caproute.cli.run_spiqa_clip_preflight import score_features


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ColSmol on the frozen SPIQA 50-question preflight")
    parser.add_argument("--config", default="configs/p1v_spiqa_colsmol_preflight.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    dataset = json.loads(Path(config["dataset"]["json"]).read_text(encoding="utf-8"))
    sample = json.loads(Path(config["dataset"]["sample_manifest"]).read_text(encoding="utf-8"))
    clip = json.loads(Path(config["dataset"]["clip_results"]).read_text(encoding="utf-8"))
    caption_by_key = {(row["paper_id"], row["qa_index"]): row for row in clip["questions"]}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    model_config = config["model"]
    model = MultiVectorEncoder(model_config["id"], cache_folder=model_config["cache_folder"],
                               local_files_only=bool(model_config["local_files_only"]), device=device)
    output_root = Path(config["outputs"]["root"])
    embedding_root = output_root / "embeddings"
    embedding_root.mkdir(parents=True, exist_ok=True)
    paper_cache = {}
    indexing_seconds = query_seconds = 0.0
    details = []
    image_archive_prefix = str(
        config["dataset"].get("image_archive_prefix", "SPIQA_testA_Images_224px")
    ).rstrip("/")

    with zipfile.ZipFile(config["dataset"]["images_zip"]) as archive:
        archive_names = set(archive.namelist())
        for row in sample:
            paper_id = row["paper_id"]
            if paper_id not in paper_cache:
                references = [name for name in sorted(dataset[paper_id]["all_figures"])
                              if f"{image_archive_prefix}/{paper_id}/{name}" in archive_names]
                images = []
                for reference in references:
                    raw = archive.read(f"{image_archive_prefix}/{paper_id}/{reference}")
                    with Image.open(io.BytesIO(raw)) as image:
                        images.append(image.convert("RGB"))
                started = time.perf_counter()
                document_embeddings = model.encode_document(images, batch_size=int(model_config["batch_size"]),
                                                              show_progress_bar=False, device=device)
                if device == "cuda":
                    torch.cuda.synchronize()
                indexing_seconds += time.perf_counter() - started
                arrays = {f"image_{index}": embedding.detach().float().cpu().numpy()
                          for index, embedding in enumerate(document_embeddings)}
                np.savez_compressed(embedding_root / f"{paper_id}_documents.npz", **arrays)
                paper_cache[paper_id] = references, document_embeddings
            references, document_embeddings = paper_cache[paper_id]
            started = time.perf_counter()
            query_embedding = model.encode_query([row["question"]], batch_size=1, show_progress_bar=False, device=device)[0]
            scores = model.similarity([query_embedding], document_embeddings)[0]
            if device == "cuda":
                torch.cuda.synchronize()
            query_seconds += time.perf_counter() - started
            np.savez_compressed(embedding_root / f"{paper_id}_{row['qa_index']}_query.npz",
                                embedding=query_embedding.detach().float().cpu().numpy())
            ranking = torch.argsort(scores, descending=True).cpu().tolist()
            relevant = {references.index(row["reference"])}
            colsmol_metrics = retrieval_metrics(ranking, relevant)
            caption_row = caption_by_key[(paper_id, row["qa_index"])]
            caption_metrics = caption_row["caption"]
            oracle = colsmol_metrics if colsmol_metrics["mrr"] > caption_metrics["mrr"] else caption_metrics
            details.append({**row, "candidate_images": len(references), "caption": caption_metrics,
                            "colsmol": colsmol_metrics, "oracle_selective": oracle,
                            "caption_signal": caption_row["caption_signal"],
                            "colsmol_signal": score_features(scores.detach().float().cpu().numpy()),
                            "colsmol_scores": [float(value) for value in scores.cpu()],
                            "colsmol_top": [references[index] for index in ranking[:5]]})

    methods = {method: mean_metrics([row[method] for row in details]) for method in ("caption", "colsmol", "oracle_selective")}
    by_type = {kind: {method: mean_metrics([row[method] for row in details if row["content_type"] == kind])
                      for method in methods} for kind in ("table", "figure")}
    baseline_best = max(methods["caption"]["recall_at_1"], methods["colsmol"]["recall_at_1"])
    index_bytes = sum(path.stat().st_size for path in embedding_root.glob("*_documents.npz"))
    summary = {
        "questions": len(details), "papers": len(paper_cache),
        "unique_images_indexed": sum(len(value[0]) for value in paper_cache.values()),
        "indexing_seconds": indexing_seconds, "query_seconds": query_seconds,
        "compressed_document_index_bytes": index_bytes,
        "peak_vram_allocated_bytes": torch.cuda.max_memory_allocated() if device == "cuda" else None,
        "methods": methods, "by_type": by_type,
    }
    gate = config["gate"]
    summary["gate_passed"] = (
        summary["questions"] >= int(gate["min_questions"])
        and methods["colsmol"]["recall_at_5"] >= float(gate["min_recall_at_5"])
        and methods["oracle_selective"]["recall_at_1"] - baseline_best >= float(gate["min_oracle_recall_at_1_gain"])
        and (summary["peak_vram_allocated_bytes"] or 0) <= int(gate["max_peak_vram_bytes"])
    )
    output = {"config": config, "config_sha256": config_hash(config),
              "dataset_sha256": sha256_file(config["dataset"]["json"]), "summary": summary, "questions": details}
    target = output_root / "results.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
