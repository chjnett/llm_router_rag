from __future__ import annotations

import argparse
import json
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import iter_answerable_questions, load_split_from_archive, sha256_file


def allocate_whole_papers(rows: list[tuple[str, str]], minimum: int) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    selected: list[tuple[str, str]] = []
    selected_papers: set[str] = set()
    for paper_id, question_id in rows:
        if len(selected) < minimum or paper_id in selected_papers:
            selected.append((paper_id, question_id))
            selected_papers.add(paper_id)
        else:
            break
    return selected, rows[len(selected):]


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze document-disjoint QASPER recovery splits")
    parser.add_argument("--config", default="configs/r1_qasper_recovery_splits.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    development = json.loads(Path(config["dataset"]["development_audit"]).read_text(encoding="utf-8"))
    development_papers = {row["paper_id"] for row in development["questions"]}
    remaining = [
        (paper_id, qa["question_id"])
        for paper_id, _, qa in iter_answerable_questions(dataset)
        if paper_id not in development_papers
    ]
    calibration, remaining = allocate_whole_papers(remaining, int(config["splits"]["calibration_min_questions"]))
    certification, final = allocate_whole_papers(remaining, int(config["splits"]["certification_min_questions"]))
    split_rows = {"calibration": calibration, "certification": certification, "final": final}
    paper_sets = {name: {paper_id for paper_id, _ in rows} for name, rows in split_rows.items()}
    assert not (development_papers & set().union(*paper_sets.values()))
    assert not (paper_sets["calibration"] & paper_sets["certification"])
    assert not (paper_sets["calibration"] & paper_sets["final"])
    assert not (paper_sets["certification"] & paper_sets["final"])

    output_root = Path(config["outputs"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    summary = {"development": {"papers": len(development_papers), "questions": len(development["questions"])}}
    for name, rows in split_rows.items():
        payload = [{"paper_id": paper_id, "question_id": question_id} for paper_id, question_id in rows]
        (output_root / f"{name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        summary[name] = {"papers": len(paper_sets[name]), "questions": len(rows)}
    manifest = {
        "config": config, "config_sha256": config_hash(config),
        "archive_sha256": sha256_file(config["dataset"]["archive"]), "summary": summary,
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
