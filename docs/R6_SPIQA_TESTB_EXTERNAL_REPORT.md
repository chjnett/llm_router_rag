# R6 SPIQA test-B 외부 평가 보고서

## 최종 판정

**Retrieval readiness FAIL / Router cost near-miss FAIL.** 기존 SciVQA test를 재사용하지 않고, R5 정책을 Git commit `01ae2ab`에서 잠근 뒤 SPIQA test-B를 한 번 평가했다. 결과를 본 뒤 특징·계수·임계값·Gate를 변경하지 않았다.

## 평가 계약

| 항목 | 고정값 |
|---|---:|
| 논문 | 65 |
| 질의 | 228 |
| 전역 후보 이미지 | 794 |
| 관련 이미지 | 질의가 참조한 그림·표 중 하나 이상 |
| Strong 모델 | `vidore/colSmol-256M`, 원본 해상도 |
| 라우터 threshold | `0.2817383584` |
| 품질 유지 Gate | R@1·MRR 각각 95% 이상 |
| 비용 Gate | Strong query saving 15% 이상 |

평가 manifest는 결과 전에 commit `b18d841`로 고정했다. 공식 SPIQA 데이터 카드는 test-B가 65편·228질의이고 figure/table Caption과 원본 이미지를 제공한다고 명시한다.

## 검색 결과

| 방식 | R@1 | R@5 | MRR |
|---|---:|---:|---:|
| Caption BGE | **0.1686** | **0.3404** | **0.3268** |
| Always ColSmol | 0.1088 | 0.2575 | 0.2233 |
| Oracle 선택 | 0.2252 | 0.4505 | 0.4221 |

사전 retrieval readiness 기준 `R@5 >= 0.50`을 어떤 실제 baseline도 통과하지 못했다. 따라서 이 데이터에서 라우터 성능을 외부 인증으로 해석하지 않는다. test-B 질문은 여러 figure/table과 본문을 함께 요구하는 경우가 있어 단일 이미지 검색 모델과의 task mismatch가 크다.

## 잠긴 라우터 진단

| 항목 | Always Strong | 잠긴 선택 결과 | 판정 |
|---|---:|---:|---|
| R@1 | 0.1088 | **0.1490** | 품질 유지 PASS |
| MRR | 0.2233 | **0.2750** | 품질 유지 PASS |
| Strong route | 100% | 85.09% | — |
| Strong saving | 0% | **14.91%** | 15% 대비 0.09%p 부족 |

검색 준비 Gate가 선행 실패했고 비용도 근소하게 실패했으므로 certification 전체는 FAIL이다. threshold를 낮추거나 15% 기준을 완화하지 않는다.

## GPU·저장 비용

- 794개 원본 이미지 indexing: `180.55s`
- 228개 query 처리: `1.39s`
- Peak VRAM: `4.34GB`
- 압축 document index: `142.22MB`

## 다음 허용 작업

1. 동일 test-B에서 정책이나 threshold를 재튜닝하지 않는다.
2. task mismatch를 분리하기 위해 single-reference 질문만 **진단 표**로 계산할 수 있으나 인증값으로 사용하지 않는다.
3. 다음 인증 데이터는 Caption+image retrieval이 명시적 평가 과제인 독립 corpus로 선정한다.
4. 새 corpus가 없으면 외부 인증을 보류하고 현재 결과를 domain-shift failure로 보고한다.

결과 artifact: `artifacts/r6_spiqa_testb_router_diagnostic.json`
