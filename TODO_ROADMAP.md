# TODO Roadmap

## Week 0 — Repository / Migration

- [x] 새 repo 생성
- [x] 이 starter bundle 복사
- [x] 기존 repo 위치 기록
- [x] MIGRATION_PLAN.md 작성
- [x] P0_IMPLEMENTATION_PLAN.md 작성

---

# Week 1 — P0 Harness

- [x] repo scaffold
- [x] config system
- [x] logging / result serialization
- [x] seed
- [x] environment metadata
- [x] PubTables subset loader
- [x] Cheap Parser interface
- [x] Strong Parser interface
- [x] Canonical IR
- [x] parsing evaluator (P0 proxy; official GriTS pending)
- [x] latency harness
- [x] VRAM measurement hook
- [x] prediction cache
- [x] 300-page sample run
- [x] Cheap/Strong aligned P0 comparison
- [x] PubTables row/column shape diagnostic (245 mapped pages)
- [x] GriTS-Top/Loc factored 2D-MSS 구현 및 공식 코드 교차검증
- [x] GriTS-Top 245-page screening
- [x] Docling tight-text bbox를 cell-region bbox로 재구성
- [x] GriTS-Loc 재평가 (Strong 0.204 → 0.528)
- [x] 대표/최악 표의 cell-region 시각 점검
- [ ] GriTS-Con용 word/content annotation 연결

### Gate
Cheap / Strong 품질과 실제 비용비를 신뢰할 수 있게 측정했는가?

**현재 판정: PASS (topology/location screening).** 비용비, GriTS-Top, 재구성 GriTS-Loc과 시각 audit을 신뢰할 수 있게 측정했다. GriTS-Con은 후속 내용 품질 항목으로 유지한다.

---

# Week 2 — P1 Oracle / Capability

Frozen rule: exact table count AND GriTS-Top ≥ 0.80 AND GriTS-Loc ≥ 0.50.

- [x] capability label
- [x] Cheap sufficient coverage: 28/245 (11.43%)
- [x] Strong-needed rate: 123/245 (50.20%)
- [x] both-fail rate: 94/245 (38.37%)
- [x] Oracle routing
- [x] Oracle saving: 9.86%
- [x] model pair decision: current PyMuPDF/Docling pair rejected for P2

### Stop Rule

- [ ] Oracle saving >= 15% 권장 — **FAIL (9.86%)**
- [x] Ccheap/Cstrong < 0.50 권장 — PASS (0.137)

**현재 판정: FAIL.** 기준을 사후 변경하지 않는다. P2는 잠그고 Cheap/Strong 후보 교체 또는 설정 개선을 같은 cohort와 기준으로 재검증한다.

### Repair Screening

- [x] PyMuPDF union/refine 300-page 평가 — FAIL (Oracle saving 9.17%)
- [x] PyMuPDF text/text 300-page 평가 — FAIL (0%)
- [x] PyMuPDF raw-lines 300-page 평가 — FAIL (9.81%)
- [x] pdfplumber 독립 lightweight parser 20-page preflight — STOP (proxy 0.183, p50 95.97ms)
- [x] Table Transformer detection 20-page preflight — PASS (proxy 1.000, model p50 17.36ms)
- [x] Table Transformer 초기 structure 계산 — 분모 오류 발견 및 superseded
- [x] TATR spanning/header postprocessing 및 시각 audit — PASS (Top 0.894, Loc 0.510, p50 127.67ms)
- [x] TATR 300-page screening — **FAIL near-miss** (Top 0.866, Loc 0.494, p50 135.79ms)
- [x] Query-time page/table rescue RAG pivot protocol 작성

### RAG Pivot R0

