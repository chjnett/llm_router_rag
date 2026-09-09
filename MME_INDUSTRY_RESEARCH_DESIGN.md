# MME-Industry 기반 산업 멀티모달 Capability Routing 연구 설계

## Material Passport

- Origin Skill: academic-research-suite
- Origin Mode: research scoping + experiment planning
- Origin Date: 2026-09-09
- Verification Status: DESIGN DRAFT — 실험 미실행
- Version Label: mme_industry_design_v1
- Target Hardware: NVIDIA RTX 3090 24GB 1장

## 0. 한 줄 결론

MME-Industry를 최종 산업 매뉴얼 RAG 벤치마크로 오해하지 않고, **보지 않은 산업 도메인에서 작은 VLM의 답을 수락할지, 큰 VLM으로 보낼지, 답변을 보류할지를 결정하는 저비용 산업 멀티모달 라우팅 preflight**로 사용한다.

## 1. 연구 포지셔닝

### 제안 명칭

**CapRoute-Industry: Risk-Calibrated Capability Routing for Cross-Industry Multimodal Question Answering**

### 해결하려는 문제

산업 이미지 질문마다 필요한 시각 이해 능력은 동일하지 않다. 모든 질문을 큰 VLM으로 처리하면 계산량이 크고, 모든 질문을 작은 VLM으로 처리하면 산업별·질문별 실패가 증가한다. 본 연구는 Strong 모델의 출력을 미리 사용하지 않고도 다음 행동을 선택할 수 있는지 검증한다.

1. Cheap VLM 답변 수락
2. Strong VLM 호출
3. 근거가 불충분하면 답변 보류(abstention)

### 기존 CapRoute와의 연결

| 기존 Scientific PDF CapRoute | CapRoute-Industry |
|---|---|
| Caption/text Cheap retrieval | Cheap VLM의 산업 이미지 답변 |
| ColSmol Strong retrieval | Strong VLM의 산업 이미지 답변 |
| Caption top score/margin/entropy | Cheap VLM의 A–E 선택 확률/margin/entropy |
| Strong query skip | Strong VLM 호출 생략 |
| Unsafe Cheap acceptance | Cheap 오답을 그대로 수락 |
| Query/page domain shift | 보지 않은 산업군으로의 domain shift |

과학 PDF 결과는 산업 QA 성공의 증거로 재사용하지 않는다. Strong-derived 특징을 쓰면 계산 절감이 0이 된다는 인과성 교훈과, corpus/domain shift에서 feature가 무너질 수 있다는 실패 교훈만 설계 근거로 사용한다.

## 2. 데이터셋의 정확한 역할

### MME-Industry

- 21개 산업 분야
- 산업별 약 50문항, 전체 약 1,050문항
- 고해상도 산업 이미지 + 객관식 질문 + A–E 선택지 + 정답
- 영어/중국어 병렬 제공
- 비 OCR 중심 시각·산업 지식 질문
- Apache-2.0
- 공식 배포는 단일 평가 split이므로 공식 leaderboard train/test처럼 취급하지 않는다.

### 중요한 해석

MME-Industry는 PDF 매뉴얼 검색 데이터가 아니다. 따라서 이 단계에서 주장할 수 있는 것은 **산업 이미지 QA 계산 라우팅**이며, 산업 매뉴얼 RAG·고장 절차 검색·실제 현장 안전성은 후속 연구 범위다.

### `E` 선택지 주의

데이터셋의 `E`는 “그림에 해당 특징이 없음”이라는 gold answer 후보다. 시스템의 abstention과 다르다.

- Dataset answer `E`: 채점 가능한 다섯 번째 정답 선택지
- System abstention: A–E 어느 답도 신뢰할 수 없어 결과를 사용자에게 내보내지 않는 정책 행동

두 항목을 같은 값으로 저장하거나 평가하지 않는다.

## 3. 연구 질문과 가설

### Primary RQ

> Strong 모델의 출력을 사전에 사용하지 않는 risk-calibrated router가 보지 않은 산업 도메인에서 Always Strong 대비 QA 품질을 유지하면서 실제 GPU 시간을 줄일 수 있는가?

### Sub-RQ

1. MME-Industry에는 Cheap으로 충분한 문항과 Strong이 필요한 문항이 함께 존재하는가?
2. Cheap 모델의 강제 선택 확률과 입력 메타데이터만으로 Strong 필요성을 예측할 수 있는가?
3. 산업 도메인을 분리해도 고정된 정책의 quality–cost–risk trade-off가 유지되는가?
4. 답변 보류 정책이 Cheap 오답 수락 위험을 낮추는가?

