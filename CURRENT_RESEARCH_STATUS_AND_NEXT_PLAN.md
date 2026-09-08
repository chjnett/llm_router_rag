# CapRoute 연구 현황과 다음 실험 계획

## 한 줄 결론

현재는 대규모 Router/GPU 확대 단계가 아니다. QASPER cached page rescue는 비용 조건부 가능성을 보였고 SPIQA에서 caption과 visual retrieval의 oracle 보완성도 paper-disjoint 표본에서 재현됐다. 그러나 50문항에서 학습한 실제 선택기는 독립 100문항에서 R@1 `0.65→0.62`로 악화됐다. 따라서 **별도 300+ 학습/보정 cohort 확보 전에는 GPU sweep과 certification을 잠근다.**

## 무엇이 확인됐는가

| 단계 | 핵심 결과 | 판정 |
|---|---|---|
| P0 PyMuPDF vs Docling | p50 91.64 vs 667.22ms, GriTS-Top 0.190 vs 0.904, Loc 0.114 vs 0.528 | 비용·구조 차이 PASS |
| P1 parser Oracle | Cheap sufficient 11.43%, both-fail 38.37%, 최대 절감 9.86% | 15% Gate FAIL |
| TATR 300 | Top 0.866, Loc 0.494, p50 135.79ms | Loc 0.50 near-miss FAIL |
| QASPER R0 | 100/100 usable, evidence exact mapping 93.68% | text-control PASS |
| QASPER R1 BM25 | Recall@5 43.68%, nDCG@5 0.3238 | 기준선 완료, 낮음 |
| QASPER R1 dense | Recall@5 54.14%, nDCG@5 0.3846 | BM25 대비 개선, 절대치는 낮음 |
| QASPER R1 RRF | Recall@5 49.78% | dense보다 하락, 실패 보존 |
| QASPER R2-P | cached adjacent recall 97.06%, Strong time -18.26% | cache 조건부 PASS |
| SPIQA CLIP confirmation | caption R@1 0.65, oracle 0.81 | 보완성 PASS |
| SPIQA ColSmol confirmation | caption R@1 0.65, oracle 0.77 | 보완성 PASS |
| SPIQA learned selector | R@1 0.62, MRR 0.7285, route 36% | 독립 확인 FAIL |

## P1-V multimodal 결론

Visual retrieval을 항상 쓰는 방식은 실패했다. 100문항에서 CLIP R@1은 0.41, ColSmol은 0.34로 caption 0.65보다 낮다. Oracle 결합은 각각 0.81/0.77이므로 질문별 보완성은 존재한다. 그러나 추론 가능 신호로 학습한 ColSmol 선택기는 train R@1 0.90에서 confirmation R@1 0.62로 무너졌다. 현재 병목은 GPU 모델 크기가 아니라 **선택 정책의 데이터 효율과 일반화**다. 상세 수치는 `docs/P1V_SPIQA_PREFLIGHT_REPORT.md`에 있다.

다음 허용 작업은 test-A 재튜닝이 아니라 독립 training/calibration 자료 설계다. 최소 300질문을 확보하기 전에는 추가 시각 모델 sweep을 하지 않는다.

## 현재 결과를 어떻게 이해해야 하는가

1. 9.86%는 전체 scientific PDF의 결론이 아니다. PubTables의 표 중심 245-page evaluable cohort에서 PyMuPDF/Docling을 비교한 결과다.
2. Router 성능을 올려도 현재 parser pair의 15% Gate 실패는 뒤집을 수 없다. 완벽한 Oracle 자체가 실패했기 때문이다.
3. QASPER 첫 100문항은 표·그림 evidence가 0건이다. 현재 retrieval 수치는 text-control이며 multimodal 근거가 아니다.
4. downstream 검색이 약한 상태에서 parser representation을 비교하면 parser 효과와 retriever 실패가 섞인다.
5. ColPali는 parser가 아니라 visual retriever다. 표 구조 복원, 답 생성, provenance 검증을 대신하지 않는다.

## R1.1 실패 진단

