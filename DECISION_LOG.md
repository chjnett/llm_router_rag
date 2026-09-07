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