### Confirmatory Hypotheses

| ID | 가설 | 사전 판정 기준 |
|---|---|---|
| H1 | Cheap/Strong 간 문항별 보완성이 존재한다. | Cheap-only correct와 Strong-only correct가 각각 5% 이상 |
| H2 | Router가 Always Strong 품질을 유지한다. | Accuracy retention ≥ 97% |
| H3 | Router가 실제 계산을 절감한다. | GPU-seconds/query saving ≥ 20% |
| H4 | Cheap 오답 수락 위험을 통제한다. | 관측 위험과 95% exact upper bound를 함께 보고; 5% upper-bound는 별도 strict Gate |

H2와 H3가 동시에 통과해야 main result로 인정한다. H1이 실패하면 모델 pair를 한 번만 교체할 수 있고, 교체 후에도 실패하면 해당 연구 경로를 중단한다.

## 4. FINER 평가

| 기준 | 판정 | 근거 |
|---|---|---|
| Feasible | 충족 | 447MB 규모, 객관식 자동 채점, RTX 3090에서 2B–7B급 로컬 VLM 비교 가능 |
| Interesting | 충족 | 산업 QA의 품질·비용·위험을 동시에 다룸 |
| Novel | 부분 충족 | 단순 small/large routing은 약함; unseen-industry·causal early routing·risk abstention 결합이 필요 |
| Ethical | 충족(제한 포함) | 공개 데이터 기반이나 실제 설비 제어에 사용하지 않는다는 제한 필요 |
| Relevant | 충족 | 이후 산업 매뉴얼·정비 지원 RAG로 확장 가능 |

## 5. 연구 범위

### 포함

- MME-Industry English QA
- 정적 산업 이미지
- 객관식 A–E 답변
- 로컬 Cheap/Strong VLM
- 사전 라우팅, calibration, abstention
- 산업 도메인 단위 일반화
- RTX 3090 wall-clock/GPU/VRAM 측정

### 제외

- 실제 설비 제어
- 정비 행동 자동 실행
- 센서 시계열 진단
- PDF 매뉴얼 retrieval
- 자유형 정비 절차 생성
- 중국어 성능을 main claim으로 사용
- 사람 대상 사용자 연구

## 6. 모델 및 추론 프로토콜

### 모델 역할

| 역할 | 1차 후보 | 선택 원칙 |
|---|---|---|
| Cheap VLM | 2B–3B급 instruction VLM | RTX 3090에서 빠르고 선택지 log-likelihood 추출 가능 |
| Strong VLM | 동일 계열 7B급 instruction VLM | tokenizer/prompt 차이를 줄이고 24GB 내 실행 가능 |
| Router | Logistic Regression | 작은 데이터에서 해석 가능하고 과적합 위험이 낮음 |
| Calibration | Temperature scaling 또는 isotonic 중 validation Brier가 낮은 하나 | calibration에서만 선택 |

모델 ID, revision, weight hash, quantization, dtype, transformers/torch/CUDA 버전을 첫 실행 전에 고정한다. 모델 family 비교는 main experiment가 아니라 사전 model-pair screening으로 1회만 허용한다.

### 답변 점수 계산

자유 생성 후 문자열 파싱을 primary confidence로 사용하지 않는다. 동일 prompt에서 A, B, C, D, E answer token의 conditional log-likelihood를 계산한다.

\[
p_j = \frac{\exp(\ell_j/T)}{\sum_{k\in\{A,B,C,D,E\}}\exp(\ell_k/T)}
\]

- 예측: `argmax_j p_j`
- top probability: `max(p)`
- margin: 가장 큰 확률 − 두 번째 확률
- entropy: `-sum(p log p)`
- calibration temperature `T`: calibration split에서만 결정

한 글자가 여러 tokenizer token으로 분리되면 option string 전체의 길이 정규화 log-likelihood를 사용한다. 모든 문항에 동일 채점 함수를 적용한다.

## 7. 데이터 감사와 분할

### P0-A 데이터 감사

1. 공식 annotations와 이미지 파일 수 대조
2. 영어/중국어 sample ID 및 gold answer 일치율 확인
3. exact/perceptual image hash로 중복 확인
4. 도메인별 정답 A–E 분포와 해상도 분포 확인
5. 유사 이미지가 여러 도메인에 있으면 동일 group으로 묶음

### 고정 도메인 분할

단일 random item split을 금지한다. 산업 도메인을 group으로 사용한다.

