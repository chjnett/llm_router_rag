# 미해결 질문 백로그

## 분류

- `SEARCH`: 문헌·데이터셋 조사로 먼저 답한다.
- `EXPERIMENT`: 작은 CPU/GPU 실험으로 답한다.
- `USER`: 연구자의 목표·접근권·감수 가능한 비용처럼 외부 증거로 대신할 수 없다.
- `BLOCKED`: 필요한 데이터나 권한이 없어 현재 답할 수 없다.

## 열린 질문

| ID | 유형 | 질문 | 가장 싼 답변 방법 | 어떤 결정을 여는가 | 상태 |
|---|---|---|---|---|---|
| Q-001 | EXPERIMENT | MME-Industry에서 Cheap와 Strong의 정확도 차이가 실제로 존재하는가? | 각 모델 고정 prompt 소규모 paired run | D2 지속 여부 | OPEN |
| Q-002 | EXPERIMENT | Strong 결과 없이도 unseen industry에서 Strong 필요성을 예측할 수 있는가? | domain-heldout logistic/threshold baseline | 핵심 routing feasibility | WAIT-Q001 |
| Q-003 | SEARCH | 산업 매뉴얼 RAG에서 risk-calibrated early routing을 직접 평가한 선행연구가 있는가? | 검색식 확장 후 핵심 논문 전문 확인 | D3 novelty | OPEN |
| Q-004 | SEARCH | 공개 영문 제조 매뉴얼로 근거 페이지가 있는 QA를 합법적으로 구축할 수 있는가? | 라이선스·문서 구조·정답 가능성 감사 | D3 data feasibility | OPEN |
| Q-005 | EXPERIMENT | FactoryBench 파일과 split이 카드 설명대로 재현 가능한가? | checksum, row count, duplicate audit | D4 유지 여부 | HOLD |

## 사용자에게만 물어야 하는 질문

현재 즉시 답이 필요한 `USER` 질문은 없다. 아래 조건이 실제 선택을 막을 때만 한 번에 하나씩 묻는다.

| ID | 질문 | 묻는 시점 |
|---|---|---|
| U-001 | 실제 제조업 전문가 또는 현장 문서에 접근할 수 있는가? | D3 공개 데이터 preflight가 통과한 뒤 |
| U-002 | 목표를 단기 국내 학회와 장기 확장 중 어디에 둘 것인가? | D2와 D3 모두 실행 가능할 때 |

## 질문 종료 조건

| 결과 | 처리 |
|---|---|
| 충분한 증거 확보 | `ANSWERED`로 바꾸고 근거 문서 링크 추가 |
| 답이 후보를 무효화 | `ANSWERED-NEGATIVE`로 바꾸고 pivot log 기록 |
| 표본 부족 | 실패로 단정하지 않고 `INCONCLUSIVE` |
| 더 싼 질문으로 분해 가능 | 기존 질문을 닫지 말고 하위 질문 ID 추가 |

## 새 질문 템플릿

```markdown
| Q-??? | SEARCH/EXPERIMENT/USER | 질문 | 가장 싼 답변 방법 | 결정 | OPEN |
```