- [x] QASPER text-control 및 SPIQA multimodal 순서 결정
- [x] R0 evidence audit 기준 고정
- [x] QASPER metadata cache 및 hash
- [x] validation 100-question manifest 고정
- [x] evidence type/mapping audit — **PASS (100 usable, 93.68% exact mapping)**
- [x] R1 Oracle evidence retrieval
- [x] R1 BM25 baseline — Recall@5 0.4368, nDCG@5 0.3238
- [x] R1 frozen dense baseline — Recall@5 0.5414, nDCG@5 0.3846
- [x] R1 BM25+dense RRF — Recall@5 0.4978 (**dense보다 하락**)
- [x] R1.1 retrieval failure stratification — dense hit@5 59.79%; neither 28/97; long-paper/multi-evidence 병목
- [x] R1.1 lightweight re-ranking preflight — **FAIL** (Recall@5 0.5190, nDCG@5 0.4296)
- [x] R1.2 section-aware chunk/query formulation — **FAIL Gate**, section passage R@5 0.5562 / R@10 0.7556
- [x] R1.3 adjacent-window + section candidate rescue — **near-miss FAIL** (R@5 0.6161, nDCG@5 0.5103)
- [x] QASPER document-disjoint recovery splits 고정 — calibration 200 / certification 200 / final 443
- [x] R1 recovery calibration — **FAIL** (best R@5 0.6303, nDCG@5 0.5122)
- [x] MiniLM-L12 비교 — L6보다 악화, 폐기
- [x] R1-P 10 complete-PDF evidence page mapping — **PREFLIGHT PASS** (page R@5 0.8971)
- [x] R2-P 10-paper cost preflight — **CONDITIONAL PASS** (cached workload: recall 0.9706, time -18.26%)
- [x] Cheap/Strong output evidence coverage — 둘 다 100%, QASPER text에서 Strong gain 없음
- [x] P1-V SPIQA small multimodal dataset access/manifest audit
- [x] P1-V 50-question Always Text vs CLIP/ColSmol GPU preflight — visual complementarity PASS
- [x] P1-V paper-disjoint 100-question confirmation — oracle complementarity reproduced
- [x] P1-V inference-only Logistic selector — **FAIL** (R@1 0.65→0.62)
- [ ] P1-V independent training/calibration cohort >=300 questions 확보
- [ ] Strong both-fail repair 후보 평가 (RAG retrieval 차이 확인 전 보류)

---

# Week 3 — P2 Router

**현재 잠금:** 50→100 paper-disjoint selector가 일반화에 실패했다. 별도 300+ 학습/보정 cohort 전에는 확대하지 않는다.

- [ ] feature extractor
- [ ] Logistic Regression
- [ ] ExtraTrees
- [ ] XGBoost
- [ ] OOF
- [ ] AUROC
- [ ] AUPRC
- [ ] ECE
- [ ] Brier
- [ ] Risk-Coverage
- [ ] AURC
- [ ] feature importance

---

# Week 4 — P3 Adaptive System

- [ ] Always Cheap
- [ ] Always Strong
- [ ] Rule-Based
- [ ] Input Router
- [ ] Lower-first + Verifier
- [ ] Full Proposed
- [ ] end-to-end latency
- [ ] cost report

Target:

```text
quality retention >= 95%
saving >= 10%
```

---

# Week 5 — Calibration / Certification

- [ ] calibration split freeze
- [ ] threshold selection
- [ ] threshold freeze
- [ ] certification
- [ ] bootstrap CI
- [ ] exact binomial upper bound
- [ ] risk-coverage report

---

# Week 6 — SciTSR External

- [ ] loader
- [ ] frozen evaluation
- [ ] domain shift analysis
- [ ] feature distribution comparison

---

# Week 7 — Retrieval

- [ ] chunker
- [ ] embedder
- [ ] index
- [ ] retriever
- [ ] PDF-MVQA
- [ ] Recall@k
- [ ] MRR
- [ ] nDCG@5

---

# Week 8 — Scientific QA

- [ ] SPIQA
- [ ] QASPER
- [ ] fixed answer model
- [ ] EM/F1/official metrics
- [ ] failure analysis

---

# Week 9 — Visual Baseline

- [ ] ColPali
- [ ] ViDoRe-compatible evaluation
- [ ] latency
- [ ] GPU usage
- [ ] index storage
- [ ] visual-heavy subset

---

# Week 10 — Extension

Main 연구 PASS 후에만.

- [ ] Query-time rescue
- [ ] query type detector
- [ ] top-k page reprocessing
- [ ] rescue ablation

---

# Final Deliverables

- [ ] frozen config files
- [ ] final split files
- [ ] full metric CSV
- [ ] publication plots
- [ ] failure analysis
- [ ] ablation table
- [ ] reproducibility appendix
- [ ] final architecture diagram
