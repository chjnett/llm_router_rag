# Project Context

## 1. 연구 배경

기존 연구에서는 capability-aware routing을 통해 Lower/Upper 모델을 선택했다.

핵심 경험:

- 작은 모델이라고 실제 wall-clock latency가 항상 작은 것은 아니었다.
- Lower-first는 결국 Upper로 escalation되는 요청에서 `Lower + Upper` 비용을 모두 지불한다.
- 일부 task에서는 cascade가 Always Upper보다 비싸졌다.
- feasibility guard가 필요했다.
- MMLU one-forward routing에서는 일부 조건에서 품질 유지와 latency 절감이 함께 재현되었다.
- calibration drift와 threshold transfer가 주요 병목이었다.

이 경험을 Scientific PDF RAG로 확장한다.

---

## 2. 새로운 연구 문제

Scientific paper PDF의 page/region 처리 난이도는 균일하지 않다.

예:

- native text 중심 page
- 단순 1~2열 본문
- 간단한 table
- 복잡한 spanning table
- figure-heavy page
- equation-heavy page
- multi-column layout
- caption / footnote / references

모든 page를 동일한 Strong/VLM path로 처리하는 것은 낭비일 수 있다.

---

## 3. 연구 질문

### RQ1
Scientific PDFs에서 Cheap Processing으로 충분한 page/region과 Strong Processing이 필요한 page/region이 실제로 공존하는가?

### RQ2
입력 구조와 Cheap output signal로 `Strong processing이 실제로 필요한 경우`를 예측할 수 있는가?

### RQ3
Selective Strong Processing이 Always Strong 대비 downstream retrieval/QA utility를 유지하면서 실제 ingestion cost/latency를 줄이는가?

### RQ4
PubTables에서 개발한 routing policy가 SciTSR 등 외부 scientific document distribution에서도 유지되는가?

---

## 4. 첫 논문의 범위

### 포함

- English
- born-digital PDFs
- scientific papers
- text
- tables
- figures
- captions
- equations
- multi-column layout

### 제외

- scanned-only PDF
- handwriting
- receipts
- contracts
- slides
- arbitrary web documents
- multilingual generalization

범위를 넓히지 않는다.

---

## 5. Main Contribution

> **Cost-constrained selective document processing for Scientific PDF RAG**

Main contribution은 하나로 유지한다.

초기 ingestion-only parser pair는 Oracle Gate를 통과하지 못했다. 현재 main **후보**는 query-time selective Strong/visual rescue이며, R1.1 retrieval Gate와 후속 cost-quality Gate를 통과해야만 main architecture로 승격한다. ColPali는 별도 visual baseline/후보 경로다.

---

## 6. 예상 논문 주장

### Claim 1
Scientific PDFs contain heterogeneous document-processing difficulty.

### Claim 2
Capability-aware routing can identify pages where inexpensive processing is sufficient.

### Claim 3
Selective strong processing preserves downstream scientific retrieval/QA utility while reducing ingestion cost relative to Always Strong.

이 세 Claim과 직접 관련 없는 기능은 Main 실험 이후로 미룬다.
