# Decision Log

연구 설계 변경을 시간순으로 기록한다.

---

## Decision 001

### Date
TBD

### Decision
Scientific born-digital PDF를 첫 논문 domain으로 고정.

### Reason
공개 dataset, 자동 평가, table/layout/RAG 연결성, 재현성.

### Alternatives Rejected
- general PDF
- finance-only
- scanned documents

---

## Decision 002

### Date
TBD

### Decision
Small/Big model routing이 아니라 Cheap/Strong Document Processing routing으로 재정의.

### Reason
모델 크기와 실제 latency가 일치하지 않을 수 있으며, 연구의 핵심은 cost-quality selective processing이기 때문.

---

## Decision 003

### Date
TBD

### Decision
Query-time VLM rescue는 Main이 아니라 Extension.

### Reason
Main novelty를 ingestion-time capability routing에 집중하기 위함.

---

## New Decision Template

### Date

### Trigger

### Decision

### Evidence

### Alternatives

### Consequence

---

## Decision 004

### Date
2026-09-07

### Trigger
기존 PMC OA API가 2026년 8월 종료되어 PubTables 문서 원본 PDF 자동 수집이 실패했다.

### Decision
NIH/NLM이 안내하는 `pmc-oa-opendata` AWS 공개 버킷에서 개별 PDF를 내려받고, PDF magic bytes와 manifest를 기록한다.

### Evidence
공식 PMC AWS 문서와 버킷 README를 확인했으며 340개 PDF를 정상 검증했다.

### Alternatives
전체 PubTables/Hugging Face 이미지 배포본(약 117GB) 다운로드, 종료된 OA API 재시도.

### Consequence
필요한 원본만 내려받아 디스크 사용을 약 553MB로 제한한다. 원본 PDF 버전 차이로 존재하지 않는 page index는 명시적으로 건너뛴다.

---

## Decision 005

### Date
2026-09-07

### Trigger
Docling 300-page 단일 프로세스가 Python 예외 없이 native 종료되었다.

### Decision
Strong parser를 25~50페이지 독립 배치로 실행하고 raw prediction cache를 보존한 뒤, document/page key로 집계한다.

### Evidence
배치 실행으로 최종 300/300개 결과를 회수했다. `PMC6067716` page 7은 단독 실행에서도 exit code 1을 재현했다.

### Alternatives
실패를 무시한 채 불완전 결과 보고, 동일한 monolithic 실행 반복.

### Consequence
`PMC6067716`을 설정의 고정 제외 목록에 기록하고 동일 seed에서 다음 유효 문서로 교체했다. 마지막 25-page 배치는 native warmup 불안정성 때문에 warmup 0으로 수행되어 config hash가 다르며, 이를 보고서에 공개한다.

---

## Decision 006

### Date
2026-09-07

### Trigger
Table-count proxy만으로는 P0 구조 품질을 판정할 수 없다.

### Decision
전체 117GB 배포본 대신 공식 PubTables-1M validation structure annotation archive만 추가하고, 행·열 shape diagnostic을 먼저 수행한다.

### Evidence
- source: `https://huggingface.co/datasets/bsmock/pubtables-1m/resolve/main/PubTables-1M-Structure_Annotations_Val.tar.gz`
- bytes: `30,264,304`
- SHA-256: `6B8C4B512E24E1040FA0829935AB9C2D13FC0015F7315CC8F13EF82A8BC95CA4`
- extracted XML: 94,959 files, 약 0.72GB

### Alternatives
2.73GB validation image archive와 4.17GB word archive를 즉시 모두 다운로드.

### Consequence
디스크를 보존하면서 245개 대응 페이지의 row/column shape를 검증한다. 이 진단은 cell span/location/content를 포함하지 않아 GriTS로 보고하지 않으며 P0 Gate는 HOLD로 유지한다.

---

## Decision 007

### Date
2026-09-07

### Trigger
행·열 shape diagnostic 이후 공식 GriTS topology/location 평가가 필요했다.

### Decision
Microsoft Table Transformer의 factored 2D-MSS와 relative-span 정의를 동일하게 구현하고, 병합 셀이 있는 합성 표에서 공식 `src/grits.py`와 수치 일치를 확인한다.

