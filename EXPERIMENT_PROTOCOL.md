# Experiment Protocol

## P0 — Harness Screening

Sample:

```text
300~500 pages/tables
```

목표:

Cheap/Strong 실제 비용과 품질 파악.

필수 출력:

| parser | quality | p50 | p95 | GPU sec/page | peak VRAM |
|---|---:|---:|---:|---:|---:|

P0에서는 Router를 만들지 않는다.

---

## P1 — Capability / Oracle

계산:

- Cheap sufficient coverage
- Strong-needed rate
- both-fail rate
- Ccheap / Cstrong
- Oracle quality
- Oracle normalized cost
- Oracle saving

### Stop Rule

권장:

```text
Oracle saving < 15%
```

이면 해당 parser pair 중단.

---

## P2 — Router

Sample:

```text
2,000~5,000
```

모델:

- Logistic Regression
- ExtraTrees
- XGBoost

평가:

- AUROC
- AUPRC
- ECE
- Brier
- Risk-Coverage
- AURC

최소 screening signal:

```text
AUROC >= 0.60
```

단 AUROC만으로 PASS하지 않는다.

---

## P3 — Full Adaptive

비교:

- Always Cheap
- Always Strong
- Rule-Based
- Pre-Router only
- Lower-first + Verifier
- Full Proposed

목표:

```text
quality retention >= 95%
saving >= 10%
```

---

## P4 — Calibration

Calibration split에서만 threshold를 선택한다.

완료 즉시 threshold freeze.

---

## P5 — Certification

독립 split.

평가:

- quality retention
- saving
- observed unsafe
- confidence interval
- exact binomial upper risk
- risk-coverage

결과 확인 후 threshold 수정 금지.

---

## P6 — External Table

SciTSR.

frozen router / frozen threshold.

---

## P7 — Retrieval

PDF-MVQA.

비교:

- Always Cheap
- Always Strong
- Rule
- Proposed
- Visual baseline

### R1.1 Retrieval Repair Gate

QASPER 100문항은 text-control 개발 cohort다. BM25 top-10과 frozen dense top-10 후보에서 고정 lightweight reranker를 평가한다.

```text
Recall@5 >= 0.65
nDCG@5 >= 0.50
```

통과 전 parser representation/router 효과를 측정하지 않는다. 이 cohort에서 고른 설정은 별도 document-disjoint split에서 다시 고정 평가한다.

---

## P8 — QA

- SPIQA
- QASPER

Answer model은 가능한 한 고정한다.

Parser/routing 효과와 generator 효과를 섞지 않는다.

---

## P9 — Visual Baseline

ColPali / ViDoRe-compatible setup.

비교:

- retrieval quality
- ingestion latency
- index size
- GPU time
- visual-heavy subset

전체 실행 전에 20~50 question/page preflight를 수행한다. full dataset 다운로드 전에 manifest, disk budget, index bytes/page를 확인한다.

---

## P10 — Extension

Main 결과가 성공했을 때만:

- query-time rescue
- top-k page reprocessing
- rescue trigger ablation
