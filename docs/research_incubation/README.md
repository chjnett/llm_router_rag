# 연구 인큐베이션 폴더

## 현재 상태

**OPEN — 최종 연구 주제 미잠금**

이 폴더는 논문 주제를 성급히 확정하지 않고 후보를 비교하고, 반증을 찾고, 작은 실험으로 제거하고, 필요하면 피벗하기 위한 living document다. 확정된 실험 프로토콜이나 결과 보고서와 섞지 않는다.

## 사용 순서

| 순서 | 문서 | 역할 |
|---:|---|---|
| 1 | [01_DIRECTION_BOARD.md](01_DIRECTION_BOARD.md) | 현재 연구 방향 후보와 상태 비교 |
| 2 | [02_QUESTION_BACKLOG.md](02_QUESTION_BACKLOG.md) | 아직 답하지 못한 질문과 답하는 방법 관리 |
| 3 | [03_EVIDENCE_AND_COUNTEREVIDENCE.md](03_EVIDENCE_AND_COUNTEREVIDENCE.md) | 지지 근거와 반증을 같은 표에 기록 |
| 4 | [04_PIVOT_DECISION_LOG.md](04_PIVOT_DECISION_LOG.md) | 유지·수정·중단·피벗 결정을 추적 |
| 5 | [05_TOPIC_LOCK_GATE.md](05_TOPIC_LOCK_GATE.md) | 최종 주제를 잠글 조건 확인 |

## 갱신 규칙

새 아이디어나 실험 결과가 생길 때 다음 순서로 갱신한다.

1. 방향 후보 또는 질문을 등록한다.
2. 먼저 문헌 검색이나 작은 실험으로 답할 수 있는지 표시한다.
3. 지지 근거와 반증을 함께 기록한다.
4. 방향이 바뀌면 이전 내용을 지우지 않고 decision log에 이유를 남긴다.
5. [05_TOPIC_LOCK_GATE.md](05_TOPIC_LOCK_GATE.md)를 통과할 때만 `LOCKED`로 바꾼다.

## 질문 최소화 원칙

- 코드·데이터·문헌으로 답할 수 있으면 사용자에게 묻지 않는다.
- 비용, 목표 학회, 산업 현장 접근권처럼 사용자만 정할 수 있는 항목만 `USER` 질문으로 둔다.
- 한 번에 사용자에게 묻는 질문은 가장 중요한 1개로 제한한다.
- 답이 없어도 안전하게 진행 가능한 항목은 가정을 명시하고 계속 검토한다.

## 다른 문서와의 경계

- 문헌 근거: [../research_search/README.md](../research_search/README.md)
- MME-Industry 실행 설계: [../../MME_INDUSTRY_RESEARCH_DESIGN.md](../../MME_INDUSTRY_RESEARCH_DESIGN.md)
- 확정된 프로젝트 결정: [../../DECISION_LOG.md](../../DECISION_LOG.md)
- 현재 실험 결과: [../../CURRENT_RESEARCH_STATUS_AND_NEXT_PLAN.md](../../CURRENT_RESEARCH_STATUS_AND_NEXT_PLAN.md)
