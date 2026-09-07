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
- [ ] parser 간 cell bbox 의미 통일 후 GriTS-Loc 확정
- [ ] GriTS-Con용 word/content annotation 연결

### Gate
Cheap / Strong 품질과 실제 비용비를 신뢰할 수 있게 측정했는가?

**현재 판정: HOLD.** GriTS-Top은 유효한 신호를 보였으나 cell bbox 의미가 달라 GriTS-Loc을 확정할 수 없으므로 P1을 시작하지 않는다.

---

# Week 2 — P1 Oracle / Capability

- [ ] capability label
- [ ] Cheap sufficient coverage
- [ ] Strong-needed rate
- [ ] both-fail rate
- [ ] Oracle routing
- [ ] Oracle saving
- [ ] model pair decision

### Stop Rule

- [ ] Oracle saving >= 15% 권장
- [ ] Ccheap/Cstrong < 0.50 권장

FAIL이면 모델쌍 변경.

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