### Evidence
- synthetic merged-cell case: GriTS-Top `0.75`, GriTS-Loc `0.75`로 공식 코드와 일치
- 245 mapped pages / 291 ground-truth tables
- GriTS-Top: PyMuPDF `0.190`, Docling `0.904`
- 초기 GriTS-Loc: PyMuPDF `0.114`, Docling `0.204`

### Alternatives
Table-count proxy만으로 P0 PASS, 전체 Table Transformer inference pipeline 재실행.

### Consequence
Topology 차이는 강한 P0 신호로 인정한다. Docling의 tight text bbox와 PubTables cell-region bbox가 의미상 다르므로 Loc 수치는 provisional로 표시하고 Gate를 HOLD한다.

---

## Decision 008

### Date
2026-09-08

### Trigger
Docling raw cell bbox가 tight text 영역이라 GriTS-Loc이 구조 위치보다 텍스트 여백에 과도하게 민감했다.

### Decision
Docling table provenance의 전체 bbox와 single-span cell text 중심선을 사용해 행·열 경계를 추정하고, 병합 셀을 해당 경계까지 확장하여 cell-region bbox를 만든다.

### Evidence
- 자동화 synthetic 2×2 cell-region test 통과
- Strong GriTS-Top 유지: `0.904`
- Strong GriTS-Loc: `0.204 → 0.528`
- Cheap GriTS-Loc: `0.114` (변경 없음)

### Alternatives
tight text bbox를 그대로 사용, 모든 표를 동일 크기 균등 격자로 강제 분할.

### Consequence
Loc 비교의 좌표 의미가 가까워졌으나 경계는 parser 원출력이 아닌 재구성값이다. 대표/최악 사례 시각 점검 전에는 P0 Gate를 HOLD한다.

---

## Decision 009

### Date
2026-09-08

### Trigger
재구성 GriTS-Loc의 대표/중앙/최악 사례가 실제 셀 구조 차이를 반영하는지 확인해야 했다.

### Decision
최악·중앙·최고 Loc 표를 고정 audit figure로 비교하고 P0 topology/location screening Gate를 PASS한다.

### Evidence
- worst: `PMC3068077` page 5 table 1, Loc `0.011` — 다수 행·열을 1×3 수준으로 축약한 실패
- median: `PMC5693913` page 8 table 0, Loc `0.559` — 부분 구조 및 경계 차이
- best: `PMC6068241` page 4 table 0, Loc `0.845` — 행·열 경계가 대부분 일치
- audit figure: `docs/figures/grits_loc_visual_audit.png`

### Alternatives
GriTS-Con 데이터까지 모두 확보할 때까지 P0 자체를 무기한 HOLD.

### Consequence
P0의 구조 품질·비용 screening은 완료한다. P1 capability/oracle을 시작할 수 있지만 content-sensitive 최종 평가는 GriTS-Con 전까지 완료로 보지 않는다.

---

## Decision 010

### Date
2026-09-08

### Trigger
사전 고정한 P1 sufficiency 기준과 비용 계약으로 capability label 및 zero-overhead Oracle을 계산했다.

### Decision
P1 Gate를 FAIL로 판정하고 P2 router 학습을 잠근다. 관측 결과에 맞춰 15% 절감 목표나 품질 임계값을 변경하지 않으며, 현재 PyMuPDF/Docling 조합을 개선하거나 교체한 뒤 동일 기준으로 P1을 재실행한다.

### Evidence
- evaluable: 245/300 pages; 55 pages는 structure XML 부재로 별도 보고
- Cheap sufficient: 28/245 (11.43%)
- Strong sufficient: 143/245 (58.37%)
- Strong needed: 123/245 (50.20%)
- both fail: 94/245 (38.37%)
- Cheap/Strong p50 ratio: 0.1374 (PASS)
- zero-overhead Oracle saving: 9.86% (15% 목표 FAIL)
- frozen protocol commit: `d67f35e`

### Alternatives
결과를 본 뒤 sufficiency 임계값 또는 절감 목표를 완화하거나, 곧바로 P2 분류기를 학습한다.

### Consequence
Capability-aware routing 가설 전체를 기각하지는 않는다. 다만 현재 parser pair의 Cheap coverage가 낮고 both-fail이 높으므로, 다음 실험은 router가 아니라 parser pair repair/screening이다.

---

## Decision 011

### Date
2026-09-08