| Split | 도메인 수 | 예상 문항 | 용도 |
|---|---:|---:|---|
| Development | 12 | 약 600 | feature/모델 구조 개발 |
| Calibration | 4 | 약 200 | threshold·temperature 선택 |
| Certification | 5 | 약 250 | 잠긴 정책 1회 평가 |

분할은 seed를 고정한 뒤 도메인 이름과 sample ID hash를 manifest로 저장한다. 정답 분포 균형은 분할 전에 계산할 수 있으나 모델 결과를 본 뒤 도메인을 이동하지 않는다.

### 보조 반복 평가

한 번의 5-domain certification 결과가 특정 산업 구성에 좌우되는 정도를 확인하기 위해 development 단계에서만 domain-grouped cross-validation을 수행한다. Certification 5개 도메인은 어떤 fold의 tuning에도 포함하지 않는다.

## 8. Capability label 정의

각 문항의 Cheap/Strong 정오답으로 oracle state를 만든다.

| Oracle state | Cheap | Strong | 이상적 행동 |
|---|---:|---:|---|
| Both-correct | 1 | 1 | Cheap 수락 |
| Cheap-only | 1 | 0 | Cheap 수락 |
| Strong-needed | 0 | 1 | Strong 호출 |
| Both-fail | 0 | 0 | Abstain 후보 |

Primary router target은 `Strong-needed`이다. 그러나 Both-fail을 단순 negative로 넣으면 잘못된 Cheap 수락을 학습할 수 있으므로 다음 2단 정책을 쓴다.

1. Early routing head: `P(Strong-needed | Cheap-only signals)`
2. Acceptance head: 현재 선택된 답이 맞을 확률을 보정해 threshold 아래면 abstain

## 9. Router 입력 특징

### 허용 특징: Strong 실행 전 계산 가능

| 그룹 | 특징 |
|---|---|
| Cheap confidence | top probability, margin, entropy, `p(E)` |
| Stability | deterministic 답과 2회 stochastic 답의 일치율 |
| Question | token length, 숫자/단위 포함, 색·형상·결함·공정 용어 flag |
| Image metadata | width, height, aspect ratio, grayscale/color 통계 |
| Cheap perception | OCR text length, OCR confidence, 객체/텍스트 밀도 proxy |
| Domain | 21개 산업 category 또는 unseen-safe `unknown` encoding |

### 금지 특징

- Strong answer
- Strong logits/confidence
- Strong embedding
- Strong latency
- gold answer
- certification domain의 결과로 만든 통계

Domain feature 사용 여부는 ablation으로 분리한다. unseen-domain main model은 알려진 category embedding에 과도하게 의존하지 않도록 `domain-free` 버전을 primary로 둔다.

## 10. 정책 결정 규칙

Early router가 출력한 Strong 필요 확률을 `r_i`, Cheap answer correctness의 calibrated probability를 `q_i`라고 한다.

\[
\pi(x_i)=
\begin{cases}
\text{Accept Cheap}, & r_i < \tau_r \land q_i \ge \tau_a \\
\text{Run Strong}, & r_i \ge \tau_r \\
\text{Abstain}, & r_i < \tau_r \land q_i < \tau_a
\end{cases}
\]

Strong 실행 후 Strong confidence가 별도 acceptance threshold보다 낮으면 abstain한다. Strong 결과를 이미 계산한 뒤 Cheap/Strong 중 더 신뢰되는 답을 고르는 late fusion은 보조 실험이며, 계산 절감으로 계산하지 않는다.

## 11. 비용 정의

Lower-first 구조이므로 routed cost는 Cheap 비용을 항상 포함한다.

\[
C_i^{route}=C_{L,i}+I_i^{U}C_{U,i}
\]

\[
Saving_{GPU}=1-\frac{\sum_i C_i^{route}}{\sum_i C_{U,i}}
\]

`Strong call saving = 1 - Strong call rate`와 `GPU saving`을 구분한다. Cheap 실행 비용 때문에 호출 생략률이 높아도 실제 GPU saving이 음수가 될 수 있다.

### 측정 규칙

- CUDA synchronize 전후 wall-clock
- 최초 model load와 warm inference를 분리 보고
- warm-up 10문항 후 본 측정
- 동일 문항 순서와 batch size 고정
- peak allocated/reserved VRAM 모두 기록
- 모든 모델 출력·logits·latency를 sample ID별 cache
- 한 번 생성된 certification output을 재생성하지 않음

## 12. 비교 기준선

| ID | Baseline |
|---|---|
| B1 | Always Cheap |
| B2 | Always Strong |
| B3 | Random router with matched Strong-call budget |
| B4 | Cheap max-probability threshold |
| B5 | Proposed causal risk-calibrated router |

