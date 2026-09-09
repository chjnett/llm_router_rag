# R5 SciVQA Corpus-size Invariant Router Screen

## 판정

**개발 신호 PASS / 정책 잠금 완료.** SciVQA validation을 논문 단위로 train 164편·1,002질의와 calibration 71편·438질의로 나눴으며 논문 중복은 0이다. 이미 개봉한 개발 자료이므로 이 결과를 외부 인증 성능으로 주장하지 않는다.

## 무엇을 바꿨는가

기존 라우터의 `candidate_log`를 제거했다. 새 7개 특징은 질문 토큰 수의 로그, 토큰 다양도, 표·시각 표현, Caption top score·margin·normalized entropy다. 후보 이미지 수와 ColSmol 파생 특징을 사용하지 않으므로 corpus 크기 변화와 Strong 선실행에 직접 의존하지 않는다.

Logistic Regression의 `C={0.10,0.25,1.00}`과 positive class weight `{1,2,4}`를 비교했다. MRR 차이가 `1e-4` 이내면 더 높은 Strong 절감과 더 단순한 모델을 선택하도록 코드화했다.

## 개발 결과

| 항목 | Always Strong | 선택 결과 | 차이 |
|---|---:|---:|---:|
| R@1 | 0.6370 | **0.7078** | +0.0708 |
| R@5 | 0.7717 | **0.8174** | +0.0457 |
| MRR | 0.7028 | **0.7603** | +0.0575 |
| Strong route | 1.0000 | **0.7854** | -0.2146 |

선택 후보는 `C=0.10`, class weight `1.0`, threshold `0.281738`이다. Calibration AUC는 `0.7869`다. 가중치 2·4는 성능을 실질적으로 개선하지 않아 cost-sensitive weighting 자체는 채택 근거가 없다.

## 보수적 해석

이번 결과는 후보 수 특징 제거가 기존 SciVQA test의 corpus-size shift 실패를 수리할 가능성을 보여준다. 그러나 같은 validation에서 모델과 threshold를 선택했으므로 낙관 편향이 있다. **기존 SciVQA test에 다시 적용하지 않으며**, 새 미개봉 외부 holdout을 확보한 뒤 정책을 먼저 잠그고 한 번만 인증한다.

재현 명령:

```powershell
.\.venv\Scripts\python.exe -m caproute.cli.screen_scivqa_invariant_router
```

원시 결과: `artifacts/r5_scivqa_invariant_router_screen.json`

동결 정책: `artifacts/r5_scivqa_invariant_router_policy_lock.json`  
SHA-256: `cf8cf46b7e876ddf8f6b48baba16469dd792f3f9645881233927142388fc3f11`