### Trigger
추가 다운로드 없이 PyMuPDF의 union/refine, text, raw-lines 전략을 동일한 P1 기준으로 300페이지 실행했다.

### Decision
PyMuPDF 설정 탐색을 중단하고 별도의 lightweight table parser 후보 screening으로 전환한다. P2는 계속 잠근다.

### Evidence
- union+refine: Cheap sufficient 10.61%, Oracle saving 9.17%
- text/text: table-count proxy 0.931이나 Cheap sufficient 0%, Oracle saving 0%
- raw-lines: Cheap sufficient 11.43%, Oracle saving 9.81%
- 모든 후보의 사전 목표: Oracle saving >=15%

### Consequence
표 개수를 맞히는 것과 셀 구조를 충분히 복원하는 것은 다르다는 음성 결과를 보존한다. 다음 Cheap 후보는 PyMuPDF parameter variant가 아니라 독립 구현이어야 한다.

---

## Decision 012

### Date
2026-09-08

### Trigger
독립 CPU parser인 pdfplumber 0.11.10 line strategy를 사전 고정한 20페이지에서 preflight했다.

### Decision
300페이지로 확대하지 않고 pdfplumber 후보를 중단한다.

### Evidence
- completed 20/20, failures 0
- p50 95.97 ms, p95 158.73 ms
- table-count F1 proxy 0.183
- malformed color operator warning 4회, 결과 누락 없음

### Consequence
비용 조건은 만족하지만 구조 개선 신호가 없다. 다음 후보는 단순 PDF 선 휴리스틱이 아닌 lightweight learned table-structure model을 우선 검토한다.

---

## Decision 013

### Date
2026-09-08

### Trigger
Microsoft Table Transformer detection 모델을 고정 threshold 0.90으로 RTX 3090에서 20페이지 preflight했다.

### Decision
TATR detection branch를 PASS하고 structure-recognition 20-page GriTS preflight 구현을 허용한다.

### Evidence
- completed 20/20
- table-count F1 proxy 1.000
- model-only p50 17.36 ms, p95 33.67 ms
- peak CUDA allocation 230,491,648 bytes

### Consequence
검출 결과만으로 P1 품질을 주장하지 않는다. 다음 단계에서 detection crop과 structure model을 연결하고 렌더링·전처리를 포함한 end-to-end 비용 및 GriTS-Top/Loc을 측정한다.

---

## Decision 014

### Date
2026-09-08

### Trigger
TATR detection과 structure-recognition을 연결해 고정된 20페이지에서 실제 GriTS 및 end-to-end latency를 측정했다.

### Decision
현재 단순 row×column 교차 후처리는 FAIL로 판정하고 300페이지 확대를 보류한다. TATR branch는 즉시 폐기하지 않고 spanning/header semantics 후처리와 시각 audit을 한 번 수행한다.

### Evidence
- exact table count: 80%
- mean GriTS-Top: 0.671 (목표 0.70 미달)
- mean GriTS-Loc: 0.392 (목표 0.50 미달)
- end-to-end p50 129.76 ms, p95 179.73 ms (비용 조건 PASS)
- peak CUDA allocation 408,653,312 bytes

### Consequence
속도 여지는 확인됐으나 구조 품질은 아직 불충분하다. 결과를 보고 threshold를 변경하지 않으며, 모델이 출력한 spanning cell과 header 정보를 버린 현재 후처리의 손실부터 검증한다.

---

## Decision 015

### Date
2026-09-08

### Trigger
초기 TATR 계산이 structure XML 미대응 4페이지를 0점으로 포함한 분모 불일치였음을 audit에서 발견했고, span-aware 후처리를 고정해 재평가했다.

### Decision
P1과 동일하게 미대응 페이지를 not-evaluable로 별도 보고하고, 대응 16페이지의 span-aware preflight를 PASS한다. TATR 300-page screening을 허용하되 P2는 계속 잠근다.

### Evidence
- attempted/completed 20/20, evaluable 16, not-evaluable 4
- exact table count 100%
- atomic Top/Loc 0.839/0.490
- span-aware Top/Loc 0.894/0.510
- end-to-end p50 127.67 ms, p95 223.06 ms
- peak CUDA allocation 408,653,312 bytes
- audit: `docs/figures/tatr_span_loc_audit.png`

