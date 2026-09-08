from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.core.repro import environment_metadata, git_metadata
from caproute.datasets.qasper import audit_question, iter_answerable_questions, load_split_from_archive, sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit QASPER evidence alignment for the RAG pivot Gate")
    parser.add_argument("--config", default="configs/r0_qasper_audit.yaml")
    parser.add_argument("--archive", default="data/raw/qasper/qasper-train-dev-v0.3.tgz")
    args = parser.parse_args()

    root = Path.cwd()
    config = load_config(args.config)
    dataset = load_split_from_archive(args.archive, config["dataset"]["split"])
    limit = int(config["dataset"]["sample_questions"])
    selected = list(iter_answerable_questions(dataset))[:limit]
    audits = [audit_question(*row) for row in selected]

    textual_total = sum(row.textual_evidence_count for row in audits)
    mapped_total = sum(row.mapped_textual_evidence_count for row in audits)
    usable = sum(row.usable for row in audits)
    mapping_rate = mapped_total / textual_total if textual_total else 0.0
    gate = config["gate"]
    passed = (
        len(audits) == limit
        and usable >= int(gate["min_usable_evidence_questions"])
        and mapping_rate >= float(gate["min_text_evidence_mapping_rate"])
    )

    output = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "config_sha256": config_hash(config),
        "archive_sha256": sha256_file(args.archive),
        "git": git_metadata(root),
        "environment": environment_metadata(),
        "summary": {
            "selected_questions": len(audits),
            "usable_evidence_questions": usable,
            "textual_evidence_items": textual_total,
            "mapped_textual_evidence_items": mapped_total,
            "text_evidence_mapping_rate": mapping_rate,
            "unique_mappings": sum(row.unique_mapping_count for row in audits),
            "tied_mappings": sum(row.tied_mapping_count for row in audits),
            "unmapped_items": textual_total - mapped_total,
            "evidence_type_counts": {
                kind: sum(row.evidence_type == kind for row in audits)
                for kind in ("paragraph", "figure_or_table", "mixed")
            },
            "gate_passed": passed,
        },
        "questions": [asdict(row) for row in audits],
    }
    output_root = Path(config["outputs"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / "audit.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = output_root / "frozen_question_ids.txt"
    manifest.write_text("\n".join(row.question_id for row in audits) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), **output["summary"]}, indent=2))
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