Oracle은 학습 가능한 baseline이 아니라 feasibility upper bound로 별도 표기한다.

## 13. 평가 지표

### QA

- Overall Accuracy
- Macro-domain Accuracy
- 도메인별 Accuracy
- `E` 정답 subset Accuracy

### Routing

- Strong-needed AUROC/AUPRC
- Brier Score/ECE
- Strong call rate
- Cheap acceptance coverage
- Risk–Coverage Curve/AURC

### Safety

- Unsafe Cheap Acceptance: Cheap을 채택했으나 오답인 비율
- Selective risk: non-abstained answer 중 오답 비율
- Abstention rate
- Clopper–Pearson 95% upper bound

### System

- p50/p95 latency
- GPU-seconds/query
- Peak VRAM
- 출력 token 수
- cache size

## 14. 통계 분석

1. Proposed vs Always Strong 정확도: paired bootstrap 95% CI
2. 불일치 정오답: exact McNemar test
3. 비용: 문항별 paired bootstrap CI
4. 도메인별 결과: macro average와 범위, aggregate만 보고하지 않음
5. calibration: reliability diagram, ECE, Brier

효과 크기와 CI를 primary로 사용하며 p-value 단독으로 성공을 선언하지 않는다.

### Strict 5% risk 인증의 표본 주의

Clopper–Pearson upper bound는 Cheap을 수락한 문항 수를 분모로 한다. Certification에서 Cheap acceptance가 너무 적으면 관측 오류가 0이어도 5% upper bound를 통과하기 어렵다. 따라서 다음을 구분한다.

- 운영 결과: 관측 unsafe risk와 CI를 그대로 보고
- Strict certification: Cheap accepted sample이 충분할 때만 PASS/FAIL 판정
- 표본 부족: `INCONCLUSIVE`, 기준 완화 금지

## 15. 단계별 Gate와 중단 규칙

### P0 — Dataset integrity

PASS 조건:

- 1,050개 수준의 이미지/영문 QA가 정상 로딩
- 누락/중복/정답 불일치가 manifest에 기록
- domain-group split overlap 0

### P1 — Model-pair feasibility

PASS 조건:

- Strong accuracy > Cheap accuracy
- Cheap-only correct ≥ 5%
- Strong-only correct ≥ 5%
- Oracle이 Always Strong보다 높음

FAIL 시 허용: 모델 pair 1회 교체. 두 번째 실패 시 종료.

### P2 — Oracle cost feasibility

PASS 조건:

- 실제 Lower-first Oracle GPU saving ≥ 20%
- Both-fail rate가 결과 해석을 무력화하지 않음

FAIL 시 Router를 학습하지 않는다.

### P3 — Development routing

PASS 조건:

- Strong-needed AUROC ≥ 0.65
- calibration quality 개선
- grouped-CV에서 대다수 fold가 같은 개선 방향

### P4 — Policy lock

- feature list 고정
- coefficients/model hash 고정
- `tau_r`, `tau_a` 고정
- data/model/code Git commit 고정
- certification command 고정

### P5 — One-shot certification

Main PASS 조건:

- Accuracy retention ≥ 97%
- GPU saving ≥ 20%
- Peak VRAM ≤ 22GB
- 동일 방향이 최소 4/5 certification domain에서 유지

Strict safety Gate는 95% upper risk ≤ 5%일 때만 별도로 PASS한다. Main Gate가 실패하면 certification에서 재튜닝하지 않는다.

## 16. Ablation

| Ablation | 검증 목적 |
|---|---|
| Question-only | 언어적 난이도만으로 충분한가 |
| Cheap confidence-only | 가장 단순한 deployable router 성능 |
| + image metadata/OCR | 값싼 시각 복잡도 신호의 추가 효과 |
| + domain category | 산업 라벨 의존성과 unseen-domain 취약성 |
| without abstention | 안전 정책의 위험 감소 효과 |

## 17. 예상 결과 해석표

| 결과 | 해석 | 다음 행동 |
|---|---|---|
| Quality PASS + Cost PASS | main claim 가능 | 산업 매뉴얼 RAG 외부 확장 |
| Quality PASS + Cost FAIL | router는 분류기일 뿐 비용 연구 실패 | Cheap 모델/one-forward 구조 재검토 |
| Quality FAIL + Cost PASS | 과도한 Cheap 수락 | threshold 재튜닝은 development에서만 |
| Oracle FAIL | 모델 pair에 routing 여지 없음 | 즉시 종료 |
| Certification domain 편차 큼 | cross-industry 일반화 실패 | domain-specific calibration 논문으로 축소 |