Dense top-5가 관련 단락을 하나라도 포함한 비율은 59.79%다.

| 진단 | 결과 | 해석 |
|---|---:|---|
| BM25와 dense 모두 hit | 40/97 | 공통으로 쉬운 문항 |
| dense만 hit | 18/97 | semantic retrieval 이득 |
| BM25만 hit | 11/97 | lexical signal을 버리면 안 됨 |
| 둘 다 miss | 28/97 | 후보 생성 자체 수리 필요 |
| single-evidence hit@5 | 65.00% | 상대적으로 쉬움 |
| multiple-evidence hit@5 | 51.35% | multi-evidence aggregation 병목 |
| 100단락 초과 논문 hit@5 | 20.00% (n=5) | 긴 문서 병목, 소표본 주의 |

질문 첫 단어별 차이도 관측됐지만 표본이 작으므로 지금 일반화하지 않는다. 긴 문서와 복수 증거는 다음 실험의 명시적 분석 축으로 유지한다.

## 후보 아키텍처를 구분한다

### A. Ingestion-time parser routing — 현재 FAIL

PyMuPDF와 Docling/TATR 중 페이지별 경로를 선택한다. PubTables 결과에서는 Oracle Gate를 통과하지 못했으므로 P2 Router를 학습하지 않는다. 실제 전체 논문 분포에서 다시 측정할 가치는 있지만, 품질 정의는 모든 페이지에 GriTS를 억지로 적용하지 않고 downstream utility와 text/layout coverage를 포함해야 한다.

### B. Query-time selective rescue — 현재 주 후보

Cheap text index로 먼저 검색하고, 불확실하거나 visual cue가 있는 질문의 후보 페이지만 Strong parser/VLM으로 재처리한다. 모든 페이지에 Strong 처리를 선지불하지 않아 현재 비용 제약과 가장 잘 맞는다. 단, R1.1 retrieval Gate 통과 전에는 구현하지 않는다.

### C. Selective ColPali visual retrieval — 후속 후보

일반 텍스트는 text index, 표·그림·복잡 페이지는 visual multi-vector index로 처리한다. ColPali의 가치와 index 저장 비용을 Always Text/Always ColPali/Rule/Oracle 비교로 먼저 측정한다. 대용량 전체 다운로드나 Router 학습 전에 작은 multimodal preflight가 필요하다.

## 동결된 실행 순서

### 1. R1.1 retrieval repair preflight — 즉시

- BM25 top-10 + dense top-10 후보를 결합한다.
- lightweight cross-encoder 또는 동등한 고정 reranker로 top-5를 재순위화한다.
- 현재 100문항은 개발/진단 cohort로만 사용한다.
- 목표: Recall@5 >= 0.65, nDCG@5 >= 0.50.
- 실패하면 parser/ColPali로 넘어가지 않고 chunking, section context, query formulation을 수리한다.

실행 결과: MiniLM cross-encoder는 MRR을 0.4719로 높였지만 Recall@5 0.5190, nDCG@5 0.4296으로 Gate를 통과하지 못했다. Dense 단독 Recall@5보다도 낮으므로 채택하지 않는다. 다음은 R1.2 section-aware chunk/query formulation 진단이다.

R1.2 결과: passage에 title/section metadata를 붙이면 Recall@5 0.5562, Recall@10 0.7556, MRR 0.4913으로 개선됐지만 Gate는 실패했다. 제목을 query에도 붙인 variant는 Recall@5 0.3326으로 악화되어 폐기한다. 개발 cohort에서 허용할 마지막 저비용 수리는 adjacent-window 또는 section-aware candidate rescue 한 번이며, 이후에도 실패하면 QASPER formulation을 멈추고 별도 split/전체 논문 preflight 설계로 이동한다.

R1.3 결과: section dense와 BM25 후보에 인접 단락 ±1을 추가하자 candidate Recall은 0.9278, nDCG@5는 0.5103으로 올라갔지만 Recall@5는 0.6161로 Gate 0.65에 미달했다. 기준을 완화하지 않고 development 100문항 탐색을 종료했다.

