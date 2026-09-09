# CapRoute 연구 현황과 다음 실험 계획

## 한 줄 결론

SciVQA validation 1,440질의에서 frozen selector의 R@1은 Always ColSmol `0.6479`에서 `0.6965`로 유의하게 상승했다(95% CI `[+0.0347,+0.0625]`). 그러나 selector가 ColSmol 점수 특징을 요구해 **실제 Strong 계산 절감은 0%**다. 현재 결과는 quality fusion PASS / compute-aware routing FAIL이며, 다음은 Cheap-only early router를 잠근 뒤 미개봉 SciVQA test에서 1회 인증하는 것이다.

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
| SPIQA initial selector | R@1 0.62, MRR 0.7285, Strong 선택 36% | 50→100 확인 FAIL |
| SPIQA expanded selector | R@1 0.716, MRR 0.8244, Strong 선택 12.35% | point PASS, 통계 INCONCLUSIVE |
| SciVQA external quality | R@1 0.6479→0.6965, CI excludes 0 | quality fusion PASS |
| SciVQA realized compute | Strong-derived 특징으로 사전 계산 필요 | saving 0%, routing FAIL |

## P1-V multimodal 결론

Visual retrieval을 항상 쓰는 방식은 실패했다. 100문항에서 CLIP R@1은 0.41, ColSmol은 0.34로 caption 0.65보다 낮다. Oracle 결합은 각각 0.81/0.77이므로 질문별 보완성은 존재한다. 그러나 추론 가능 신호로 학습한 ColSmol 선택기는 train R@1 0.90에서 confirmation R@1 0.62로 무너졌다. 현재 병목은 GPU 모델 크기가 아니라 **선택 정책의 데이터 효율과 일반화**다. 상세 수치는 `docs/P1V_SPIQA_PREFLIGHT_REPORT.md`에 있다.

확대 실험에서 별도 train/calibration 380문항을 확보하고 정책을 인증 전에 잠갔다. Certification의 R@1 차이는 +3.70%p였지만 bootstrap 95% CI `[-1.23,+9.88]%p`, McNemar p=`0.375`다. SciVQA에서 품질 일반화는 확인했지만 비용 인과성이 실패했으므로, 다음 허용 작업은 Strong 특징을 제거한 early router 수리다.

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

## 2026-09-09 입력 해상도 공학 스크리닝

새 모델을 내려받기 전에 기존 ColSmol-256M의 224×224 입력이 병목인지 동결된 초기 preflight 50문항에서 확인했다. 이 표본은 모델·해상도 공학용 개발 표본이며 certification 성능으로 재사용하지 않는다.

| ColSmol-256M 입력 | R@1 | R@5 | MRR | 표 R@1 | 그림 R@1 | Indexing | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| 224px 정사각 이미지 | 0.360 | 0.940 | 0.5727 | 0.520 | 0.200 | 35.16 s | 4.01 GiB |
| 원본 해상도 이미지 | **0.580** | 0.940 | **0.7209** | **0.800** | **0.360** | 23.92 s | 3.92 GiB |

해상도만 바꿔 R@1이 +22%p, MRR이 +0.1481 개선됐다. 특히 표 R@1은 +28%p다. 그림은 +16%p 개선됐지만 0.36으로 여전히 약하다. 원본 이미지 중앙값은 502×252, 최대는 1097×1411이며 기존 파일은 모두 224×224였다.

이는 더 큰 모델을 바로 쓰기 전에 입력 전처리 손실을 제거해야 한다는 강한 공학적 신호다.

동일 50문항·원본 해상도에서 ColSmol-500M도 한 번 비교했다. 전체 R@1은 0.58로 동일했고 MRR은 0.7209→0.7229(+0.002)에 그쳤다. 표 R@1은 0.80→0.76으로 하락하고 그림 R@1은 0.36→0.40으로 상승했다. 50문항 중 MRR 개선 7건, 악화 6건, 동일 37건이다. Peak VRAM은 3.92→4.38GiB, 로컬 모델 저장공간은 약 479→954MiB로 증가했다.

따라서 현재 pair에서는 **ColSmol-256M + 원본 해상도**를 동결하고 500M은 채택하지 않는다. 세부 수치·결과/가중치 hash는 `artifacts/p1v_spiqa_model_resolution_screen.json`에 보존한다. SPIQA test-A에서 추가 모델/threshold 탐색을 하지 않고 외부 table/figure scientific-document 데이터 검증으로 이동한다.

## 2026-09-09 SciVQA 외부 validation

MIT 라이선스 SciVQA validation에서 unanswerable 240개를 결과 전에 제외하고, SPIQA와 겹치지 않는 235논문·240그림·1,440 answerable 질문을 고정했다.

Caption R@1/R@5/MRR은 0.3653/0.4986/0.4336, ColSmol-256M 원본은 0.6479/0.7701/0.7070, Oracle은 0.7396/0.8451/0.7908이었다. frozen 13-feature selector는 0.6965/0.7938/0.7447로 Always ColSmol보다 R@1 +4.86%p였다. R@1 차이 95% CI는 [+3.47,+6.25]%p이고 McNemar p=`2.97e-12`다.

그러나 이것은 **quality fusion PASS / compute routing FAIL**이다. 현 selector는 ColSmol top score·margin·entropy를 입력으로 쓰므로 Caption을 선택할 때도 Strong 계산을 이미 수행한다. Strong 선택률 80.63%를 호출률로 해석할 수 없고 실제 Strong query compute 절감은 0%다.

다음 아키텍처는 (1) Cheap/query/Caption 신호만 쓰는 early router가 ColSmol 실행 여부를 먼저 결정하고, (2) Strong을 실행한 경우에만 현재 full selector를 optional late fusion으로 사용하는 2단 구조다. SciVQA validation은 구조 개발 자료로 전환하고, 아직 열지 않은 SciVQA test를 최종 1회 외부 인증에 사용한다. 상세 보고서는 `docs/R3_SCIVQA_EXTERNAL_REPORT.md`다.
