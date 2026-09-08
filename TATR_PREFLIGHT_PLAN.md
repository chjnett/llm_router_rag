# Table Transformer Preflight Plan

## Purpose

Test whether a learned PubTables-1M table detector provides enough detection signal to justify implementing the full detection + structure Cheap path.

## Frozen Setup

- Model: `microsoft/table-transformer-detection`
- Revision: `main`, safetensors preferred
- Cohort: the same first 20 document-disjoint pages, seed 42
- Input: existing PubTables validation page images
- Device: RTX 3090 CUDA, `model.eval()`, no gradients
- Detection threshold: 0.90

## Preflight Gate

- 20/20 completion
- table-count F1 proxy >= 0.70
- model inference p50 < 250 ms/page
- peak VRAM < 4 GB

This is only a detector preflight, not P1 sufficiency evidence. Passing permits implementation of the paired structure-recognition model and 20-page GriTS preflight. Failing stops the TATR branch.

## Detection Result

PASS: 20/20 completed, table-count proxy 1.000, model-only p50 17.36 ms, p95 33.67 ms, peak CUDA allocation 230,491,648 bytes. PDF rendering and processor time are excluded from this model-only latency and must be included in the later end-to-end parser measurement.
