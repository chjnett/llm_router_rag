# Research Rules

## 1. 데이터 누수 방지

- page random split보다 document-level split을 우선한다.
- 같은 paper의 page가 train과 test에 동시에 들어가지 않게 한다.
- threshold는 Calibration split에서만 선택한다.
- Certification / Final / External 결과를 보고 threshold를 수정하지 않는다.

---

## 2. Split 정책

권장:

```text
Selection / Train
Calibration
Certification
Final Test
External Test
```

각 split의 document id 목록을 파일로 저장한다.

---

## 3. Gate 기반 연구

모든 Phase는 Gate를 통과해야 다음 Phase로 간다.

Fail 결과를 숨기거나 기준을 사후 완화하지 않는다.

---

## 4. Baseline 우선

Proposed method보다 먼저 다음을 구현한다.

- Always Cheap
- Always Strong
- Rule-Based
- Input-only Router
- Lower-first + Verifier

---

## 5. 비용 정의

parameter count나 theoretical FLOPs만으로 비용을 주장하지 않는다.

반드시 측정:

- p50 latency
- p95 latency
- GPU seconds
- peak VRAM
- energy/page if available
- model call count
- normalized cost

---

## 6. Router 원칙

처음부터 deep router를 만들지 않는다.

순서:

1. Logistic Regression
2. ExtraTrees
3. XGBoost
4. small MLP only if justified

Router complexity보다 architecture와 operating point가 핵심이다.

---

## 7. 실패 실험 기록

실패도 삭제하지 않는다.

반드시 저장:

- config
- log
- metric
- reason
- decision
- next action

---

## 8. 주장 제한

다음과 같은 과도한 주장을 금지한다.

- "Adaptive RAG is universally more efficient."
- "Our router generalizes to all PDFs."
- "Strict safety is guaranteed" without certification.
- "Small models are always cheaper."

권장:

> Scientific born-digital PDFs에서 selective document processing의 cost-quality tradeoff를 검증했다.

---

## 9. Reproducibility

모든 결과는 git commit과 config hash를 가져야 한다.

---

## 10. 변경 관리

Main research question이 바뀌는 변경은 `DECISION_LOG.md`에 반드시 기록한다.

