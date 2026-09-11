# 2026 Routing 선행연구에 따른 노벨티 재점검

## 1. 판정

**REVISE — risk-calibrated Cheap/Strong routing 자체를 핵심 노벨티로 주장하지 않는다.**

## 2. 새로 확인한 직접 선행연구

| 연구 | 확인된 범위 | 본 연구와 겹치는 부분 | 상태 |
|---|---|---|---|
| [R³AG, ACL 2026](https://aclanthology.org/2026.acl-long.939/) | query–retriever capability alignment, retrieval quality와 generation utility 학습 | query별 retriever capability routing, contrastive supervision | peer-reviewed, 공식 초록 |
| [RC-RAG, EMNLP Findings 2024](https://aclanthology.org/2024.findings-emnlp.133/) | retrieval quality·사용 불확실성을 이용한 refusal과 risk metric | RAG 위험 제어와 abstention | peer-reviewed, 공식 초록 |
| [BalanceRAG](https://arxiv.org/abs/2605.20084) | LLM-only→RAG cascade의 joint threshold risk certification | cascade, abstention, target risk, retrieval cost 제한 | preprint, 초록 |
| [SURE-RAG](https://arxiv.org/abs/2605.03534) | evidence sufficiency verification과 selective answering | support/refute/insufficient, calibrated selective risk | preprint, 초록 |
| [BCAS, LREC 2026](https://aclanthology.org/2026.lrec-1.808/) | search depth·retrieval·token budget의 accuracy/cost 측정 | budget-constrained retrieval evaluation | peer-reviewed, 공식 초록 |

## 3. 삭제해야 할 과장된 주장

- “최초의 risk-aware RAG router”
- “최초의 RAG abstention 정책”
- “최초의 query별 retriever 선택”
- “contrastive learning을 처음 routing에 적용”
- “비용과 정확도를 함께 본 최초 연구”

## 4. 남길 수 있는 연구 중심

### Evidence-requirement-aware processing

질문을 단순 난이도로 분류하지 않고 필요한 증거 처리 능력으로 나눈다.

1. exact identifier lookup
2. lexical/semantic passage retrieval
3. layout/table/figure understanding
4. multi-document synthesis 또는 conflict resolution
5. insufficient evidence에 대한 abstention

라우팅 대상도 LLM 하나가 아니라 parser, index, retriever, reranker, generator로 이어지는 **document-processing path**다.

### Domain-heldout causal evaluation

- Strong 경로 결과를 routing feature로 사용하지 않는다.
- 제품군·규정 문서·산업군을 통째로 heldout한다.
- 같은 하드웨어에서 end-to-end GPU time과 peak VRAM을 측정한다.
- 전체 정확도뿐 아니라 unsafe Cheap acceptance의 상한을 보고한다.

이 결합도 자동으로 novelty가 되는 것은 아니다. 선택한 도메인에서 직접 선행연구 전문을 비교한 뒤 claim을 더 좁혀야 한다.

## 5. 가장 강한 반론

> “R³AG가 capability-aware retriever routing을, BalanceRAG가 risk-calibrated cascade를 이미 다뤘다. 새 논문은 기존 기법을 다른 데이터셋에 적용한 것뿐이다.”

이 반론을 이기려면 도메인 이름만 바꾸면 안 된다. 기존 연구가 다루지 않은 **처리 능력 taxonomy**, **domain-heldout failure**, **경로 전체의 실제 비용**, **증거 유형별 오류 분석** 중 적어도 두 축을 실험적으로 보여야 한다.

## 6. 다음 검증 질문

1. TechQA 또는 ObliQA에서 cheap/strong 승패가 증거 유형별로 실제 분리되는가?
2. 단순 max-score보다 evidence-type feature가 unseen product/document에서 유효한가?
3. R³AG baseline을 재현하거나 공정하게 근사할 수 있는가?
4. Clopper–Pearson 또는 conformal 방식이 작은 heldout domain에서도 유효한 coverage를 남기는가?
5. 이득이 model size가 아니라 processing path 선택에서 발생함을 ablation으로 보일 수 있는가?

## 7. 현재 Gate

위 질문 1의 oracle capability gap이 확인되기 전에는 새 아키텍처를 구현하지 않는다. 먼저 데이터와 baseline이 연구 질문을 지지할 수 있는지 확인한다.
