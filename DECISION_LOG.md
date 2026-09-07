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