### Consequence
초기 0.671/0.392 결과는 삭제하지 않고 superseded로 기록한다. 다음은 300페이지 전체에서 cache, 비용 및 P1 Oracle saving을 다시 계산하는 단계다.

---

## Decision 016

### Date
2026-09-08

### Trigger
20페이지 PASS 후 동일한 span-aware TATR 파이프라인을 300페이지로 확대했다.

### Decision
300페이지 screening을 near-miss FAIL로 판정한다. Loc 기준을 0.50에서 사후 완화하지 않고 TATR/Docling 기반 P2를 시작하지 않는다. 사전에 합의한 대로 downstream RAG의 query-time page/table rescue로 연구 protocol을 피벗한다.

### Evidence
- completed 300/300, evaluable 245, not-evaluable 55
- exact table count 99.18%
- GriTS-Top 0.866 (PASS)
- GriTS-Loc 0.494 (0.50 기준 FAIL, -0.006)
- end-to-end p50 135.79 ms, p95 219.79 ms (PASS)
- peak CUDA allocation 411,431,424 bytes

### Consequence
TATR의 빠른 검출·topology 결과는 보조 evidence로 보존하지만 primary ingestion router 후보로 승격하지 않는다. 다음 Gate는 parser 자체 GriTS가 아니라 fixed downstream retrieval/QA utility와 실제 Strong rescue 비용으로 정의해야 한다.

---

## Decision 017

### Date
2026-09-08

### Trigger
Downstream RAG pivot에 사용할 데이터셋의 접근성과 현재 약 10GB 디스크 제약을 검토했다.

### Decision
QASPER validation 100문항 evidence audit을 text-control 첫 Gate로 사용하고, 통과 후 SPIQA test-A의 table/figure subset으로 확장한다. MMVQA/PDF-MVQA는 Google Drive 분할 배포 접근성을 확인한 뒤 외부 평가 후보로 유지한다.

### Evidence
- QASPER: 1,005 validation questions / 281 papers, human supporting evidence 제공
- SPIQA: table/figure scientific QA에 적합하지만 전체 배포 크기 약 33.6GB
- 현재 C: 여유 공간 약 10GB

### Consequence
QASPER 결과를 multimodal 최종 주장으로 사용하지 않는다. R0는 evidence/chunk/page alignment와 retrieval baseline 가능성만 검증한다.

---

## Decision 018

### Date
2026-09-08

### Trigger
동결된 QASPER validation 100문항에서 human evidence와 canonical paragraph의 정렬을 측정했다.

### Decision
R0 evidence audit을 PASS하고 R1 retrieval baseline을 허용한다. 다음 실행 순서는 Oracle evidence retrieval 후 BM25이며, dense/hybrid는 BM25 결과 확인 뒤 수행한다.

### Evidence
- selected/usable questions: 100/100
- textual evidence items: 174
- mapped items: 163 (93.68%; Gate 90%)
- unique/tied/unmapped: 163/0/11
- evidence types: paragraph 100, figure/table 0, mixed 0
- automated tests: 14 passed

### Consequence
현재 표본은 text-control로만 사용한다. 첫 100문항에 표·그림 증거가 없으므로 멀티모달 효과를 주장하지 않으며, SPIQA 평가 전까지 해당 한계를 모든 요약에 유지한다.

---

## Decision 019

### Date
2026-09-08

### Trigger
R0 고정 문항에 Oracle evidence ranking과 BM25 검색을 실행했다.

### Decision
BM25 단독 결과로 parser routing을 시작하지 않는다. 같은 질문·단락·지표를 유지한 frozen dense baseline과 hybrid를 다음 판정점으로 실행한다.

### Evidence
- evaluated/skipped: 97/3 questions
- Oracle Recall@5 0.9936, nDCG@5 1.0000
- BM25 Recall@1/5/10: 0.1690/0.4368/0.5665
- BM25 MRR 0.3645, nDCG@5 0.3238
- automated tests: 15 passed

### Consequence
lexical baseline은 구현과 평가 sanity check를 통과했지만 evidence recovery가 낮다. Dense 검색도 낮으면 문서 처리 라우팅 전에 retrieval formulation을 수리한다.

---

## Decision 020

### Date
2026-09-08

### Trigger
동일 97문항에 frozen BGE-small-en-v1.5 dense 및 BM25+dense reciprocal-rank fusion을 실행했다.

