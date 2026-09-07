# Migration Plan

기존 저장소 `C:\llm_models\llm_router`는 reference-only이며 이 계획 작성 과정에서도 수정하지 않았다. 신규 구현 위치는 `C:\llm_models\caproute-rag`이다.

## KEEP

직접 복사하지 않고 동작과 테스트 계약을 보존하여 신규 저장소에 독립 구현한다.

| 기존 경로 | 역할 | 신규 경로 | 이유 | 변경 필요 | dependency |
|---|---|---|---|---|---|
| `src/common.py` | YAML 로딩, seed, JSON/JSONL I/O | `src/caproute/core/{config,repro,io}.py` | 작고 검증 가능한 범용 기능 | 책임별 분리, atomic write와 config hash 추가 | stdlib, PyYAML, NumPy, optional PyTorch |
| `src/power_metrics.py` | `nvidia-smi` 기반 전력 표본 수집 | `src/caproute/benchmark/power.py` | RTX 3090 실측 비용에 필요 | provenance와 오류 상태 추가 | `nvidia-smi`, stdlib |

## PORT

| 기존 경로 | 역할 | 신규 경로 | 필요한 변경 | dependency |
|---|---|---|---|---|
| `src/run_model_screening.py` | p50/p95, CUDA synchronize, peak VRAM, raw output 저장 | `src/caproute/benchmark/harness.py` | prompt/model 루프를 page/parser 루프로 교체; warmup/repeat/cache hit 분리 | NumPy, optional PyTorch |
| `src/run_risk_calibration.py::bootstrap_metrics` | paired bootstrap CI | 향후 `src/caproute/statistics/bootstrap.py` | document-cluster bootstrap으로 변경; P0에서는 미이식 | NumPy |
| `src/run_risk_bound_calibration.py::binomial_upper` | exact one-sided binomial upper bound | 향후 `src/caproute/statistics/risk.py` | capability unsafe 정의로 일반화; P0에서는 미이식 | SciPy |
| `src/analyze_cascade_feasibility_guard.py` | 비용 절감 가능성 guard | 향후 `src/caproute/routing/feasibility.py` | LLM 호출 비용을 parser page/region 비용으로 변경; P1 전에는 실행하지 않음 | NumPy |
| `src/metrics.py` | 비용 정규화와 operating-point 계약 | 향후 `src/caproute/routing/metrics.py` | accuracy를 parsing/downstream utility로 교체; P2 전에는 미이식 | NumPy |

## REWRITE

| 기존 경로 | 아이디어 | 신규 구현 | 이유 |
|---|---|---|---|
| `src/task_harness.py`, `src/scoring.py` | 입력 정규화와 자동 평가 | `datasets/pubtables.py`, `evaluation/parsing.py` | task answer가 아니라 document/table structure를 평가해야 함 |
| `src/inference.py`, `src/model_registry.py` | 구현체 registry와 공통 호출 계약 | `parsers/base.py`, `parsers/cheap.py`, `parsers/strong.py` | parser는 LLM generate와 다른 입력·출력·오류 계약 필요 |
| confidence/verifier 계열 | cheap output 자체의 신뢰도 사용 | P2의 PDF feature/output verifier | P0 Gate 전에는 router를 만들지 않음 |

## DROP

| 기존 경로 | 이유 |
|---|---|
| `src/prepare_*gsm8k*`, `src/*math500*`, `src/*asdiv*`, `src/*svamp*` | 수학 답안 도메인 전용 |
| `src/*mmlu*`, `src/*kmmlu*` | 객관식/option-logit 전용 |
| `src/*mbpp*` | 코드 실행 및 answer extractor 전용 |
| 기존 prompts 및 answer-only verifier/cascade | 연구 단위를 LLM 답변에서 document representation으로 전환 |
| 기존 artifacts, paper, HTML | 과거 결과이며 신규 실험 provenance와 혼합 금지 |

## Dependency 결정

- P0 필수: Python 3.10+, PyYAML, NumPy, PyMuPDF.
- P0 선택: PyTorch(CUDA VRAM 계측), Docling(Strong adapter), psutil.
- Docling은 extra로 격리하여 기본 테스트가 모델 다운로드 없이 실행되게 한다.
- PubTables-1M 데이터와 모델 weight는 Git에 넣지 않고 경로 및 revision만 config/manifest에 기록한다.

## 완료 조건

- [x] 기존 utility 후보 조사
- [x] KEEP/PORT/REWRITE/DROP 분류
- [x] 신규 파일 경로 결정
- [x] dependency 충돌 및 선택 dependency 경계 확인
- [x] 과거 결과와 신규 코드/출력 경로 분리

