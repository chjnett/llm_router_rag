# CapRoute 현재 필독 문서 가이드

Markdown을 읽기 전에 전체 흐름을 쉬운 말로 보고 싶다면 [architecture_explained.html](architecture_explained.html)을 먼저 연다.

## 가장 짧은 읽기 순서

현재 결과와 다음 판단만 이해하려면 아래 6개 문서를 순서대로 읽으면 된다. 예상 총 소요 시간은 약 45~60분이다.

| 순서 | 문서 | 예상 시간 | 읽어야 하는 이유 | 읽은 뒤 알게 되는 것 |
|---:|---|---:|---|---|
| 1 | [README.md](README.md) | 5분 | 프로젝트의 범위와 핵심 원칙을 빠르게 파악 | 무엇을 해결하는 연구인지 |
| 2 | [CURRENT_RESEARCH_STATUS_AND_NEXT_PLAN.md](CURRENT_RESEARCH_STATUS_AND_NEXT_PLAN.md) | 10분 | 가장 최신 결과와 현재 판단 확인 | 어디까지 성공·실패했고 다음 단계가 무엇인지 |
| 3 | [docs/P1V_SPIQA_PREFLIGHT_REPORT.md](docs/P1V_SPIQA_PREFLIGHT_REPORT.md) | 15분 | 최신 SPIQA·ColSmol 실험의 전체 근거 확인 | R@1 67.9→71.6%, route 12.35%, 통계 미확정의 의미 |
| 4 | [ARCHITECTURE.md](ARCHITECTURE.md) | 10분 | Cheap→Strong 선택 처리 구조 이해 | 시스템 구성요소와 데이터 흐름 |
| 5 | [DECISION_LOG.md](DECISION_LOG.md) | 10분 | 결과에 따라 방향을 바꾼 이유 확인 | 실패를 숨기지 않고 어떤 Gate로 결정했는지 |
| 6 | [TODO_ROADMAP.md](TODO_ROADMAP.md) | 5분 | 완료·잠금·다음 작업 확인 | 지금 해야 할 일과 하지 말아야 할 일 |

## 실험을 직접 실행하기 전에 추가로 읽을 문서

| 우선순위 | 문서 | 용도 |
|---|---|---|
| 필수 | [RESEARCH_RULES.md](RESEARCH_RULES.md) | 데이터 누수, 사후 임계값 변경, 실패 결과 보존 규칙 |
| 필수 | [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | split, cache, 측정 및 Gate 적용 절차 |
| 필수 | [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | 환경과 재현 방법 |
| 참고 | [DATASETS_AND_METRICS.md](DATASETS_AND_METRICS.md) | 데이터셋과 Recall/MRR/GriTS 등 지표 정의 |
| 참고 | [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | 연구 배경과 장기 목표 |

## 이전 단계의 근거가 필요할 때만 읽을 문서

| 질문 | 문서 |
|---|---|
| 왜 ingestion-time parser routing을 포기했는가? | [docs/P1_PHASE_REPORT.md](docs/P1_PHASE_REPORT.md), [docs/P1_REPAIR_PHASE_REPORT.md](docs/P1_REPAIR_PHASE_REPORT.md) |
| QASPER retrieval은 왜 중단했는가? | [docs/R1_RETRIEVAL_BASELINE_REPORT.md](docs/R1_RETRIEVAL_BASELINE_REPORT.md), [docs/R1_CALIBRATION_REPORT.md](docs/R1_CALIBRATION_REPORT.md) |
| Page rescue는 비용을 실제로 줄였는가? | [docs/R1_PAGE_MAPPING_REPORT.md](docs/R1_PAGE_MAPPING_REPORT.md), [docs/R2_PAGE_RESCUE_COST_REPORT.md](docs/R2_PAGE_RESCUE_COST_REPORT.md) |
| 초기 평가 harness는 어떻게 검증했는가? | [docs/P0_PHASE_REPORT.md](docs/P0_PHASE_REPORT.md) |

## 지금 읽지 않아도 되는 문서

`*_IMPLEMENTATION_PLAN.md`, `MIGRATION_PLAN.md`, `PHASE_REPORT_TEMPLATE.md`, `TATR_PREFLIGHT_PLAN.md`는 구현 이력이나 작성 양식이다. 현재 연구 결과를 이해하는 데는 필수가 아니며, 해당 단계를 다시 구현할 때만 확인한다.

## 현재 기억해야 할 결론

> 확대된 locked selector는 독립 81문항에서 Caption R@1을 67.9%에서 71.6%로 높이고 ColSmol 호출을 12.35%로 제한했다. 그러나 95% 신뢰구간이 0을 포함하므로 통계적 성공으로 확정하지 않는다. 입력 해상도 실험에서는 256M R@1이 36%에서 58%로 상승했고, 500M은 전체 R@1을 더 높이지 못해 거절했다. 현재 표현은 `ColSmol-256M + 원본 해상도`이며 다음 단계는 외부 멀티모달 데이터셋의 독립 인증이다.
