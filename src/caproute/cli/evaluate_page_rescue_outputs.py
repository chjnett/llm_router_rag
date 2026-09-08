from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

from caproute.cli.evaluate_qasper_page_mapping import token_coverage
from caproute.cli.run_page_rescue_cost import adjacent_pages
from caproute.core.config import load_config
from caproute.datasets.qasper import canonical_paragraphs, load_split_from_archive


def main() -> None:
    parser = argparse.ArgumentParser(description="Check evidence preservation in cached Cheap and Strong page outputs")
    parser.add_argument("--config", default="configs/r2_page_rescue_cost.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    mapping = json.loads(Path(config["dataset"]["page_mapping_results"]).read_text(encoding="utf-8"))
    qasper = load_split_from_archive(config["dataset"]["qasper_archive"], "validation")
    calibration = json.loads(Path(config["dataset"]["calibration_results"]).read_text(encoding="utf-8"))
    calibration_by_id = {row["question_id"]: row for row in calibration["questions"]}
    strong_by_page = {}
    for path in Path(config["cache"]["root"]).glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        page = document["pages"][0]
        strong_by_page[(document["document_id"], int(page["page_id"]))] = " ".join(
            block.get("text", "") for block in page.get("blocks", []) if block.get("text")
        )
    paper_mapping = {paper["paper_id"]: paper for paper in mapping["papers"] if paper.get("success")}
    threshold = float(config["quality_proxy"]["min_evidence_token_coverage"])
    cheap_page_text = {}
    rows = []
    for question in mapping["questions"]:
        paper_id = question["paper_id"]
        paper = qasper[paper_id]
        paragraphs = canonical_paragraphs(paper)
        mappings = paper_mapping[paper_id]["mappings"]
        # Use the frozen calibration relevance indices rather than reinterpreting answers.
        source = calibration_by_id[question["question_id"]]
        selected = adjacent_pages(question["retrieved_pages"], paper_mapping[paper_id]["pages"])
        evidence = []
        for index in source["relevant_indices"]:
            page = mappings[index]["page"]
            if page is None:
                continue
            key = (paper_id, page)
            if key not in cheap_page_text:
                with pymupdf.open(Path(config["dataset"]["pdf_root"]) / f"{paper_id}.pdf") as document:
                    cheap_page_text[key] = document[page].get_text("text")
            cheap = token_coverage(paragraphs[index], cheap_page_text[key])
            strong = token_coverage(paragraphs[index], strong_by_page.get(key, ""))
            evidence.append({"paragraph_index": index, "page": page, "selected": page in selected,
                             "cheap_coverage": cheap, "strong_coverage": strong,
                             "cheap_usable": cheap >= threshold, "strong_usable": strong >= threshold})
        if evidence:
            rows.append({"paper_id": paper_id, "question_id": question["question_id"], "evidence": evidence})

    evidence_rows = [evidence for row in rows for evidence in row["evidence"]]
    summary = {
        "questions": len(rows), "evidence_instances": len(evidence_rows), "coverage_threshold": threshold,
        "cheap_mean_coverage": sum(row["cheap_coverage"] for row in evidence_rows) / len(evidence_rows),
        "strong_mean_coverage": sum(row["strong_coverage"] for row in evidence_rows) / len(evidence_rows),
        "cheap_usable_rate": sum(row["cheap_usable"] for row in evidence_rows) / len(evidence_rows),
        "strong_usable_rate": sum(row["strong_usable"] for row in evidence_rows) / len(evidence_rows),
        "selective_strong_usable_rate": sum(row["selected"] and row["strong_usable"] for row in evidence_rows) / len(evidence_rows),
        "question_any_cheap_usable": sum(any(e["cheap_usable"] for e in row["evidence"]) for row in rows) / len(rows),
        "question_any_strong_usable": sum(any(e["strong_usable"] for e in row["evidence"]) for row in rows) / len(rows),
        "question_any_selective_strong_usable": sum(any(e["selected"] and e["strong_usable"] for e in row["evidence"]) for row in rows) / len(rows),
    }
    target = Path(config["outputs"]["root"]) / "output_quality.json"
    target.write_text(json.dumps({"summary": summary, "questions": rows}, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))


if __name__ == "__main__":
    main()
