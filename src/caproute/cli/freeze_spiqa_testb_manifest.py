from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the unopened SPIQA test-B retrieval manifest")
    parser.add_argument("--config", default="configs/r6_spiqa_testb_external.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    metadata_path = Path(config["dataset"]["json"])
    archive_path = Path(config["dataset"]["images_zip"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    prefix = config["dataset"]["image_archive_prefix"].rstrip("/")
    corpus = []
    queries = []
    index_by_reference = {}
    with zipfile.ZipFile(archive_path) as archive:
        archive_names = set(archive.namelist())
        for paper_id in sorted(metadata):
            paper = metadata[paper_id]
            for reference, caption in sorted(paper["all_figures_tables"].items()):
                member = f"{prefix}/{reference}"
                if member not in archive_names:
                    raise FileNotFoundError(member)
                index_by_reference[reference] = len(corpus)
                corpus.append({
                    "paper_id": paper_id,
                    "reference": reference,
                    "archive_path": member,
                    "caption": caption,
                })
        for paper_id in sorted(metadata):
            paper = metadata[paper_id]
            for index, question in enumerate(paper["question"]):
                references = paper["referred_figures_tables"][index]
                relevant = sorted({index_by_reference[reference] for reference in references})
                if not relevant:
                    raise ValueError(f"Question {paper_id}:{index} has no relevant image")
                queries.append({
                    "query_id": f"{paper_id}:{paper['question_id'][index]}",
                    "paper_id": paper_id,
                    "question": question,
                    "qa_pair_type": "test-b",
                    "relevant_indices": relevant,
                    "reference_images": references,
                })
    output = {
        "status": "frozen_before_retrieval",
        "config_sha256": config_hash(config),
        "metadata_sha256": sha256_file(metadata_path),
        "images_zip_sha256": sha256_file(archive_path),
        "contract": {
            "dataset": "google/spiqa test-B",
            "papers": len(metadata),
            "queries": len(queries),
            "images": len(corpus),
            "candidate_scope": "global test-B corpus",
            "relevance": "a hit on any referred figure/table is relevant",
        },
        "corpus": corpus,
        "queries": queries,
    }
    target = Path(config["dataset"]["manifest"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **output["contract"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
