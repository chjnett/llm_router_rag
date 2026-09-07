# Datasets and Metrics

## Dataset 역할 분리

하나의 dataset으로 전체 논문을 평가하지 않는다.

| 역할 | Dataset | 목적 |
|---|---|---|
| Layout | PubLayNet | scientific PDF layout / pre-router feature |
| Table Capability | PubTables-1M | Cheap vs Strong capability label |
| External Table | SciTSR | frozen router external generalization |
| Multimodal Retrieval | PDF-MVQA | retrieval downstream |
| Scientific Multimodal QA | SPIQA | figure/table scientific QA |
| Text-only Scientific QA | QASPER | text-only control |
| Visual Baseline | ViDoRe / ColPali | parsing-free visual retrieval comparison |

---

# 1. PubLayNet

목적:

- scientific document layout
- page structural complexity
- pre-router feature analysis

평가:

- mAP
- class-wise AP

---

# 2. PubTables-1M

Main capability benchmark.

평가:

- GriTS_Top
- GriTS_Con
- GriTS_Loc
- cell F1
- structure F1

---

# 3. SciTSR

External scientific table benchmark.

규칙:

- PubTables에서 threshold freeze
- SciTSR 결과를 보고 threshold 수정 금지

---

# 4. PDF-MVQA

목적:

- multimodal scientific PDF retrieval
- multi-page evidence retrieval

평가:

- Recall@1
- Recall@5
- Recall@10
- MRR
- nDCG@5

---

# 5. SPIQA

목적:

- scientific figures/tables QA
- multimodal downstream quality

평가:

- official metric 우선
- EM/F1/accuracy 병행 가능

---

# 6. QASPER

역할:

- text-only scientific QA control
- supporting evidence 기반 QA

주의:

PDF parsing benchmark로 사용하지 않는다.

---

# 7. Router Metrics

필수:

- AUROC
- AUPRC
- ECE
- Brier Score
- Risk-Coverage Curve
- AURC
- Cheap coverage
- Strong call rate
- observed unsafe
- 95% CI
- exact binomial upper bound

---

# 8. System Metrics

## Parser

- GriTS
- structure F1
- text coverage
- layout mAP

## Retrieval

- Recall@k
- MRR
- nDCG@5

## QA

- EM
- F1
- official dataset metric

## Cost

- p50
- p95
- GPU seconds/page
- energy/page
- peak VRAM
- Strong call rate
- normalized cost

