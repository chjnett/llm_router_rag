# Phase Report

## Phase

P0 — implementation status; screening Gate not yet evaluated

## Date

2026-09-07

## Git Commit

Initial commit pending at report creation. 실제 실행 manifest가 commit과 dirty 상태를 자동 기록한다.

## Goal

English born-digital scientific paper PDF에서 Cheap/Strong document processing의 품질과 실제 비용을 동일한 Canonical IR 및 benchmark contract로 비교할 수 있는 P0 harness를 준비한다.

## Completed

- [x] 기존 `llm_router` reference-only 분석 및 migration 분류
- [x] 신규 repository scaffold/config/reproducibility metadata
- [x] PubTables-1M 공식 PASCAL VOC split loader
- [x] PyMuPDF Cheap parser와 optional Docling Strong parser
- [x] Canonical IR, atomic cache, failure-preserving result serialization
- [x] parsing proxy evaluator와 latency/VRAM/power harness
- [x] offline unit/integration tests
- [ ] 실제 300~500 page screening
- [ ] official GriTS 연결

## Changed Files

- `MIGRATION_PLAN.md`
- `P0_IMPLEMENTATION_PLAN.md`
- `configs/p0_screening.yaml`
- `src/caproute/**`
- `tests/test_p0.py`

## Dataset

- name: PubTables-1M
- split: validation 예정
- n: 300 예정
- document-level split: one sampled page per document
- preprocessing: official PASCAL VOC page detection annotations
- current availability: missing

## Models / Parsers

### Cheap

- name: PyMuPDF native text + optional table finder
- version: runtime metadata에 기록

### Strong

- name: Docling
- version: runtime metadata에 기록
- current availability: 별도 strong extra 설치 필요

## Metrics

실제 데이터 실행 전이므로 수치를 보고하지 않는다.

| Metric | Cheap | Strong |
|---|---:|---:|
| Quality | N/A | N/A |
| p50 latency | N/A | N/A |
| p95 latency | N/A | N/A |
| GPU sec/page | N/A | N/A |
| Peak VRAM | N/A | N/A |

## Gate

**NOT EVALUATED**

### Gate Criteria

- 300~500개의 document-disjoint page에서 두 parser가 완주할 것
- 공식 또는 명시된 proxy quality와 p50/p95/VRAM/GPU time이 캐시와 분리되어 기록될 것
- Cheap/Strong 차이를 신뢰할 수 있는 데이터가 확보될 것

## Failure Analysis

- 현재 데이터 경로에 PubTables-1M annotation/page images/source PubMed PDFs가 없다.
- 공식 PubTables-1M은 page/table image와 PASCAL VOC XML, PDF 좌표 annotation을 제공하지만 원본 PubMed PDF는 별도로 연결해야 한다.
- 기본 Anaconda의 torch import가 native abort를 일으켜 CPU-only P0 core에서 torch 강제 import를 제거했다. Docling용 격리 환경에서 CUDA를 다시 검증해야 한다.
- 현 evaluator의 table count F1은 smoke-test proxy이며 GriTS가 아니다.

## Decision

- P0 코드 구조는 유지한다.
- P1/router로 진행하지 않는다.
- 다음 작업은 데이터·환경 준비 후 300-page screening이다.

## Next Phase Recommendation

1. 충분한 디스크를 확인한다.
2. PubTables validation annotation/image subset과 해당 PubMed OA 원본 PDF를 준비한다.
3. Docling 전용 환경에서 CUDA smoke test를 한다.
4. 20-page preflight 후 300-page P0 screening을 실행한다.
5. Gate 결과가 PASS일 때만 P1 Oracle/Capability로 이동한다.

