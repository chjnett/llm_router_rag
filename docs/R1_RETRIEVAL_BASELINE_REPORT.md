# R1 Retrieval Baseline Report

## 현재 판정

**BASELINE 완료 / ROUTING 보류.** Oracle, BM25, frozen BGE dense 및 RRF hybrid를 완료했다. Dense가 BM25보다 개선됐지만 Recall@5 54.14%는 parser representation 차이를 검증하기에 낮다. Stop Rule에 따라 chunk/query/re-ranking을 먼저 수리한다.

## 평가 계약

- R0에서 고정한 100문항을 그대로 사용
- canonical paragraph 내부의 exact-mapped human evidence만 relevance로 사용
- 매핑 증거가 하나도 없는 3문항은 제외하고 97문항 평가
- 문서가 주어진 scientific-paper RAG 설정: 각 질문은 해당 논문 단락 안에서 검색
- 지표: evidence Recall@1/5/10, MRR, nDCG@5

## 결과

| 방법 | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| Oracle evidence ranking | 0.7738 | 0.9936 | 1.0000 | 1.0000 | 1.0000 |
| BM25 | 0.1690 | 0.4368 | 0.5665 | 0.3645 | 0.3238 |
| BGE-small-en-v1.5 dense | 0.1406 | **0.5414** | **0.6872** | 0.3959 | **0.3846** |
| BM25+dense RRF | **0.1922** | 0.4978 | 0.6350 | **0.4137** | 0.3839 |

Oracle Recall@1이 1.0이 아닌 이유는 일부 문항에 정답 증거 단락이 여러 개이기 때문이다. Oracle은 첫 위치부터 relevant evidence를 반환하지만 Recall은 전체 relevant 단락 중 회수 비율로 계산한다.

Dense inference는 RTX 3090에서 97문항, 34개 고유 논문에 3.44초가 걸렸다. BM25 top-5와 dense top-5의 합집합은 Recall 64.53%, top-10 합집합은 77.05%다. 두 검색기는 상호 보완적이지만 고정 RRF가 Recall@5를 49.78%로 낮췄으므로 RRF를 성공 결과로 포장하지 않는다.

## 다음 판정점

라우팅은 계속 잠근다. 먼저 미회수 문항을 evidence length, question type, paragraph position별로 분석하고, 후보 합집합 안에서 lightweight re-ranking이 Recall@5를 올릴 수 있는지 검증한다. 같은 frozen 100문항에서 임의로 threshold를 조정하지 않는다.
