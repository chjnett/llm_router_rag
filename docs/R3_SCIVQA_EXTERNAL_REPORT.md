# R3 SciVQA External Validation Report

## Verdict

**Retrieval complementarity PASS, frozen quality fusion PASS, compute-aware routing FAIL.**

SciVQA에서 ColSmol은 Caption BGE보다 크게 강했고, SPIQA에서 잠근 selector는 두 결과를 선택해 Always ColSmol보다도 유의하게 높은 검색 품질을 냈다. 그러나 현재 selector가 ColSmol score·margin·entropy를 입력으로 사용하므로 선택 전에 Strong 계산이 이미 필요하다. 선택률을 비용 절감률로 해석할 수 없다.

## Frozen external contract

| Item | Value |
|---|---:|
| Dataset | `katebor/SciVQA` validation |
| License | MIT |
| Papers | 235 |
| Candidate figures | 240 |
| Answerable queries | 1,440 |
| Excluded unanswerable queries | 240 |
| SPIQA paper overlap | 0 |

Manifest는 GPU 결과 전에 `artifacts/r3_scivqa_external_manifest.json`으로 고정했다. JSON SHA-256은 `e34f0f...f4cfba`, image ZIP SHA-256은 `0099bd...00669`다.

## Retrieval result

| Method | R@1 | R@5 | MRR | Interpretation |
|---|---:|---:|---:|---|
| Caption BGE | 0.3653 | 0.4986 | 0.4336 | Cheap text baseline |
| ColSmol-256M, original resolution | 0.6479 | 0.7701 | 0.7070 | Strong visual baseline |
| Oracle selector | 0.7396 | 0.8451 | 0.7908 | Label-aware upper bound |
| Frozen 13-feature selector | **0.6965** | **0.7938** | **0.7447** | Post-retrieval quality fusion |

Visual 질문의 Caption/ColSmol R@1은 0.2472/0.6375, non-visual 질문은 0.4833/0.6583이다. 외부 도메인에서는 Strong이 기본 경로에 가깝지만 Caption이 Strong 실패 일부를 보완해 Oracle R@1이 추가로 +9.17%p 높다.

## Frozen-selector uncertainty

| Comparison against Always ColSmol | Estimate | Paired bootstrap 95% CI |
|---|---:|---:|
| R@1 difference | +0.0486 | [+0.0347, +0.0625] |
| MRR difference | +0.0376 | [+0.0258, +0.0501] |

Selected-only correct는 88건, Strong-only correct는 18건이며 McNemar exact p=`2.97e-12`다. 품질 개선은 통계적으로 명확하다.

## Compute result and architectural failure

| Item | Value |
|---|---:|
| 240-image indexing | 62.07 s |
| 1,440 combined query evaluation | 5.57 s |
| Peak allocated VRAM | 3.87 GiB |
| Compressed caption+visual index | 47.29 MiB |
| Strong result selection rate | 80.63% |
| Realized Strong compute saving | **0%** |

현재 13개 특징 중 `strong_top`, `strong_margin`, `strong_entropy`와 세 difference 특징은 ColSmol 질의 점수를 계산해야 얻을 수 있다. 따라서 Caption을 최종 선택한 19.38%에서도 ColSmol은 이미 실행됐다. 이 결과는 quality fusion의 일반화 증거이지 compute-aware selective routing의 완성 증거가 아니다.

## Required architecture correction

1. **Early Cheap-only pre-router:** 질문 길이·visual/table 어휘·후보 수·Caption top/margin/entropy만 사용한다.
2. Early router가 Strong 필요로 판단한 경우에만 ColSmol query encoding과 MaxSim을 실행한다.
3. Strong 실행 후에는 현재 13-feature selector를 optional late fusion으로 사용할 수 있지만, 이 단계는 비용 절감 주장을 하지 않는다.
4. SciVQA validation은 이제 architecture-development evidence로 취급한다.
5. Cheap-only 정책과 threshold를 SPIQA train/calibration에서 고정한 뒤, 아직 열지 않은 SciVQA test에서 한 번만 인증한다.

최종 Gate는 R@1·MRR Always Strong 대비 95% 이상 유지, 실제 Strong query compute 15% 이상 절감, peak VRAM 22GB 이하이다.

## Reproduction

```powershell
.venv\Scripts\python.exe -m caproute.cli.freeze_scivqa_external_manifest --config configs\r3_scivqa_external_manifest.yaml
.venv-colsmol\Scripts\python.exe -m caproute.cli.run_scivqa_external_retrieval --config configs\r3_scivqa_external_retrieval.yaml
.venv\Scripts\python.exe -m caproute.cli.evaluate_scivqa_locked_selector --config configs\r3_scivqa_locked_selector.yaml
```

두 번째 명령은 결과가 생성되며 retrieval Gate가 통과한다. 세 번째 명령은 quality Gate는 통과하지만 compute Gate가 실패하므로 의도적으로 non-zero exit를 반환한다.
