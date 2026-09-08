# RAG Pivot Implementation Plan

## Research Question

Can query-time selective page/table rescue preserve evidence retrieval utility relative to Always Strong while reducing Strong document-processing cost?

## Why QASPER First

The first Gate uses QASPER validation as a text-control benchmark. It provides 1,005 questions over 281 scientific NLP papers and human-selected supporting evidence. This allows retrieval correctness to be tested without first downloading the 33.6GB SPIQA distribution. QASPER is not treated as the final multimodal result.

After the text-control Gate passes, SPIQA test-A table/figure questions become the multimodal evaluation. MMVQA/PDF-MVQA remains an external multipage retrieval candidate because its current release is distributed through multiple Google Drive artifacts.

## R0 — Dataset and Evidence Audit

- Download QASPER metadata only.
- Freeze the first 100 answerable validation questions after deterministic sorting by paper id and question id.
- Keep papers document-disjoint from any later calibration/certification split.
- Classify evidence as paragraph, table/figure (`FLOAT SELECTED`), or mixed.
- Verify that evidence strings can be mapped to canonical chunks and, for a small PDF subset, back to pages.

### R0 Gate

- 100 questions loaded deterministically.
- At least 80 questions contain usable evidence.
- At least 90% of usable textual evidence maps to exactly one canonical paragraph or an explicitly recorded tie.
- Dataset/config hash and frozen question ids are saved.

## R1 — Retrieval Baselines

Run in this order:

1. Oracle evidence retrieval (evaluation ceiling)
2. BM25 over QASPER-provided paragraphs
3. Dense retrieval with one frozen local embedding model
4. Hybrid BM25+dense

Metrics: evidence Recall@1/5/10, MRR, nDCG@5. Do not run a generator yet.

## R2 — Document Representation Baselines

- Always Cheap: native PyMuPDF representation
- Always Strong: Docling representation
- TATR-assisted: native text plus learned table regions

Use the same chunking, embedder and retrieval parameters. Parser changes must not be compensated by changing the answer model.

## R3 — Query-time Rescue

Start with a rule baseline before a learned trigger. Retrieve from Cheap representation, then reprocess only uncertain top-k pages with Strong processing and retrieve again.

Frozen candidate signals:

- top-1/top-2 similarity margin
- retrieval score entropy
- table/figure cue in query
- evidence-type prediction
- Cheap output schema/coverage warning

## Primary Gate

Relative to Always Strong:

- evidence Recall@5 retention >= 95%
- nDCG@5 retention >= 95%
- Strong processed pages reduced >= 20%
- end-to-end query latency saving >= 10%

Selection thresholds are chosen only on calibration data. Certification/final results cannot change them.

## Stop Conditions

- If BM25/dense retrieval cannot recover human evidence, stop before parser routing and repair chunk/evidence alignment.
- If Always Cheap and Always Strong retrieval utility are indistinguishable, ingestion/rescue routing lacks a downstream target.
- If a perfect rescue oracle cannot save 15%, do not train a rescue trigger.

## Immediate Deliverables

- `configs/r0_qasper_audit.yaml`
- QASPER metadata cache and SHA-256
- frozen question-id manifest
- `src/caproute/datasets/qasper.py`
- R0 evidence audit report
- monitoring HTML update
