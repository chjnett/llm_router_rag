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

---

# Week 3 — P2 Router

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
