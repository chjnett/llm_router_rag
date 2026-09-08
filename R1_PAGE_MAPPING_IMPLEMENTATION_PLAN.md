# R1-P Complete-PDF Evidence Page Mapping Plan

## 목적

QASPER의 paragraph-level retrieval 실패가 실제 query-time page rescue 실패와 같은지 확인한다. 이 실험은 Recall@5 기준을 완화하지 않으며 ColPali, VLM 또는 parser Router를 학습하지 않는다.

## 표본 동결

- Source split: QASPER calibration only
- Eligibility: calibration 결과에서 exact-mapped textual evidence를 가진 질문이 2개 이상인 paper
- Ordering: paper id 오름차순
- Sample: 첫 10 papers와 그 paper에 속한 모든 calibration evaluable questions
- PDF source: canonical arXiv paper id의 born-digital PDF
- Download 또는 native text 추출 실패 paper는 교체하지 않고 실패로 기록

## 자동 페이지 매핑 규칙

1. PyMuPDF native text를 page별로 추출한다.
2. Unicode NFKC, case folding, line-break hyphen 복원, 공백 축약을 적용한다.
3. Canonical paragraph가 한 page의 normalized text에 exact substring이면 exact mapping이다.
4. Exact가 아니면 paragraph token의 page 내 coverage를 계산한다.
5. Coverage >=0.80이고 best-second page margin >=0.10일 때만 approximate mapping으로 허용한다.
6. 그 외는 ambiguous/unmapped로 남기고 threshold를 결과 후 변경하지 않는다.

## 측정

- PDF download/parse success
- born-digital native text coverage
- canonical paragraph exact/approximate/ambiguous/unmapped 비율
- human evidence paragraph의 page mapping rate
- 기존 section-dense 및 adjacent rescue 결과를 page id로 투영한 Recall@1/5
- 인접 page ±1 rescue Recall@5
- page당 native scan latency p50/p95

## Gate

```text
PDF parse success >= 8/10 papers
evidence page mapping rate >= 80%
mapped evaluable questions >= 30
page-level Recall@5 >= 65%
```

모두 통과할 때만 10-paper downstream representation preflight 또는 작은 ColPali P1-V를 설계한다. 실패하면 QASPER page-rescue branch를 중단하고 page-grounded dataset으로 이동한다.

## 산출물

- frozen paper/question manifest
- PDF SHA-256 및 source URL
- paragraph-to-page mapping cache
- page-level retrieval result JSON
- visual audit sheet for ambiguous mappings
- phase report와 Decision Log
