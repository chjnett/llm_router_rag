# P1-V SPIQA Multimodal Retrieval Preflight Report

## Verdict

**Visual-signal feasibility PASS. 초기 50→100 selector는 FAIL했지만, 확대된 train/calibration/certification에서는 점 추정 Gate를 PASS했다. 통계적 인증은 아직 미완료다.**

SPIQA test-A의 224px 이미지와 메타데이터만 사용했다. 첫 50문항(12개 논문)은 개발용 사전실험, 이후 100문항(27개 논문)은 첫 표본의 논문을 완전히 제외한 확인 표본이다. 두 표본은 각각 table/figure 질문을 절반씩 고정했다.

## Frozen cohorts

| Cohort | Papers | Questions | Images | Purpose |
|---|---:|---:|---:|---|
| Preflight | 12 | 50 | 98 | 신호·정책 선택 |
| Paper-disjoint confirmation | 27 | 100 | 221 | 고정 정책 확인 |

## Retrieval results

### 50-question preflight

| Method | R@1 | R@5 | MRR | nDCG@5 |
|---|---:|---:|---:|---:|
| Caption BGE | 0.740 | 0.940 | 0.8169 | 0.8418 |
| CLIP visual | 0.440 | 0.820 | 0.6142 | 0.6485 |
| ColSmol-256M | 0.360 | 0.940 | 0.5727 | 0.6574 |
| Caption/CLIP oracle | 0.880 | 0.960 | 0.9154 | 0.9230 |
| Caption/ColSmol oracle | 0.920 | 0.980 | 0.9419 | 0.9490 |

### Input-resolution engineering screen

같은 동결 50문항과 ColSmol-256M을 유지하고 이미지만 224×224에서 원본 해상도로 교체했다. 이 결과는 모델 선택용 development evidence이며 certification 결과가 아니다.

| Input | ColSmol R@1 | R@5 | MRR | Table R@1 | Figure R@1 |
|---|---:|---:|---:|---:|---:|
| 224px | 0.360 | 0.940 | 0.5727 | 0.520 | 0.200 |
| Original resolution | **0.580** | 0.940 | **0.7209** | **0.800** | **0.360** |

R@1은 +22%p, MRR은 +0.1481 개선됐다. 원본 이미지의 중앙 크기는 502×252이고 최대 크기는 1097×1411이다. 표 검색 개선은 크지만 figure R@1 0.36은 아직 낮아 500M 모델 비교의 명시적 분석 축으로 남긴다.

### 500M model-size screen

동일 원본 이미지와 50문항에서 ColSmol-500M을 한 번 비교했다.

| Model | R@1 | R@5 | MRR | Table R@1 | Figure R@1 | Peak VRAM | Runtime storage |
|---|---:|---:|---:|---:|---:|---:|---:|
| ColSmol-256M | **0.580** | 0.940 | 0.7209 | **0.800** | 0.360 | **3.92 GiB** | **479 MiB** |
| ColSmol-500M | **0.580** | 0.940 | **0.7229** | 0.760 | **0.400** | 4.38 GiB | 954 MiB |

500M은 전체 R@1을 개선하지 않았고 MRR 차이는 +0.002다. 표 성능 하락과 저장공간 약 2배 증가를 감수할 근거가 없어 현재 조합에서는 거절한다. 256M+원본 해상도를 동결하고 외부 데이터로 이동한다.

### 100-question paper-disjoint confirmation

| Method | R@1 | R@5 | MRR | nDCG@5 |
|---|---:|---:|---:|---:|
| Caption BGE | 0.650 | 0.870 | 0.7557 | 0.7731 |
| CLIP visual | 0.410 | 0.800 | 0.5549 | 0.5959 |
| ColSmol-256M | 0.340 | 0.750 | 0.5147 | 0.5496 |
| Caption/CLIP oracle | 0.810 | 0.950 | 0.8626 | 0.8798 |
| Caption/ColSmol oracle | 0.770 | 0.950 | 0.8488 | 0.8693 |

Visual 모델을 항상 사용하는 것은 caption baseline보다 명확히 나쁘다. 반면 질문마다 더 나은 경로를 고르는 oracle은 독립 표본에서도 R@1을 12~16%p 높인다. 따라서 보완성은 재현됐지만, 그 선택을 정답을 보지 않고 할 수 있는지가 핵심 병목이다.

## Real selector test

50문항에서 Logistic Regression을 학습하고 임계값을 고정했다. 입력은 후보 이미지 수, 질문 길이와 table/figure 어휘, caption/ColSmol의 top score·margin·entropy 및 두 경로 차이뿐이다. 정답 reference, content type label, retrieval metric은 입력에 사용하지 않았다.

| Cohort | Caption R@1 | Selected R@1 | Caption MRR | Selected MRR | ColSmol route | AUC |
|---|---:|---:|---:|---:|---:|---:|
| Train 50 | 0.740 | 0.900 | 0.8169 | 0.9194 | 28% | 0.923 |
| Confirmation 100 | 0.650 | **0.620** | 0.7557 | **0.7285** | 36% | 0.747 |

