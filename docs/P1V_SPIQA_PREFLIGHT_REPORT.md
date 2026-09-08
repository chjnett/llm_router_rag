# P1-V SPIQA Multimodal Retrieval Preflight Report

## Verdict

**Visual-signal feasibility PASS, deployable selector FAIL.** GPU 확대와 P2 승격은 보류한다.

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
| ColSmol, 100q/221 images | 4.04 GiB | 79.14 s | 7.18 s |

ColSmol compressed document index는 50문항 표본 26.7MB, 확인 표본 60.2MB다.

## Anomalies and constraints

- OpenAI CLIP `.bin` 로드는 Torch 2.5.1 환경의 보안 제한으로 거부되어 safetensors LAION CLIP으로 교체했다. 제한을 우회하지 않았다.
- full ColPali는 약 5.85GB base weights와 현재 디스크 여유를 고려해 다운로드하지 않고 ColSmol-256M으로 대체했다.
- ColSmol은 Transformers 5.15 이상을 요구해 격리 환경 `.venv-colsmol`을 사용했다. main 환경은 변경하지 않았다.
- 어댑터가 base model 식별자를 확인하므로 현재 실행에는 Hugging Face 메타데이터 접근이 필요하다. 가중치는 로컬 cache를 사용한다.
- 최초 저장에서 bfloat16→NumPy 직렬화 오류가 발생했으며 float32 저장으로 수정했다. metric 계산은 바뀌지 않았다.

## Decision and next unlock condition

현재 결과만으로 추가 GPU sweep이나 P2 전체 구현을 진행하지 않는다. 다음 GPU 실험은 최소 300개 이상의 **별도 학습/보정 질문**과 논문 단위 독립 certification cohort를 확보한 뒤 허용한다. 우선순위는 (1) 더 큰 학습 cohort, (2) caption 실패를 예측하는 cheap confidence 설계, (3) 고정 threshold certification이다. 동일 test-A 확인 표본으로 재튜닝하지 않는다.

## Reproduction

```powershell
.venv\Scripts\python.exe -m caproute.cli.run_spiqa_clip_preflight --config configs\p1v_spiqa_clip_preflight.yaml
.venv\Scripts\python.exe -m caproute.cli.run_spiqa_clip_preflight --config configs\p1v_spiqa_clip_confirmation.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_spiqa_colsmol_preflight --config configs\p1v_spiqa_colsmol_preflight.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_spiqa_colsmol_preflight --config configs\p1v_spiqa_colsmol_confirmation.yaml
.venv\Scripts\python.exe -m caproute.cli.evaluate_spiqa_selector --config configs\p1v_spiqa_colsmol_selector.yaml
```
