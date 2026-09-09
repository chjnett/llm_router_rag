# R4 Cheap-only Early Router Policy Lock

## 판정

SciVQA test를 열기 전에 `Cheap-only early router`의 계수와 임계값을 잠갔다. 이 정책은 질문과 Caption 검색에서 이미 얻을 수 있는 7개 특징만 사용하며, ColSmol 점수는 의사결정 입력에 포함하지 않는다.

## 동결 계약

| 항목 | 값 |
|---|---:|
| 학습 | SPIQA 50 papers / 286 questions |
| 보정 | SPIQA 16 papers / 94 questions |
| 모델 | StandardScaler + Logistic Regression (`C=0.25`) |
| 임계값 | `0.3281827436` |
| 최소 R@1 retention | 95% |
| 최소 MRR retention | 95% |
| 최대 Strong route | 85% |

입력 특징은 candidate count의 로그, 질문 토큰 수, table 언급, visual 언급, Caption top score, margin, normalized entropy다. `p >= 0.3281827436`일 때만 ColSmol query encoding과 MaxSim을 실행한다.

## 잠금 전 결과

| Split | Caption R@1 | Always Strong R@1 | Selected R@1 | Selected MRR | Strong route | 실제 Strong 절감 |
|---|---:|---:|---:|---:|---:|---:|
| Train | 0.6329 | 0.6049 | 0.7483 | 0.8275 | 41.61% | 58.39% |
| Calibration | 0.5745 | 0.5532 | 0.7553 | 0.8389 | 38.30% | 61.70% |

Calibration AUC는 `0.8156`이다. 이 수치는 내부 보정 성능이며 외부 일반화의 증거로 사용하지 않는다.

## 다음 1회 평가 규칙

1. 이 파일과 policy artifact를 Git에 커밋·푸시한다.
2. 그 이후에만 SciVQA test manifest와 정답 연결을 생성한다.
3. test 결과를 보고 계수나 임계값을 변경하지 않는다.
4. Always Strong 대비 R@1/MRR retention 95% 이상, 실제 Strong query skip 15% 이상, peak VRAM 22GB 이하를 모두 보고한다.

정확한 계수·스케일러·입력 hash는 `artifacts/r4_spiqa_early_router_policy_lock.json`을 기준으로 한다.
