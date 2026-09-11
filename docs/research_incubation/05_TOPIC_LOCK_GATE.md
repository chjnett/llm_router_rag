# 최종 연구 주제 잠금 Gate

## 현재 판정

**NOT READY — 어느 후보도 최종 주제로 잠그지 않음**

## FINER 평가표

각 항목을 1~5점으로 평가한다. 평균 3.0 이상이며 한 항목도 2점 미만이 아니어야 다음 Gate로 간다. 확인되지 않은 항목은 점수를 추정하지 않고 `?`로 둔다.

| 후보 | Feasible | Interesting | Novel | Ethical | Relevant | 상태 |
|---|---:|---:|---:|---:|---:|---|
| D1 Scientific PDF routing | ? | ? | ? | ? | ? | 비용 Gate 반증 반영 필요 |
| D2 산업 image QA routing | ? | ? | ? | ? | ? | preflight 전 |
| D3 산업 manual RAG routing | ? | ? | ? | ? | ? | 데이터 feasibility 전 |
| D4 telemetry reasoning routing | ? | ? | ? | ? | ? | 데이터 무결성 전 |
| D5 기술지원 evidence-aware RAG | ? | ? | ? | ? | ? | corpus coverage 감사 전 |
| D6 규제 문서 capability routing | ? | ? | ? | ? | ? | direct novelty 감사 전 |
| D7 기업 지식 path routing | ? | ? | ? | ? | ? | 데이터·라이선스 확인 전 |
| D8 CTI knowledge routing | ? | ? | ? | ? | ? | 직접 경쟁·dual-use 검토 전 |

## 필수 잠금 조건

| Gate | 통과 조건 | 현재 |
|---|---|---|
| G1 Problem | 구체적 사용자·실패 상황·기존 비용이 한 문단으로 설명됨 | 미통과 |
| G2 Data | 라이선스, split, gold label, 누수 검사가 가능함 | 미통과 |
| G3 Gap | 핵심 선행연구 전문 검토 후 직접 중복이 없음 | 미통과 |
| G4 Feasibility | RTX 3090에서 작은 preflight가 시간·VRAM 한도를 통과 | 미통과 |
| G5 Falsifiability | 성공·실패·중단 수치가 test 전에 잠김 | 미통과 |

## 잠금 절차

1. 한 후보가 FINER 기준과 G1–G5를 모두 통과한다.
2. Primary RQ 한 문장과 2~3개 sub-RQ를 작성한다.
3. in-scope, out-of-scope, 주요 가정을 고정한다.
4. Devil's Advocate 검토에서 Critical 문제가 없어야 한다.
5. `LOCKED_TOPIC.md`를 새로 만들고 이 문서 상태를 `LOCKED`로 변경한다.

## 잠금 해제 조건

잠금 뒤에도 데이터 누수, 재현 불가, 직접 선행연구 발견, 안전성 문제처럼 핵심 결론을 무효화하는 새 근거가 나오면 잠금을 해제한다. 사후 성능이 마음에 들지 않는다는 이유만으로 질문이나 임계값을 바꾸지 않는다.
