from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from caproute.datasets.qasper import canonical_paragraphs, load_split_from_archive
from caproute.evaluation.retrieval import tokenize


def bucket(value: int, boundaries: tuple[int, ...], labels: tuple[str, ...]) -> str:
    for boundary, label in zip(boundaries, labels):
        if value <= boundary:
            return label
    return labels[-1]


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"questions": 0, "hit_at_5": 0.0, "recall_at_5": 0.0}
    return {
        "questions": len(rows),
        "hit_at_5": sum(row["hit_at_5"] for row in rows) / len(rows),
        "recall_at_5": sum(row["recall_at_5"] for row in rows) / len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Stratify frozen QASPER retrieval failures")
    parser.add_argument("--dense", default="outputs/r1_qasper_dense/results.json")
    parser.add_argument("--bm25", default="outputs/r1_qasper_bm25/results.json")
    parser.add_argument("--archive", default="data/raw/qasper/qasper-train-dev-v0.3.tgz")
    parser.add_argument("--output", default="outputs/r1_qasper_analysis/analysis.json")
    args = parser.parse_args()
    dense = json.loads(Path(args.dense).read_text(encoding="utf-8"))
    bm25 = json.loads(Path(args.bm25).read_text(encoding="utf-8"))
    bm25_by_id = {row["question_id"]: row for row in bm25["questions"]}
    dataset = load_split_from_archive(args.archive, "validation")
    rows = []

    for result in dense["questions"]:
        paper = dataset[result["paper_id"]]
        paragraphs = canonical_paragraphs(paper)
        qa = next(item for item in paper["qas"] if item["question_id"] == result["question_id"])
        relevant = set(result["relevant_indices"])
        dense_top = set(result["dense_top_indices"][:5])
        lexical_top = set(bm25_by_id[result["question_id"]]["bm25_top_indices"][:5])
        earliest = min(relevant)
        evidence_lengths = [len(tokenize(paragraphs[index])) for index in relevant]
        question_lead = tokenize(qa["question"])[0] if tokenize(qa["question"]) else "empty"
        if question_lead not in {"what", "how", "which", "why", "does", "do", "is", "are", "was", "were"}:
            question_lead = "other"
        rows.append({
            "question_id": result["question_id"],
            "hit_at_5": bool(dense_top & relevant),
            "recall_at_5": len(dense_top & relevant) / len(relevant),
            "bm25_hit_at_5": bool(lexical_top & relevant),
            "question_lead": question_lead,
            "evidence_count": "single" if len(relevant) == 1 else "multiple",
            "shortest_evidence_tokens": bucket(min(evidence_lengths), (128, 256, 512), ("<=128", "129-256", "257-512", ">512")),
            "paper_paragraphs": bucket(len(paragraphs), (25, 50, 100), ("<=25", "26-50", "51-100", ">100")),
            "evidence_position": bucket(int(100 * earliest / max(1, len(paragraphs) - 1)), (24, 49, 74), ("Q1", "Q2", "Q3", "Q4")),
        })

    strata = {}
    for field in ("question_lead", "evidence_count", "shortest_evidence_tokens", "paper_paragraphs", "evidence_position"):
        groups = defaultdict(list)
        for row in rows:
            groups[row[field]].append(row)
        strata[field] = {key: summarize(value) for key, value in sorted(groups.items())}
    complementarity = {
        "both_hit": sum(row["hit_at_5"] and row["bm25_hit_at_5"] for row in rows),
        "dense_only": sum(row["hit_at_5"] and not row["bm25_hit_at_5"] for row in rows),
        "bm25_only": sum(not row["hit_at_5"] and row["bm25_hit_at_5"] for row in rows),
        "neither": sum(not row["hit_at_5"] and not row["bm25_hit_at_5"] for row in rows),
    }
    output = {"evaluated_questions": len(rows), "overall": summarize(rows), "complementarity_at_5": complementarity, "strata": strata, "questions": rows}
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in output.items() if key != "questions"}, indent=2))


if __name__ == "__main__":
    main()