## 18. Novelty 주장 범위

### 주장 가능한 기여

1. Strong-derived signal 없이 실제 계산을 줄이는 causal early VLM routing
2. 무작위 문항 분할이 아닌 unseen-industry 평가
3. accuracy–GPU cost–selective risk를 함께 고정한 산업 QA 평가
4. dataset answer `E`와 system abstention을 분리한 위험 보정
5. 성공뿐 아니라 Oracle/외부 domain 실패를 보존하는 gate-driven protocol

### 주장하면 안 되는 것

- 최초의 LLM/VLM router
- 산업 매뉴얼 RAG 해결
- 실제 제조 안전 보장
- 산업 전반에 일반화
- MME-Industry accuracy SOTA

### 보수적 출판성

- KSC/KCC: P5 main Gate 통과 시 충분한 실험 논문 후보
- 산업 AI/멀티모달 워크숍: domain generalization과 risk 결과가 명확하면 후보
- 상위 국제학회: MME-Industry 단독으로 부족; 실제 매뉴얼 retrieval 또는 새로운 산업 capability benchmark 필요

## 19. 후속 Industrial Manual RAG 확장

MME-Industry 성공 후 별도 연구로 확장한다.

| 질의 유형 | Cheap/Strong 경로 |
|---|---|
| 알람 코드·부품 번호 | exact/BM25 retrieval |
| 일반 증상 설명 | dense text retrieval |
| 배선도·부품도·계기판 | visual document retrieval |
| 여러 증상·문서 충돌 | graph/hybrid Strong retrieval |
| 안전 근거 부족 | abstain/human escalation |

이 단계에서는 page/evidence ground truth가 있는 별도 매뉴얼 QA benchmark가 필요하다. MME-Industry의 이미지와 정답을 PDF retrieval ground truth로 변환하지 않는다.

## 20. 구현 산출물

| Artifact | 권장 경로 |
|---|---|
| 데이터 감사 | `artifacts/mme_industry/data_audit.json` |
| 분할 manifest | `artifacts/mme_industry/domain_split_manifest.json` |
| 모델 lock | `artifacts/mme_industry/model_pair_lock.json` |
| Cached outputs | `artifacts/mme_industry/cache/<model>/<sample_id>.json` |
| Oracle 보고서 | `docs/MME_P1_ORACLE_REPORT.md` |
| Router lock | `artifacts/mme_industry/router_policy_lock.json` |
| Certification 결과 | `artifacts/mme_industry/certification_summary.json` |
| 최종 보고서 | `docs/MME_P5_CERTIFICATION_REPORT.md` |

## 21. 실행 예상시간

모델 다운로드 시간을 제외한 보수적 추정이다.

| 단계 | 예상시간 |
|---|---:|
| 데이터 감사·manifest | 1–2시간 |
| 100문항 모델-pair preflight | 1–3시간 |
| 전체 1,050문항 Cheap/Strong cache | 4–10시간 |
| Oracle 분석·분할 고정 | 1시간 |
| Router/CV/calibration | 2–4시간 |
| One-shot certification·통계 | 2–4시간 |
| 합계 | 약 1–2일의 GPU/분석 작업 |

## 22. 첫 실행 전 동결 체크리스트

- [ ] 정확한 Cheap/Strong model ID와 revision 결정
- [ ] MME-Industry dataset commit/hash 기록
- [ ] 영문만 primary로 확정
- [ ] domain split manifest 생성
- [ ] forced-choice scoring sanity test 10문항 통과
- [ ] GPU 측정 코드 sanity test 통과
- [ ] P1/P2 Gate를 config에 기록
- [ ] certification data를 development 코드에서 차단
- [ ] 모든 inference output cache 활성화
- [ ] 실행 commit hash 기록

## 참고 자료

- MME-Industry dataset: https://huggingface.co/datasets/Ajax102/MME-Industry
- MME-Industry paper: https://arxiv.org/abs/2501.16688
- UniversalRAG: https://aclanthology.org/2026.acl-long.177/
- Adaptive-RAG: https://aclanthology.org/2024.naacl-long.389/
- MME-Industry는 공개 데이터 카드와 논문 메타데이터를 기준으로 설계했으며, 실제 실행 전에 원본 annotations와 라이선스를 다시 고정 검증한다.

## AI 사용 고지

이 연구 설계 초안 작성에는 AI 기반 문헌 검색과 연구 설계 보조가 사용되었다. 데이터, 모델 출력, 통계 결과는 아직 생성되지 않았으며 문서의 수치는 사전 Gate 또는 공개 데이터 설명이다.
