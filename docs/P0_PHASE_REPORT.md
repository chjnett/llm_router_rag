# Phase Report

## Phase

P0 — 300-page Cheap/Strong screening

## Date

2026-09-07

## Git Commit

`fed429a`, `5331b37` 기반 실행. 본 보고서와 후속 harness 보완 commit은 최종 커밋 후 갱신한다.

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
- [x] 실제 300-page screening
- [x] 동일 document/page key 기반 결과 정렬 및 비교
- [ ] official GriTS 연결

## Changed Files

- `MIGRATION_PLAN.md`
- `P0_IMPLEMENTATION_PLAN.md`
- `configs/p0_screening.yaml`
- `src/caproute/**`
- `tests/test_p0.py`

## Dataset

- name: PubTables-1M validation annotation + PMC OA source PDF
- split: deterministic screening subset (`seed=42`)
- n: 300 pages / 300 documents
- document-level split: one sampled page per document
- preprocessing: official PASCAL VOC page detection annotations
- exclusion: `PMC6067716` (page 7, reproducible Docling native exit); deterministic replacement included

## Models / Parsers

### Cheap

- name: PyMuPDF native text + optional table finder
- version: 1.28.2

### Strong

- name: Docling
- version: 2.126.0
- device: CUDA, OCR off, table structure on, 4 threads

## Metrics

| Metric | Cheap | Strong |
|---|---:|---:|
| Table-count F1 proxy | 0.280 | 0.976 |
| p50 latency | 91.64 ms | 667.22 ms |
| p95 latency | 212.10 ms | 1,921.27 ms |
| p50 Strong/Cheap | 1.00x | 7.28x |
| p95 Strong/Cheap | 1.00x | 9.06x |
| Row/column shape similarity | 0.225 | 0.964 |
| GriTS-Top | 0.190 | 0.904 |
| GriTS-Loc (reconstructed) | 0.114 | 0.528 |
| Peak CUDA allocation | 0 | 약 603~628 MB/batch |

Strong은 Cheap보다 두 진단 품질이 높지만 p50 7.28배, p95 9.06배 느렸다. 이는 선택적 문서 처리의 비용-품질 이질성이 존재한다는 screening 신호다. 그러나 table-count proxy는 셀 구조, spanning cell, 읽기 순서 및 텍스트 정확도를 평가하지 않으므로 capability label이나 논문 성능 수치로 사용하지 않는다.

동일 key 300개가 정렬되었고 그중 proxy가 양쪽 모두 정의된 299개에서 Strong 우세 214개, 동률 85개, Cheap 우세 0개였다. 이 비교 역시 count proxy 진단 결과일 뿐 capability 정답표가 아니다.

추가로 공식 validation structure XML을 문서 내 table 순서로 연결했다. 완전 대응된 245페이지에서 행·열 개수 기반 shape similarity는 Cheap 0.225, Strong 0.964였다. 나머지 55페이지는 대응 structure XML이 없어 제외했다. 이 지표는 cell span, cell location, content를 평가하지 않는 자체 진단이며 GriTS가 아니다.

동일 245페이지의 291개 정답 표에 Microsoft 공식 factored 2D-MSS 방식의 GriTS를 적용했다. 병합 셀 합성 예제에서 공식 코드와 Top/Loc `0.75`로 일치했다. GriTS-Top은 Cheap 0.190, Strong 0.904로 구조 우세가 명확했다. GriTS-Loc은 Cheap 0.114, Strong 0.204였으나 Docling bbox가 cell region보다 tight text 영역을 나타내는 경우가 있어 parser 간 bbox 의미가 통일되기 전에는 provisional 수치로만 취급한다.

Docling table provenance의 전체 영역과 single-span cell text 중심선을 이용해 행·열 경계를 재구성한 결과 Strong GriTS-Loc은 0.204에서 0.528로 상승했고 Top은 0.904로 유지됐다. 이는 초기 Loc 저하의 상당 부분이 bbox 의미 차이였음을 보여준다. 다만 재구성 경계는 heuristic이므로 대표/최악 사례 시각 점검 전까지 확정 수치로 사용하지 않는다.

## Gate

**PASS — topology/location screening 범위**

### Gate Criteria

- 300개의 document-disjoint page 완주: **충족 (300/300 정렬)**
- uncached p50/p95 및 CUDA 메모리 기록: **충족**
- GriTS-Top 공식 정렬 + 공식 코드 교차검증: **충족**
- 재구성 GriTS-Loc + worst/median/best 시각 audit: **충족**
- GriTS-Con: **후속 항목 (P0 구조 screening의 blocker는 아님)**

## Failure Analysis

- Docling monolithic 실행이 native 종료되어 25~50페이지 배치로 복구했다. 일반 Python 예외 로그는 생성되지 않았다.
- `PMC6067716` page 7은 단독으로도 native exit code 1이 재현되어 설정에 exclusion을 기록하고 deterministic replacement를 사용했다.
- 마지막 offset 275 배치는 warmup native instability를 피하려고 warmup 0, 나머지는 warmup 2로 실행되어 config hash가 다르다.
- Docling은 일부 표에서 orphan cell recovery/drop 경고를 냈다. 공식 구조 metric 전에는 이 경고가 실제 품질에 미치는 영향을 판단할 수 없다.
- 전력 수치는 시스템 전체 GPU 샘플 기반 gross 값이라 parser별 순수 에너지로 해석하지 않는다.
- 현 table-count F1은 smoke-test proxy이며 공식 GriTS가 아니다.
- row/column shape 진단은 245/300페이지만 평가 가능했고 GriTS의 topology/location/content 정렬을 대체하지 못한다.
- GriTS-Loc의 Docling cell-region은 text 중심선 기반 재구성값이다.
- 시각 audit에서 worst/median/best가 실제 구조 실패/부분 일치/높은 일치와 대응했다.

## Decision

- Cheap/Strong 비용 분리는 충분히 크므로 모델쌍과 P0 코드 구조를 유지한다.
- P0 topology/location 구조 screening Gate를 PASS한다.
- 다음 작업은 P1 capability label과 Oracle saving 계산이다. Router 학습(P2)은 P1 Gate 전까지 시작하지 않는다.

## Next Phase Recommendation

1. GriTS-Top/Loc 기반 Cheap sufficient 기준을 사전 정의한다.
2. Cheap sufficient coverage, Strong-needed, both-fail을 계산한다.
3. 측정 비용비로 Oracle normalized cost와 saving을 계산한다.
4. P1 Stop Rule(Oracle saving ≥15%, Ccheap/Cstrong <0.50)을 판정한다.
5. GriTS-Con은 content-sensitive 최종 평가 전에 별도로 연결한다.