다음 문서 단위 분할을 고정했다: development 34 papers/100 questions, calibration 62/200, certification 60/200, final 123/443. Development paper의 나머지 질문도 다른 split에 넣지 않았다. 다음 recovery 방법 선택은 calibration에서만 수행한다.

Calibration 결과: exact-mapped 187문항에서 section dense Recall@5 0.5979, adjacent+MiniLM-L6 0.6303/nDCG@5 0.5122였다. L12 reranker는 0.6212/0.4987로 더 나빠 폐기했다. Recall Gate 0.65를 완화하지 않으며 certification/final은 열지 않는다. 다음은 10개 complete PDF에서 paragraph miss와 실제 evidence-page miss가 같은지 확인하는 R1-P mapping preflight다.

R1-P 결과: 10/10 PDFs, 103 pages를 파싱했고 evidence 57/59(96.61%)를 page에 매핑했다. 34문항의 page Recall@5는 0.8971, adjacent ±1 rescue Recall은 0.9706이었다. 이는 실제 page-level rescue가 유망하다는 preflight 신호지만 평균 7.53 candidate pages의 Strong 처리 비용은 아직 측정하지 않았다. 다음은 같은 10편에서 Always Text와 query-time Strong rescue의 실제 비용·품질 R2-P다.

R2-P 결과: cached 34-query workload에서 adjacent 전략은 103페이지 중 80페이지만 Strong 처리해 page recall 0.9706, Strong 시간 18.26% 절감으로 조건부 PASS했다. 그러나 캐시 없는 반복 처리는 93.63초로 Always Strong 37.05초보다 152.68% 비싸다. Cheap/Strong evidence usable rate가 모두 100%여서 QASPER text-control에서는 Strong 품질 이득도 없다. QASPER GPU 확대를 중단하고 작은 table/figure multimodal preflight로 이동한다.

### 2. 전체 논문 분포 preflight — retrieval recovery 확인 후

- 처음부터 30~50편을 수작업 라벨링하지 않는다.
- 10편의 born-digital complete paper로 비용·페이지 유형·text coverage와 downstream retrieval 차이를 먼저 측정한다.
- preflight에서 경로 차이가 관측될 때만 document-disjoint 30~50편으로 확대한다.
- PubTables 9.86%와 실제 논문 분포 결과를 별도 표로 보고한다.

### 3. ColPali P1-V — multimodal subset 확보 후

- Always Text, Always ColPali, Rule Selective, Oracle Selective를 비교한다.
- 20~50 question/page 소표본에서 GPU, index bytes/page, Recall@5를 먼저 측정한다.
- preflight 없이 33.6GB SPIQA 전체를 다운로드하지 않는다.
- 통과 후보 기준: Always ColPali 대비 quality retention >=95%, indexing saving >=15%, index storage saving >=20%, peak VRAM <=22GB.

### 4. Router 학습 — Oracle Gate 통과 후에만

Logistic Regression → ExtraTrees → XGBoost 순서다. Calibration/Certification/Final/External 문서를 분리하고, 결과를 본 뒤 threshold를 완화하지 않는다.

## 당장 하지 않는 것

- 현재 97문항 결과를 최종 test 성능으로 주장
- PubTables 9.86%를 전체 논문 분포에 일반화
- ColPali 전체 index 생성
- Local VLM 전체 페이지 실행
- Oracle Gate 전 Router/threshold 학습
- 표·그림 0건인 QASPER 표본으로 multimodal 효과 주장

## 최종 연구 질문

> English born-digital scientific PDFs에서 query와 page capability에 따라 Cheap text representation과 Strong/visual processing을 선택하면, Always Strong/Visual 대비 retrieval·QA 품질을 유지하면서 실제 GPU 시간, latency 및 index storage를 줄일 수 있는가?

이 질문은 기존 핵심인 `Cheap Document Processing -> Strong Document Processing`을 유지하면서, 실패한 ingestion-only parser pair에 연구 전체를 묶지 않는다.
