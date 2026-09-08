# CapRoute Codex Starter Bundle

> 현재 연구 상태와 실험 결과는 브라우저에서 [`index.html`](index.html)을 열어 확인한다.

## Project

**CapRoute: Cost-Constrained Capability Routing for Scientific PDF RAG**

이 폴더는 Codex가 새 repository에서 연구 구현을 시작할 때 사용하는 handoff 패키지다.

## 사용 순서

1. 새 repository를 만든다.
2. 이 폴더의 모든 `.md` 파일을 repository root에 복사한다.
3. 기존 연구 repository는 별도 위치에 그대로 보존한다.
4. `CODEX_MASTER_PROMPT.md`의 내용을 Codex 첫 프롬프트로 전달한다.
5. Codex가 먼저 `MIGRATION_PLAN.md`를 채우게 한다.
6. 그 다음 `P0`만 구현한다.
7. 각 Phase 종료 시 `PHASE_REPORT_TEMPLATE.md` 형식으로 결과를 남긴다.

## 반드시 먼저 읽을 파일

1. `CODEX_MASTER_PROMPT.md`
2. `PROJECT_CONTEXT.md`
3. `RESEARCH_RULES.md`
4. `ARCHITECTURE.md`
5. `MIGRATION_PLAN.md`
6. `TODO_ROADMAP.md`
7. `EXPERIMENT_PROTOCOL.md`

## 가장 중요한 원칙

이 프로젝트의 핵심은 단순한 `Small LLM -> Large LLM routing`이 아니다.

> **Cheap Document Processing -> Strong Document Processing을 capability-aware하게 선택하여 scientific PDF RAG의 품질을 유지하면서 ingestion 비용을 줄이는 것**

첫 논문 범위는 **영문 born-digital scientific paper PDF**로 제한한다.

## 새 repo 권장 구조

```text
caproute-rag/
├─ README.md
├─ CODEX_MASTER_PROMPT.md
├─ PROJECT_CONTEXT.md
├─ RESEARCH_RULES.md
├─ ARCHITECTURE.md
├─ MIGRATION_PLAN.md
├─ TODO_ROADMAP.md
├─ EXPERIMENT_PROTOCOL.md
├─ DATASETS_AND_METRICS.md
├─ REPRODUCIBILITY.md
├─ PHASE_REPORT_TEMPLATE.md
├─ DECISION_LOG.md
├─ configs/
├─ data/
├─ src/
├─ experiments/
├─ outputs/
└─ docs/
```

## 첫 번째 실제 목표

처음부터 Router를 학습하지 않는다.

먼저 P0/P1에서 아래 세 가지를 확인한다.

1. Cheap path가 충분한 sample이 실제로 존재하는가?
2. Cheap path가 Strong path보다 실제로 충분히 싼가?
3. 완벽한 router를 가정했을 때도 10~15% 이상 절감할 여지가 있는가?

이 세 조건이 부족하면 모델쌍을 바꾸고, 억지로 Router 실험으로 넘어가지 않는다.

## 현재 구현 상태

- P0 Cheap/Strong 300-page screening 완료
- Cheap baseline: PyMuPDF 1.28.2
- Strong baseline: Docling 2.126.0 / CUDA
- Canonical IR, raw prediction cache, latency/VRAM/power harness 구현
- PubTables validation GriTS-Top/Loc 평가 및 Microsoft 공식 코드 교차검증 완료
- GriTS-Top: Cheap `0.190`, Strong `0.904` (245 pages / 291 tables)
- offline test: `11 passed`
- GriTS-Loc: Cheap `0.114`, Strong `0.528` (Docling cell-region 재구성 후)
- P0 Gate: **PASS** — topology/location screening과 시각 audit 완료
- P1 Oracle: Cheap sufficient `11.43%`, Strong sufficient `58.37%`, both-fail `38.37%`
- P1 Oracle saving: `9.86%` (사전 목표 `15%` 미달), P1 Gate: **FAIL**
- TATR 20-page span-aware preflight: Top `0.894`, Loc `0.510`, p50 `127.67 ms` — PASS
- TATR 300-page screening: Top `0.866`, Loc `0.494`, p50 `135.79 ms` — **FAIL near-miss**
- 다음 단계: P2를 잠그고 downstream RAG의 query-time page/table rescue pivot protocol 설계

실행 경로와 완료 조건은 `P0_IMPLEMENTATION_PLAN.md`, `P1_IMPLEMENTATION_PLAN.md`, 현재 판단은 `docs/P0_PHASE_REPORT.md`, `docs/P1_PHASE_REPORT.md`를 따른다.
