# Codex Master Prompt

아래 지시를 이 repository의 최상위 작업 규칙으로 사용하라.

---

이 프로젝트는 연구용 코드베이스다.

프로젝트 이름:

> **CapRoute: Cost-Constrained Capability Routing for Scientific PDF RAG**

먼저 repository root에 있는 다음 문서를 순서대로 읽어라.

1. `PROJECT_CONTEXT.md`
2. `RESEARCH_RULES.md`
3. `ARCHITECTURE.md`
4. `MIGRATION_PLAN.md`
5. `TODO_ROADMAP.md`
6. `EXPERIMENT_PROTOCOL.md`
7. `DATASETS_AND_METRICS.md`
8. `REPRODUCIBILITY.md`

## 핵심 연구 목표

영문 born-digital scientific paper PDF에서 모든 페이지를 비싼 parser/VLM으로 처리하지 않는다.

대신:

- Cheap document processing이 충분한 page/region은 Cheap path로 처리하고
- Strong processing이 실제로 필요한 page/region만 Strong parser/VLM로 escalate하고
- downstream RAG retrieval/QA 품질을 Always Strong에 가깝게 유지하면서
- 실제 ingestion latency/cost/GPU usage를 줄인다.

이 연구는 단순 Small LLM -> Large LLM routing 프로젝트가 아니다.

핵심 표현은:

> **Cheap Document Representation -> Strong Document Representation Routing**

이다.

## 현재 작업 방식

기존 research repository는 reference-only다.

기존 repository를 직접 수정하지 마라.

새 repository에서 구현하라.

기존 repository에서 아래 utility만 조사한다.

- experiment logging
- seed/reproducibility
- latency benchmark
- VRAM measurement
- energy measurement
- calibration
- bootstrap confidence interval
- exact binomial risk bound
- feasibility guard
- result serialization

다음 domain-specific 코드는 새 프로젝트로 그대로 가져오지 마라.

- GSM8K/MATH adapters
- MMLU/KMMLU adapters
- MBPP adapters
- 기존 prompts
- answer-only verifier
- A/B/C/D option parsing
- task-specific answer extractors

## 첫 번째 작업

코딩을 바로 시작하지 말고 먼저 `MIGRATION_PLAN.md`를 실제 기존 repository 분석 결과로 채워라.

모든 재사용 후보를 다음 네 범주로 분류한다.

- KEEP
- PORT
- REWRITE
- DROP

각 항목에 반드시:
- 기존 파일 경로
- 재사용 이유
- 신규 경로
- 변경 필요 여부
- dependency
를 적어라.

그 다음 `P0_IMPLEMENTATION_PLAN.md`를 생성하라.

내용:
- 현재 repository 상태
- 생성/변경할 파일
- 모듈 책임
- dependency
- P0 실행 명령
- 예상 output
- 완료 조건
- 예상 failure mode

그 후에만 P0 구현을 시작하라.

## 지금 구현할 범위: P0만

P0 목표:

1. repository scaffold
2. config system
3. logging / seed / environment metadata
4. PubTables-1M subset loader
5. Cheap Parser interface
6. Strong Parser interface
7. Canonical IR
8. parsing quality evaluator
9. latency / VRAM benchmark harness
10. raw prediction caching
11. 300~500 sample screening 실행 가능 구조

## 아직 하지 말 것

- Router training
- threshold tuning
- QASPER RAG
- SPIQA RAG
- PDF-MVQA full retrieval
- ColPali full baseline
- Query-time VLM rescue
- 전체 dataset inference
- 대규모 hyperparameter sweep

## 절대 지켜야 할 연구 규칙

1. Baseline을 Proposed method보다 먼저 구현한다.
2. Calibration / Certification / Final / External split을 섞지 않는다.
3. Certification 결과를 hyperparameter tuning에 사용하지 않는다.
4. External test를 보고 threshold를 다시 고르지 않는다.
5. 모든 inference output을 cache한다.
6. 실패 실험을 삭제하지 않는다.
7. config와 git commit을 모든 결과에 기록한다.
8. parser-specific output을 downstream에 직접 넘기지 않고 Canonical IR을 사용한다.
9. GPU가 RTX 3090 24GB 하나라는 제약을 항상 고려한다.
10. 모델 크기가 아니라 실제 latency/GPU seconds/energy를 비용으로 측정한다.

## Phase 종료 보고

각 Phase가 끝나면 `PHASE_REPORT_TEMPLATE.md` 형식으로 보고서를 생성한다.

Gate가 FAIL이면 다음 Phase로 자동 진행하지 않는다.

먼저 실패 원인을 분석하고 다음 후보를 제안한다.

