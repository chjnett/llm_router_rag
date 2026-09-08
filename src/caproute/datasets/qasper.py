from __future__ import annotations

import hashlib
import json
import re
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


FLOAT_MARKER = "FLOAT SELECTED"


def normalize_evidence(text: str) -> str:
    """Normalize presentation-only differences without changing content."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_split_from_archive(archive: str | Path, split: str) -> dict[str, Any]:
    member = {"train": "qasper-train-v0.3.json", "validation": "qasper-dev-v0.3.json"}.get(split)
    if member is None:
        raise ValueError(f"Unsupported split in train/dev archive: {split}")
    with tarfile.open(archive, "r:gz") as bundle:
        extracted = bundle.extractfile(member)
        if extracted is None:
            raise FileNotFoundError(f"{member} not found in {archive}")
        return json.load(extracted)


def canonical_paragraphs(paper: dict[str, Any]) -> list[str]:
    paragraphs = [paper.get("abstract", "")]
    paragraphs.extend(
        paragraph
        for section in paper.get("full_text", [])
        for paragraph in section.get("paragraphs", [])
    )
    return [text for text in paragraphs if normalize_evidence(text)]


@dataclass(frozen=True)
class EvidenceAudit:
    paper_id: str
    question_id: str
    question: str
    evidence_type: str
    textual_evidence_count: int
    mapped_textual_evidence_count: int
    unique_mapping_count: int
    tied_mapping_count: int
    unmapped_evidence: tuple[str, ...]

    @property
    def usable(self) -> bool:
        return self.textual_evidence_count > 0


def iter_answerable_questions(dataset: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], dict[str, Any]]]:
    for paper_id in sorted(dataset):
        paper = dataset[paper_id]
        for qa in sorted(paper.get("qas", []), key=lambda row: row["question_id"]):
            if any(not annotation["answer"].get("unanswerable", False) for annotation in qa.get("answers", [])):
                yield paper_id, paper, qa


def audit_question(paper_id: str, paper: dict[str, Any], qa: dict[str, Any]) -> EvidenceAudit:
    paragraph_index: dict[str, int] = {}
    for paragraph in canonical_paragraphs(paper):
        key = normalize_evidence(paragraph)
        paragraph_index[key] = paragraph_index.get(key, 0) + 1

    evidence: list[str] = []
    has_float = False
    for annotation in qa.get("answers", []):
        answer = annotation["answer"]
        if answer.get("unanswerable", False):
            continue
        for item in answer.get("evidence", []):
            if normalize_evidence(item) == normalize_evidence(FLOAT_MARKER):
                has_float = True
            elif normalize_evidence(item):
                evidence.append(item)

    # Multiple annotators often select the same paragraph; audit each canonical
    # evidence string once so annotator duplication cannot inflate the Gate.
    deduplicated = {normalize_evidence(item): item for item in evidence}
    counts = [paragraph_index.get(key, 0) for key in deduplicated]
    unique = sum(count == 1 for count in counts)
    tied = sum(count > 1 for count in counts)
    unmapped = tuple(deduplicated[key] for key, count in zip(deduplicated, counts) if count == 0)
    evidence_type = "mixed" if has_float and deduplicated else "figure_or_table" if has_float else "paragraph"
    return EvidenceAudit(
        paper_id=paper_id,
        question_id=qa["question_id"],
        question=qa["question"],
        evidence_type=evidence_type,
        textual_evidence_count=len(deduplicated),
        mapped_textual_evidence_count=unique + tied,
        unique_mapping_count=unique,
        tied_mapping_count=tied,
        unmapped_evidence=unmapped,
    )
