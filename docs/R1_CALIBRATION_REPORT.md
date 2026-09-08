# R1 Retrieval Recovery Calibration Report

## 판정

**FAIL.** Paper-disjoint calibration 200문항 중 exact-mapped text evidence가 있는 187문항을 평가했다. 가장 좋은 frozen candidate는 MiniLM-L6 adjacent rescue였지만 Recall@5 0.6303으로 Gate 0.65에 미달했다. Certification과 Final은 열지 않는다.

## 고정 분할

- Calibration: 62 papers / 200 answerable questions
- Evaluated: 61 papers / 187 questions
- Skipped: 13 questions with no exact-mapped textual evidence
- Development 34 papers와 교집합 없음

## 결과

| 방법 | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@5 |
|---|---:|---:|---:|---:|---:|
| BM25 | 0.1359 | 0.4268 | 0.5997 | 0.3571 | 0.3075 |
| Section-aware BGE-small | 0.2553 | 0.5979 | 0.7181 | 0.5193 | 0.4867 |
| Adjacent + MiniLM-L6 | **0.2769** | **0.6303** | **0.8040** | **0.5593** | **0.5122** |
| Adjacent + MiniLM-L12 | 0.2621 | 0.6212 | 0.7811 | 0.5474 | 0.4987 |

Candidate pool Recall은 0.9518이다. L6 reranker는 nDCG@5 기준 0.50을 통과했지만 Recall@5 기준 0.65에 0.0197 미달했다. L12는 모든 핵심 지표에서 L6보다 낮아 폐기한다.

## 해석

Development의 near-miss가 paper-disjoint calibration에서도 재현되어 adjacent context 자체는 유망하다. 그러나 paragraph-level evidence Recall Gate는 통과하지 못했다. Query-time rescue는 페이지 단위로 처리하므로, 다음에는 10개 complete PDF에서 retrieval paragraph miss가 evidence page miss로 이어지는지 측정한다. 이 preflight는 Gate를 완화하기 위한 것이 아니라 평가 단위가 실제 아키텍처와 맞는지 확인하기 위한 것이다.

## 다음 제한

- Certification 200과 Final 443의 결과 파일을 생성하지 않는다.
- Calibration에서 추가 reranker/model sweep을 하지 않는다.
- 10-PDF page mapping protocol을 먼저 고정한다.
- page-level 결과가 유망하지 않으면 ColPali/router 학습 전에 현재 QASPER branch를 중단한다.