확인 표본에서 R@1은 3%p, MRR은 0.0272 하락했다. Gate는 실패다. 훈련 표본 향상은 일반화 증거가 아니며 논문 성능으로 주장하지 않는다.

## Measured compute

| Model/run | Peak allocated VRAM | Indexing | Query |
|---|---:|---:|---:|
| CLIP, 50q/98 images | 0.76 GiB | 0.47 s | 0.50 s |
| CLIP, 100q/221 images | 0.75 GiB | 0.88 s | 1.30 s |
| ColSmol, 50q/98 images | 4.01 GiB | 35.16 s | 3.85 s |
| ColSmol original resolution, 50q/98 images | 3.92 GiB | 23.92 s | 4.01 s |
| ColSmol-500M original resolution, 50q/98 images | 4.38 GiB | 24.87 s | 3.98 s |
| ColSmol, 100q/221 images | 4.04 GiB | 79.14 s | 7.18 s |

ColSmol compressed document index는 50문항 표본 26.7MB, 확인 표본 60.2MB다.

## Anomalies and constraints

- OpenAI CLIP `.bin` 로드는 Torch 2.5.1 환경의 보안 제한으로 거부되어 safetensors LAION CLIP으로 교체했다. 제한을 우회하지 않았다.
- full ColPali는 약 5.85GB base weights와 현재 디스크 여유를 고려해 다운로드하지 않고 ColSmol-256M으로 대체했다.
- ColSmol은 Transformers 5.15 이상을 요구해 격리 환경 `.venv-colsmol`을 사용했다. main 환경은 변경하지 않았다.
- 최초 어댑터 로드는 base model 식별자 확인 단계에서 장시간 정지했다. adapter와 base snapshot을 오프라인 runtime으로 고정하고 `local_files_only`로 재실행했으며, 중복 Hugging Face cache는 오프라인 로드 검증 후 삭제했다.
- 최초 저장에서 bfloat16→NumPy 직렬화 오류가 발생했으며 float32 저장으로 수정했다. metric 계산은 바뀌지 않았다.

## Decision and next unlock condition

초기 실패 이후 남은 79개 논문 461문항을 train 286 / calibration 94 / certification 81로 논문 단위 분리했다. 아래 확대 실험은 앞의 50·100문항과도 논문이 겹치지 않는다.

## Expanded locked-policy result

| Split | Papers | Questions | Caption R@1 | Selected R@1 | Route rate |
|---|---:|---:|---:|---:|---:|
| Train | 50 | 286 | 0.6329 | 0.6958 | 19.23% |
| Calibration | 16 | 94 | 0.5745 | 0.6489 | 27.66% |
| Certification | 13 | 81 | 0.6790 | **0.7160** | **12.35%** |

정책은 train에서만 적합하고 calibration에서 threshold `0.392054`를 고정했다. Certification 전에 scaler, coefficients, intercept, threshold와 train/calibration result hash를 `policy_lock.json`에 기록했다.

Git에 보존되는 고정 정책과 인증 요약은 `artifacts/p1v_spiqa_selector_policy_lock.json`, `artifacts/p1v_spiqa_selector_certification.json`이다.

Certification에서 R@1은 +3.70%p, R@5는 +1.23%p, MRR은 +0.0266 개선됐다. 그러나 paired bootstrap 95% CI는 R@1 `[-1.23,+9.88]%p`, MRR `[-0.0103,+0.0704]`이며 McNemar exact p=`0.375`다. Selector-only correct 4건, caption-only correct 1건이다.

따라서 point-estimate Gate는 PASS하지만 통계적으로 우월하거나 비열등하다고 인증하지 않는다. SPIQA test-A 118개 논문을 모두 개발/확인/학습/보정/인증에 배정했으므로 같은 데이터의 추가 튜닝을 금지한다. 다음 해제 조건은 새로운 external dataset 또는 더 큰 독립 certification cohort다.

## Reproduction

```powershell
.venv\Scripts\python.exe -m caproute.cli.run_spiqa_clip_preflight --config configs\p1v_spiqa_clip_preflight.yaml
.venv\Scripts\python.exe -m caproute.cli.run_spiqa_clip_preflight --config configs\p1v_spiqa_clip_confirmation.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_spiqa_colsmol_preflight --config configs\p1v_spiqa_colsmol_preflight.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_spiqa_colsmol_preflight --config configs\p1v_spiqa_colsmol_preflight_fullres.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_spiqa_colsmol_preflight --config configs\p1v_spiqa_colsmol_500m_preflight_fullres.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_spiqa_colsmol_preflight --config configs\p1v_spiqa_colsmol_confirmation.yaml
.venv\Scripts\python.exe -m caproute.cli.evaluate_spiqa_selector --config configs\p1v_spiqa_colsmol_selector.yaml
.venv\Scripts\python.exe -m caproute.cli.freeze_spiqa_router_splits --config configs\p1v_spiqa_router_splits.yaml
.venv\Scripts\python.exe -m caproute.cli.freeze_spiqa_selector_policy --config configs\p1v_spiqa_colsmol_selector_lock.yaml
.venv\Scripts\python.exe -m caproute.cli.evaluate_spiqa_locked_selector --config configs\p1v_spiqa_colsmol_selector_certified.yaml
```