### Decision
R1 baseline은 완료하지만 parser representation 및 routing 단계는 보류한다. 현재 병목은 document processing 차이보다 evidence retrieval이며, 다음은 failure stratification과 lightweight re-ranking preflight다.

### Evidence
- Dense Recall@1/5/10: 0.1406/0.5414/0.6872; MRR 0.3959; nDCG@5 0.3846
- RRF Recall@1/5/10: 0.1922/0.4978/0.6350; MRR 0.4137; nDCG@5 0.3839
- top-5 candidate union Recall 0.6453; top-10 union Recall 0.7705
- RTX 3090 wall time: 3.44 seconds for 97 questions / 34 papers
- automated tests: 16 passed

### Consequence
Dense는 BM25보다 Recall@5를 10.46%p 높였지만 절대 회수율은 낮다. 단순 RRF의 Recall 하락도 실패 결과로 보존한다. Retrieval 수리 전에는 selective parser의 효용을 평가하지 않는다.

---

## Decision 021

### Date
2026-09-08

### Trigger
BM25 top-10과 dense top-10 합집합을 고정 MiniLM cross-encoder로 재순위화했다.

### Decision
R1.1 reranker를 FAIL로 판정하고 채택하지 않는다. Parser routing, ColPali 및 전체 논문 확장은 계속 보류하며 section-aware chunk/query formulation을 다음 진단으로 수행한다.

### Evidence
- candidate Recall 0.7705, mean candidates 15.15
- reranked Recall@5 0.5190 (Gate 0.65)
- reranked nDCG@5 0.4296 (Gate 0.50)
- MRR 0.4719; GPU wall time 1.61 seconds

### Consequence
현재 문제는 단순 candidate reranking만으로 해결되지 않는다. Canonical paragraph가 section/title context를 잃는 표현 문제를 먼저 검증한다.

---

## Decision 022

### Date
2026-09-08

### Trigger
Plain paragraph가 잃은 paper title/section context를 passage와 query에 선택적으로 추가해 frozen BGE retrieval을 비교했다.

### Decision
Section-aware passage는 유용한 개선으로 보존하지만 R1.2 Gate는 FAIL로 판정한다. Title query variant는 폐기한다. 개발 cohort의 반복 사용을 제한하기 위해 저비용 R1.3 수리를 한 번만 더 허용한다.

### Evidence
- section passage Recall@5/10: 0.5562/0.7556; MRR 0.4913; nDCG@5 0.4484
- title query + section passage Recall@5/10: 0.3326/0.4489
- Gate: Recall@5 >=0.65 and nDCG@5 >=0.50 — FAIL
- automated tests: 18 passed

### Consequence
Section metadata는 이후 representation에 유지할 후보지만 성공으로 승격하지 않는다. R1.3 이후에는 같은 100문항에서 추가 조합을 반복 탐색하지 않고 별도 split을 만든다.

---

## Decision 023

### Date
2026-09-08

### Trigger
마지막 허용 development 실험으로 section dense/BM25 후보와 인접 단락 ±1을 결합해 재순위화했다.

### Decision
R1.3을 near-miss FAIL로 판정하고 development 100문항 탐색을 종료한다. Recall 기준을 0.65에서 완화하지 않는다.

### Evidence
- mean seed/expanded candidates: 15.41/29.06
- candidate Recall 0.9278
- Recall@5 0.6161 (Gate 0.65, FAIL)
- nDCG@5 0.5103 (Gate 0.50, PASS)
- MRR 0.5363, wall time 6.41 seconds

### Consequence
Adjacent context는 유망 신호로 보존하지만 성공 주장을 하지 않는다. 같은 질문에서 추가 조합 탐색을 금지하고 paper-disjoint recovery split을 만든다.

---

## Decision 024

### Date
2026-09-08

### Trigger
R1 개발 탐색 종료 후 recovery 방법 선택과 독립 검증을 분리해야 했다.

### Decision
QASPER validation의 answerable questions를 paper 단위로 development/calibration/certification/final에 고정한다.

### Evidence
- development: 34 papers / 100 questions
- calibration: 62 papers / 200 questions
- certification: 60 papers / 200 questions
- final: 123 papers / 443 questions
- 교집합 paper 0; automated tests 20 passed

### Consequence
다음 recovery 방법 선택은 calibration에서만 한다. Certification/final 결과는 설정 선택에 사용하지 않는다.
