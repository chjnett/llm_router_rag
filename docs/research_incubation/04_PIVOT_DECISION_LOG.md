# 피벗 및 결정 기록

## 상태 값

- `KEEP`: 방향 유지
- `REFINE`: 연구질문·데이터·평가 범위를 좁힘
- `PIVOT`: 해결하려는 문제나 핵심 데이터 변경
- `HOLD`: 선행 조건을 기다림
- `DROP`: 중단 조건 충족

## 현재 기록

| 날짜 | 대상 | 결정 | 계기 | 유지되는 자산 | 다음 Gate |
|---|---|---|---|---|---|
| 2026-09-12 | 전체 주제 | REFINE | architecture 중심 주장만으로는 선행연구 대비 약할 수 있음 | capability-aware routing 코드, 실측 비용, 인과적 early feature 원칙 | 도메인 문제와 gold 평가 결합 |
| 2026-09-12 | D2 MME-Industry | KEEP | 정답 라벨과 산업군이 있어 routing signal을 싸게 검증 가능 | Cheap/Strong/Abstain 설계 | 데이터 감사와 capability gap |
| 2026-09-12 | D3 산업 매뉴얼 RAG | HOLD | 실제 문제 적합성은 높지만 gold QA와 전문가 검증이 아직 없음 | 문서 routing 경험과 retrieval 평가 코드 | 공개 문서 feasibility |
| 2026-09-12 | 최종 주제 | HOLD | 후보 간 핵심 Gate가 아직 미측정 | 모든 후보 문서 | Topic Lock Gate |

## 피벗을 발생시키는 조건

| 조건 | 기본 결정 |
|---|---|
| Cheap–Strong 차이 <5%p | 모델 조합 또는 데이터 변경 |
| Oracle도 실측 비용 20% 절감 불가 | 해당 라우팅 방향 DROP |
| 기존 연구가 동일 claim·평가를 이미 수행 | claim REFINE 또는 domain PIVOT |
| gold label을 재현 가능하게 확보 불가 | 데이터 후보 HOLD/DROP |
| 평균은 좋아도 heldout domain 대부분에서 방향 불일치 | 일반화 주장 제거 |

## 기록 규칙

결정을 바꿀 때 이전 행을 수정하지 않는다. 새 행에 날짜, 새 결정, 바뀐 근거를 추가한다. 코드나 장시간 실험으로 이어지는 결정은 관련 plan 문서와 commit hash를 연결한다.

## 새 결정 템플릿

```markdown
| YYYY-MM-DD | D? | KEEP/REFINE/PIVOT/HOLD/DROP | 새 근거 | 재사용 자산 | 다음 Gate |
```
