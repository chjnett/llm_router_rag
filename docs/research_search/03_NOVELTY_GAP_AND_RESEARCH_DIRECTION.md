# 연구 공백, 노벨티, 실행 방향

## 1. 보수적 결론

이 연구는 **아키텍처만으로는 약하지만, 제조업의 서로 다른 처리 능력과 안전한 보류를 실측 비용 아래에서 선택하는 문제로 좁히면 논문 가치가 있다.** MME-Industry 하나만으로 산업 매뉴얼 RAG를 주장해서는 안 된다.

## 2. 새롭다고 주장하면 안 되는 것

| 약한 주장 | 이유 |
|---|---|
| 질문 복잡도에 따라 RAG를 바꾼다 | Adaptive-RAG가 선행 |
| 텍스트와 이미지를 선택 검색한다 | UniversalRAG 등 선행 |
| 작은 모델과 큰 모델을 라우팅한다 | RouteLLM 계열 선행 |
| 제조업 문서에 RAG를 쓴다 | 안전·고장·공정 규격 연구 선행 |
| 문서 페이지를 이미지로 검색한다 | ColPali 계열 선행 |

## 3. 방어 가능한 기여 묶음

### 기여 1 — Causal early routing

라우팅 시점에 Cheap 결과와 입력 메타데이터만 사용한다. Strong 결과·Strong score·Strong latency를 feature로 쓰지 않는다. 그래야 Strong 호출 생략이 실제 절감이다.

### 기여 2 — Cross-industry generalization

문항을 무작위로 나누지 않고 산업 분야 자체를 development/calibration/certification으로 분리한다. 이는 동일 이미지·유사 문항 누수보다 어려운 “보지 않은 산업” 일반화를 측정한다.

### 기여 3 — Risk-calibrated abstention

정확도 평균만 높이는 대신 Cheap 오답 수락률의 신뢰구간 상한을 제한한다. 데이터셋 답 `E`와 시스템 보류를 분리하고, 안전성이 낮으면 사람에게 전달한다.

### 기여 4 — Measured compute

비용을 모델 파라미터나 API 가격으로 가정하지 않고 같은 RTX 3090에서 GPU time, end-to-end latency, peak VRAM, Strong 호출률을 측정한다.

## 4. 논문 중심 가설

> Strong-derived 정보를 사용하지 않는 risk-calibrated capability router는 보지 않은 산업 분야에서도 Always Strong 정확도의 97% 이상을 유지하면서 실제 GPU 처리 비용을 20% 이상 절감할 수 있다.

이 문장은 **가설**이며 현재 결과가 아니다. 최종 수치는 certification split 1회 평가 뒤에만 쓴다.

## 5. 단계별 연구 프로그램

| 단계 | 데이터 | 증명할 것 | 진행 조건 |
|---|---|---|---|
| A. Feasibility | MME-Industry development | Cheap/Strong capability gap과 oracle 절감 가능성 | 각 모델 차이 ≥5%p, oracle 절감 ≥20% |
| B. Locked routing | MME calibration/certification | unseen-industry quality–cost–risk | 정확도 유지 ≥97%, 절감 ≥20% |
| C. External modality | FactoryBench | 정책 개념이 telemetry reasoning에도 통하는가 | 데이터 무결성 감사 통과 |
| D. Industrial manual RAG | 자체 gold benchmark | 실제 매뉴얼의 텍스트·표·도면·절차를 능력별 처리 | 근거 라벨과 전문가 검증 확보 |

## 6. 산업 매뉴얼에서 적용할 최종 아키텍처

| 입력 신호 | Cheap 경로 | Strong 경로 | 보류 조건 |
|---|---|---|---|
| 정확한 알람 코드 | BM25/text lookup | 다중 문서 비교 | 코드 미존재·버전 충돌 |
| 자연어 증상 | dense/hybrid retrieval | 원인-절차 추론 | 근거 coverage 부족 |
| 표·수치 | layout parser | VLM 표 추론 | 단위·revision 불일치 |
| 도면·패널 | visual retriever | 강한 VLM | 이미지 해상도/영역 불확실 |
| 안전 조치 | 규칙+근거 검색 | 강한 reasoning+검증 | 상충 근거 또는 고위험 |

## 7. 핵심 ablation

1. Cheap confidence만 사용 vs 입력 metadata 추가
2. 무작위 split vs 산업군 heldout split
3. binary Cheap/Strong vs Cheap/Strong/Abstain
4. 가정 비용 vs 실제 GPU 시간
5. free generation confidence vs A–E forced-choice log-likelihood

## 8. 실패도 의미 있게 남기는 규칙

- Cheap와 Strong 차이가 작으면 모델 조합 부적합으로 결론 낸다.
- Oracle도 20%를 못 줄이면 router 학습 전에 중단한다.
- 평균은 좋아도 산업별 4/5에서 같은 방향이 아니면 일반화 주장을 낮춘다.
- 위험 상한이 5%를 넘으면 “안전 인증 성공”이라고 쓰지 않는다.
- accepted Cheap 표본이 부족하면 실패가 아니라 `INCONCLUSIVE`로 보고 표본을 늘린다.

## 9. 지금 바로 할 다음 작업

[../../MME_INDUSTRY_RESEARCH_DESIGN.md](../../MME_INDUSTRY_RESEARCH_DESIGN.md)의 Phase 0을 실행해 MME 파일 checksum, 산업별 행 수, 이미지 중복, 선택지/정답 유효성을 검증한다. 그 전에는 모델 다운로드나 장시간 GPU 추론을 시작하지 않는다.
