from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf

from caproute.core.config import load_config
from caproute.benchmark.harness import percentile
from caproute.datasets.qasper import canonical_paragraphs, load_split_from_archive
from caproute.evaluation.retrieval import mean_metrics


def normalize_pdf_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def token_coverage(reference: str, candidate: str) -> float:
    reference_counts = Counter(re.findall(r"[^\W_]+", normalize_pdf_text(reference)))
    candidate_counts = Counter(re.findall(r"[^\W_]+", normalize_pdf_text(candidate)))
    total = sum(reference_counts.values())
    return sum(min(count, candidate_counts[token]) for token, count in reference_counts.items()) / total if total else 0.0


def map_paragraph(paragraph: str, pages: list[str], min_coverage: float, min_margin: float) -> dict:
    normalized = normalize_pdf_text(paragraph)
    exact = [index for index, page in enumerate(pages) if normalized and normalized in page]
    if len(exact) == 1:
        return {"status": "exact", "page": exact[0], "coverage": 1.0, "margin": 1.0}
    if len(exact) > 1:
        return {"status": "ambiguous", "page": None, "coverage": 1.0, "margin": 0.0, "candidate_pages": exact}
    scores = [token_coverage(paragraph, page) for page in pages]
    order = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
    best = scores[order[0]] if order else 0.0
    second = scores[order[1]] if len(order) > 1 else 0.0
    margin = best - second
    if best >= min_coverage and margin >= min_margin:
        return {"status": "approximate", "page": order[0], "coverage": best, "margin": margin}
    return {"status": "ambiguous" if best >= min_coverage else "unmapped", "page": None,
            "coverage": best, "margin": margin, "candidate_pages": order[:2]}


def ranked_unique_pages(paragraph_ranking: list[int], mappings: list[dict], limit: int) -> list[int]:
    result = []
    for index in paragraph_ranking:
        page = mappings[index]["page"]
        if page is not None and page not in result:
            result.append(page)
        if len(result) == limit:
            break
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Map QASPER canonical paragraphs and retrieval results to PDF pages")
    parser.add_argument("--config", default="configs/r1_page_mapping.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    output_root = Path(config["outputs"]["root"])
    manifest = json.loads((output_root / "sample_manifest.json").read_text(encoding="utf-8"))
    downloads = json.loads((output_root / "download_report.json").read_text(encoding="utf-8"))
    download_by_id = {row["paper_id"]: row for row in downloads["papers"]}
    calibration = json.loads(Path(config["dataset"]["calibration_results"]).read_text(encoding="utf-8"))
    result_by_id = {row["question_id"]: row for row in calibration["questions"]}
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    mapping_config = config["mapping"]
    paper_results, question_results = [], []
    native_scan_ms_per_page = []
    started = time.perf_counter()

    for item in manifest["papers"]:
        paper_id = item["paper_id"]
        download = download_by_id[paper_id]
        if not download["success"]:
            paper_results.append({"paper_id": paper_id, "success": False, "reason": "download_or_parse_failure"})
            continue
        scan_started = time.perf_counter()
        with pymupdf.open(download["path"]) as document:
            page_texts = [normalize_pdf_text(page.get_text("text")) for page in document]
        scan_ms = (time.perf_counter() - scan_started) * 1000
        native_scan_ms_per_page.extend([scan_ms / len(page_texts)] * len(page_texts))
        paragraphs = canonical_paragraphs(dataset[paper_id])
        mappings = [map_paragraph(paragraph, page_texts, float(mapping_config["approximate_token_coverage"]),
                                  float(mapping_config["best_second_margin"])) for paragraph in paragraphs]
        counts = Counter(mapping["status"] for mapping in mappings)
        paper_results.append({"paper_id": paper_id, "success": True, "pages": len(page_texts),
                              "paragraphs": len(paragraphs), "mapping_counts": dict(counts), "mappings": mappings})
        for question_id in item["question_ids"]:
            source = result_by_id[question_id]
            relevant_paragraphs = set(source["relevant_indices"])
            evidence_pages = {mappings[index]["page"] for index in relevant_paragraphs if mappings[index]["page"] is not None}
            if not evidence_pages:
                continue
            rescue_ranking = [index for _, index in sorted(zip(source["candidate_scores"], source["candidate_indices"]),
                                                           key=lambda row: (-row[0], row[1]))]
            retrieved_pages = ranked_unique_pages(rescue_ranking, mappings, 5)
            adjacent_pages = set(retrieved_pages)
            for page in retrieved_pages:
                adjacent_pages.update(index for index in (page - 1, page + 1) if 0 <= index < len(page_texts))
            question_results.append({
                "paper_id": paper_id, "question_id": question_id,
                "evidence_pages": sorted(evidence_pages), "retrieved_pages": retrieved_pages,
                "page_recall_at_5": len(set(retrieved_pages) & evidence_pages) / len(evidence_pages),
                "page_hit_at_5": bool(set(retrieved_pages) & evidence_pages),
                "adjacent_rescue_recall": len(adjacent_pages & evidence_pages) / len(evidence_pages),
                "adjacent_rescue_hit": bool(adjacent_pages & evidence_pages),
                "adjacent_page_count": len(adjacent_pages),
            })

    all_mappings = [mapping for paper in paper_results if paper.get("success") for mapping in paper["mappings"]]
    relevant_items = 0
    mapped_relevant_items = 0
    for item in manifest["papers"]:
        paper = next((row for row in paper_results if row["paper_id"] == item["paper_id"] and row.get("success")), None)
        if paper is None:
            continue
        relevant = set().union(*(set(result_by_id[qid]["relevant_indices"]) for qid in item["question_ids"]))
        relevant_items += len(relevant)
        mapped_relevant_items += sum(paper["mappings"][index]["page"] is not None for index in relevant)
    page_metrics = mean_metrics([{key: float(row[key]) for key in ("page_recall_at_5", "page_hit_at_5", "adjacent_rescue_recall", "adjacent_rescue_hit")}
                                 for row in question_results])
    summary = {
        "attempted_papers": len(manifest["papers"]),
        "parsed_papers": sum(row.get("success", False) for row in paper_results),
        "total_pages": sum(row.get("pages", 0) for row in paper_results),
        "canonical_paragraphs": len(all_mappings),
        "paragraph_mapping_counts": dict(Counter(row["status"] for row in all_mappings)),
        "evidence_paragraphs": relevant_items, "mapped_evidence_paragraphs": mapped_relevant_items,
        "evidence_page_mapping_rate": mapped_relevant_items / relevant_items if relevant_items else 0.0,
        "mapped_questions": len(question_results), "page_metrics": page_metrics,
        "mean_adjacent_page_count": sum(row["adjacent_page_count"] for row in question_results) / len(question_results),
        "native_scan_ms_per_page_p50": percentile(native_scan_ms_per_page, 0.50),
        "native_scan_ms_per_page_p95": percentile(native_scan_ms_per_page, 0.95),
        "wall_seconds": time.perf_counter() - started,
    }
    gate = config["gate"]
    summary["gate_passed"] = (
        summary["parsed_papers"] >= int(gate["min_pdf_parse_success"])
        and summary["evidence_page_mapping_rate"] >= float(gate["min_evidence_page_mapping_rate"])
        and summary["mapped_questions"] >= int(gate["min_mapped_questions"])
        and page_metrics.get("page_recall_at_5", 0.0) >= float(gate["min_page_recall_at_5"])
    )
    output = {"summary": summary, "papers": paper_results, "questions": question_results}
    (output_root / "page_mapping_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
