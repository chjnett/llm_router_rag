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

## 실패 계층화 결과

- dense top-5 hit: 58/97 (59.79%)
- BM25/dense 모두 hit: 40, dense만 hit: 18, BM25만 hit: 11, 둘 다 miss: 28
- single-evidence hit@5: 65.00%; multiple-evidence: 51.35%
- 100단락 초과 논문 hit@5: 20.00% (5문항뿐이므로 탐색적 결과)

BM25-only 11문항 때문에 lexical 후보를 버리면 안 되며, 둘 다 놓친 28문항 때문에 reranking만으로 전체 문제를 해결할 수도 없다. Reranker 결과는 후보 생성 병목과 순위 병목을 분리하는 preflight로 해석한다.

## R1.1 lightweight reranker 결과

BM25 top-10과 dense top-10의 합집합(평균 15.15개)을 MiniLM cross-encoder로 재순위화했다.

| 지표 | 결과 | Gate | 판정 |
|---|---:|---:|---|
| Candidate Recall | 0.7705 | - | 상한 확인 |
| Recall@5 | 0.5190 | >=0.65 | FAIL |
| nDCG@5 | 0.4296 | >=0.50 | FAIL |
| MRR | 0.4719 | - | dense 0.3959 대비 개선 |
| GPU wall time | 1.61s / 97 questions | - | 저비용 |

첫 relevant paragraph를 위로 올리는 효과는 있었지만 복수 증거 회수와 top-5 recall은 개선하지 못했다. 이 reranker는 채택하지 않는다.

## R1.2 section/title context 결과

| Variant | Recall@5 | Recall@10 | MRR | nDCG@5 | 판정 |
|---|---:|---:|---:|---:|---|
| Plain dense | 0.5414 | 0.6872 | 0.3959 | 0.3846 | 기준 |
| Section-aware passage | **0.5562** | **0.7556** | **0.4913** | **0.4484** | 개선, Gate FAIL |
| Title query + section passage | 0.3326 | 0.4489 | 0.2575 | 0.2299 | 악화, 폐기 |

Section metadata는 candidate 생성과 첫 relevant 순위를 개선했지만 Recall@5 0.65/nDCG@5 0.50 Gate에는 미달했다. 논문 제목을 질문에 반복하는 방식은 semantic signal을 희석한 것으로 추정되며 사용하지 않는다.

## R1.3 adjacent-window rescue 결과

Section-aware dense top-10과 BM25 top-10을 합치고 각 후보의 인접 단락 ±1을 추가한 뒤 MiniLM으로 재순위화했다.

| 지표 | 결과 | Gate | 판정 |
|---|---:|---:|---|
| 평균 seed / expanded candidates | 15.41 / 29.06 | - | - |
| Candidate Recall | 0.9278 | - | 충분한 후보 상한 |
| Recall@5 | 0.6161 | >=0.65 | FAIL (-0.0339) |
| nDCG@5 | 0.5103 | >=0.50 | PASS |
| MRR | 0.5363 | - | 최고 관측값 |
| GPU wall time | 6.41s / 97 questions | - | preflight 비용 |

한 지표만 통과했으므로 전체 Gate는 실패다. 개발 문항에서 조합을 더 탐색하지 않는다.

## 고정 recovery split

| Split | Papers | Answerable questions | 용도 |
|---|---:|---:|---|
| Development | 34 | 100 | 완료된 진단, 재사용 금지 |
| Calibration | 62 | 200 | recovery 방법/설정 선택 |
| Certification | 60 | 200 | 동결 방법 독립 검증 |
| Final | 123 | 443 | 최종 보고 |

모든 split은 paper-disjoint다. Development에 한 질문이라도 포함된 paper는 그 paper의 다른 질문까지 후속 split에서 제외했다.
