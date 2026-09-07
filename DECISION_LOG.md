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

