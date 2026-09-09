# R4 SciVQA Cheap-only Early Router 외부 인증

## 결론

잠긴 Cheap-only early router는 SciVQA test에서 **품질 Gate와 자원 Gate는 통과했지만 비용 Gate는 실패**했다. 따라서 전체 판정은 FAIL이다. Test 결과를 본 뒤 임계값을 바꾸지 않는다.

## 사전 고정 조건

- Policy commit: `195377d`
- Threshold: `0.3281827436`
- R@1/MRR retention: Always Strong의 95% 이상
- 실제 Strong query skip: 15% 이상
- Peak allocated VRAM: 22GB 이하
- Test manifest: 545 papers, 599 images, 3,594 answerable queries, SPIQA overlap 0

## 결과

| 방법 | R@1 | R@5 | MRR |
|---|---:|---:|---:|
| Caption | 0.2785 | 0.3962 | 0.3384 |
| Always Strong (ColSmol-256M) | 0.5431 | 0.6669 | 0.6045 |
| Locked Early Router | **0.5729** | **0.6898** | **0.6302** |
| Oracle | 0.6324 | 0.7585 | 0.6922 |

| Gate | 관측값 | 기준 | 판정 |
|---|---:|---:|---|
| R@1 retention | 105.48% | ≥95% | PASS |
| MRR retention | 104.26% | ≥95% | PASS |
| Strong query skip | 10.35% | ≥15% | **FAIL** |
| Peak VRAM | 4.04GiB | ≤22GB | PASS |

Always Strong 대비 R@1 차이는 +2.98%p이며 paired bootstrap 95% CI는 `[+2.39,+3.59]%p`다. MRR 차이는 +0.0258, 95% CI `[+0.0206,+0.0312]`다. Selected-only/Strong-only 정답은 116/9, McNemar exact `p=7.78e-25`다.

## 왜 비용 Gate가 실패했는가

SPIQA train의 candidate image 수는 1–29, calibration은 4–23이었지만 SciVQA test는 모든 질문에서 599였다. 표준화된 `candidate_log`의 평균 logit 기여가 test에서 `+0.8712`로 커져 Strong 호출 확률을 밀어 올렸다. Caption top/margin 분포 변화도 각각 평균 `+0.4836`, `+0.4390`을 더했다. 그 결과 calibration Strong route 38.30%가 test에서 89.65%로 증가했다.

이는 정책 구현 오류가 아니라 **corpus 규모와 Cheap score 분포의 domain shift에 대한 calibration 실패**다. Test에서 해당 특징을 제거하거나 threshold를 변경하면 누수가 되므로 하지 않는다.

## 기초 검색 Gate와 실행 이상

ColSmol R@5는 `0.6669`로 retrieval preflight 기준 `0.70`에 미달했다. 이 실패도 그대로 보존한다. 공식 Hugging Face CLI는 Brotli decode 오류로 JSON 다운로드를 중단했으며, 공식 `resolve/main` URL에 `Accept-Encoding: identity`를 사용해 동일 파일을 내려받았다. Manifest에 파일 SHA-256을 기록했다.

## 다음 허용 작업

1. SciVQA test는 더 이상 정책 선택에 사용하지 않는다.
2. 별도의 development corpus에서 corpus-size invariant 특징 또는 per-paper candidate formulation을 설계한다.
3. 비용을 임계값의 사후 제약이 아니라 학습 목적에 직접 포함한 cost-sensitive/coverage-regularized router를 비교한다.
4. 새로운 미개봉 dataset 또는 별도 paper-disjoint holdout을 확보한 뒤에만 다시 인증한다.
5. 현재 병목은 Strong retriever의 모델 크기보다 routing calibration이므로 즉시 더 큰 모델 sweep을 하지 않는다.

상세 로컬 결과는 `outputs/r4_scivqa_test_retrieval/results.json`과 `outputs/r4_scivqa_early_router_certification/results.json`, Git 추적 요약은 `artifacts/r4_scivqa_early_router_certification_summary.json`에 있다.
