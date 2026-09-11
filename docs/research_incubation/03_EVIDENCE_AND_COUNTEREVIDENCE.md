# 근거 및 반증 장부

## 원칙

한 방향을 지지하는 결과만 모으지 않는다. 각 방향에 대해 `SUPPORT`, `COUNTER`, `UNCERTAIN`을 함께 기록하며, 확인하지 않은 기대를 결과처럼 쓰지 않는다.

## 현재 장부

| ID | 방향 | 종류 | 관찰 또는 주장 | 근거 | 강도 | 다음 확인 |
|---|---|---|---|---|---|---|
| E-001 | D1 | SUPPORT | Cheap-only early router가 SciVQA에서 품질 Gate를 통과했다 | [현재 상태](../../CURRENT_RESEARCH_STATUS_AND_NEXT_PLAN.md), [R4 인증](../R4_SCIVQA_EARLY_ROUTER_CERTIFICATION.md) | 프로젝트 실험 | split·측정 조건 재확인 |
| E-002 | D1 | COUNTER | Strong query skip 10.35%로 15% 비용 Gate에 미달했다 | [R4 인증](../R4_SCIVQA_EARLY_ROUTER_CERTIFICATION.md) | 프로젝트 실험 | 동일 test 재튜닝 금지 |
| E-003 | D2 | SUPPORT | MME-Industry는 산업군별 정답 라벨이 있는 image QA다 | [데이터셋 감사](../research_search/01_DATASET_AND_BENCHMARK_AUDIT.md) | 공식 카드 수준 | 로컬 파일 감사 |
| E-004 | D2 | COUNTER | MME-Industry는 PDF 매뉴얼 retrieval을 평가하지 않는다 | [데이터셋 감사](../research_search/01_DATASET_AND_BENCHMARK_AUDIT.md) | 명확한 과제 불일치 | 논문 claim 범위 제한 |
| E-005 | D3 | SUPPORT | 제조 안전·고장 절차·공정 규격 RAG는 실제 문제와 평가 사례가 있다 | [선행연구 지도](../research_search/02_INDUSTRIAL_RAG_PRIOR_WORK.md) | 초록 수준 | 핵심 원문 V2 검토 |
| E-006 | D3 | COUNTER | 제조업 RAG 적용 자체와 modality routing 자체는 이미 선행연구가 있다 | [노벨티 분석](../research_search/03_NOVELTY_GAP_AND_RESEARCH_DIRECTION.md) | 다수 공식 초록 | direct risk-routing 선행 탐색 |
| E-007 | D4 | UNCERTAIN | FactoryBench가 대규모 정답 데이터를 제공한다고 명시하지만 Hub viewer 오류가 관찰됐다 | [데이터셋 감사](../research_search/01_DATASET_AND_BENCHMARK_AUDIT.md) | 미검증 데이터 카드 | 파일 다운로드 후 무결성 검사 |

## 근거 강도

| 등급 | 의미 |
|---|---|
| 프로젝트 실험 | cache·config·split으로 재현 가능한 내부 결과 |
| 공식 전문 | 학회/저널 원문 방법과 표까지 확인 |
| 공식 초록/카드 | 존재와 큰 범위는 확인했지만 세부 조건 미확인 |
| 추론 | 확인된 근거를 바탕으로 한 프로젝트 해석 |
| 가설 | 아직 시험하지 않은 기대 |

## 새 근거 템플릿

```markdown
| E-??? | D? | SUPPORT/COUNTER/UNCERTAIN | 관찰 | 링크 | 강도 | 다음 확인 |
```
