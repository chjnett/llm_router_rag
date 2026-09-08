# R1 Retrieval Baseline Report

## 현재 판정

**진행 중.** Oracle과 BM25를 완료했다. BM25 Recall@5가 43.68%이므로 lexical retrieval만으로 parser routing 실험을 시작하지 않는다. 동결 dense 및 hybrid 결과를 먼저 확인한다.

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

Oracle Recall@1이 1.0이 아닌 이유는 일부 문항에 정답 증거 단락이 여러 개이기 때문이다. Oracle은 첫 위치부터 relevant evidence를 반환하지만 Recall은 전체 relevant 단락 중 회수 비율로 계산한다.

## 다음 판정점

고정된 영어 scientific retrieval embedding으로 dense baseline을 실행한다. dense도 증거를 충분히 회수하지 못하면 parser 선택기를 학습하기 전에 chunk/evidence 정렬과 query formulation을 보완한다.
