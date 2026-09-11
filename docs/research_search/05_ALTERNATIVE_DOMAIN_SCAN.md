# CapRoute 대체 도메인 탐색

## Material Passport

- Origin Skill: academic-research-suite
- Mode: literature scan + topic exploration
- Search Date: 2026-09-12
- Verification: 공식 학회 페이지·공식 저장소·공식 데이터 카드 중심 V1 스크리닝
- Status: 후보 탐색이며 최종 주제 아님

## 1. 결론

현재 자원과 관심사에 가장 잘 맞는 대체 후보는 **기술지원 문서 RAG**다. **규제 문서 RAG**는 평가 데이터가 가장 강하지만 법률 도메인 전문성과 경쟁 부담이 더 크다. 산업 매뉴얼 RAG는 실제 문제 적합성은 가장 높지만 gold QA 구축이 선행돼야 한다.

## 2. 후보 비교

| 우선순위 | 후보 | 공개 라벨 | 자연어 RAG 적합성 | RTX 3090 가능성 | 직접 경쟁 부담 | 현재 판단 |
|---:|---|---|---|---|---|---|
| 1 | 기술지원 문서 | 답변·근거 문서 | 매우 높음 | 높음 | 중간 | **즉시 데이터 감사** |
| 2 | 규제·컴플라이언스 문서 | gold passage/span | 매우 높음 | 높음 | 높음 | **강한 대안** |
| 3 | 산업 매뉴얼 troubleshooting | 자체 구축 필요 | 매우 높음 | 높음 | 중간 | **장기 주제** |
| 4 | 기업 지식 문서 | 수동 QA, judge 의존 | 높음 | 높음 | 중간 | 데이터 접근 확인 |
| 5 | 금융 보고서 | 답·reasoning program | 중간~높음 | 높음 | 매우 높음 | 우선순위 낮춤 |
| 6 | Cyber Threat Intelligence | 다수 task label | 높음 | 높음 | 매우 높음 | 우선순위 낮춤 |
| 7 | 의료 RAG | 대규모 QA | 높음 | 일부 가능 | 매우 높음+고위험 | 현재 보류 |

이 평가는 V1 문헌 스크리닝에 기반한 임시 판단이다. FINER 점수나 최종 선택으로 사용하지 않는다.

## 3. 후보 A — 기술지원 문서 RAG

### 근거

- [TechQA, ACL 2020](https://aclanthology.org/2020.acl-main.117/)은 실제 기술지원 포럼 질문과 accepted IBM Technote 답을 연결한다.
- 공식 논문은 600 train, 310 development, 490 evaluation QA와 801,998 Technote corpus를 설명한다.
- [IBM 공식 코드](https://github.com/IBM/techqa)는 Apache-2.0이며 leaderboard는 종료됐지만 데이터 사용 안내와 평가 코드를 유지한다.
- [NVIDIA TechQA-RAG-Eval](https://huggingface.co/datasets/nvidia/TechQA-RAG-Eval)은 45.8MB corpus와 소규모 JSON을 제공해 저비용 preflight 후보가 된다.

### CapRoute 적용

| 질문 신호 | Cheap 처리 | Strong 처리 |
|---|---|---|
| 제품명·오류 코드·로그 문자열 | BM25 또는 exact match | 불필요 |
| 자연어 증상·표현 불일치 | dense retrieval | query rewrite + reranker |
| 여러 원인·버전 비교 | hybrid retrieval | multi-document reasoning |
| 근거 없음·충돌 | 답변 금지 | abstain 또는 human |

### 가능한 차별점

**Evidence-requirement-aware routing**: 질문 난이도만 예측하지 않고 exact identifier, lexical symptom, semantic symptom, multi-document diagnosis, insufficient evidence 중 어떤 증거 처리가 필요한지 조기에 선택한다.

### 치명적 위험

- 데이터가 오래됐고 IBM 단일 제품 생태계에 편향될 수 있다.
- 전체 80만 문서 corpus는 저장 공간과 색인 시간이 크다.
- accepted answer가 항상 현재 제품 버전에 유효한지 별도 확인이 필요하다.

## 4. 후보 B — 규제·컴플라이언스 RAG

### 근거

- [ObliQA 공식 저장소](https://github.com/RegNLP/ObliQADataset)는 40개 규제 문서와 27,869개 question-passage pair를 공개한다.
- [RIRAG 2025 shared task](https://aclanthology.org/2025.regnlp-1.1/)는 ObliQA를 이용해 retrieval과 answer generation을 비교했다.
- [ObliQA-MP, NLLP 2025](https://aclanthology.org/2025.nllp-1.10/)는 여러 passage를 결합해야 하는 규제 QA와 learning-to-rank를 다룬다.
- [LegalBench-RAG](https://github.com/ZeroEntropy-AI/legalbenchrag)는 character-level gold span으로 retrieval precision/recall을 결정론적으로 계산한다.

### CapRoute 적용

Cheap BM25/dense retrieval로 충분한 단일 의무 질문과, graph/LTR/reranking이 필요한 multi-passage 질문을 구분한다. 잘못된 passage를 안전하게 수락하는 위험과 처리 비용을 함께 측정한다.

### 장점과 위험

- 장점: gold passage가 있어 generation judge 없이 retrieval을 평가할 수 있다.
- 위험: 이미 hybrid, graph feature, LTR 연구가 있어 단순 router는 약하다.
- 위험: 법률적 정확성을 주장하려면 전문가 검증이 필요하다. 초기 논문은 retrieval benchmark 연구로 제한해야 한다.

## 5. 후보 C — 기업 지식 RAG

[EKRAG, KnowledgeNLP 2025](https://aclanthology.org/2025.knowledgenlp-1.13/)은 제품 발표, 기술 블로그, 재무 보고서 등 5,000개 공개 기업 문서와 1,347개 수동 질문을 설명한다. 문서 유형과 multi-hop 수준이 섞여 있어 경로 선택에는 적합하지만, 답변 평가는 EM/RM/LLM-as-judge 의존성이 있고 데이터 배포·라이선스를 먼저 확인해야 한다.

## 6. 우선순위를 낮춘 후보

### 금융 문서

[FinQA, EMNLP 2021](https://aclanthology.org/2021.emnlp-main.300/)은 전문가 QA와 gold reasoning program을 제공해 자동 평가가 강하다. 그러나 table-text numerical reasoning 분야가 이미 성숙했고, 본 연구가 retrieval routing보다 solver routing 연구로 이동할 가능성이 크다.

### Cyber Threat Intelligence

[CTIBench, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5acd3c628aa1819fbf07c39ef73e7285-Abstract-Datasets_and_Benchmarks_Track.html)은 다섯 CTI task family의 라벨을 제공한다. 그러나 [CTIConnect, KDD 2026](https://doi.org/10.1145/3770855.3817527)이 heterogeneous CTI RAG를 직접 평가하므로 단순 domain pivot의 novelty가 약하다. dual-use 위험도 별도 검토해야 한다.

### 의료 문서

[MIRAGE/MedRAG, ACL Findings 2024](https://aclanthology.org/2024.findings-acl.372/)은 7,663개 의료 QA와 대규모 RAG 비교를 제공한다. 데이터는 좋지만 계산 경쟁 규모가 크고 의료 안전성·전문가 검증 부담이 커 현재 자원에서는 우선순위를 낮춘다.

## 7. 최소 비용 판별 실험

1. TechQA-RAG-Eval의 라이선스, 행 수, corpus-answer 연결률을 CPU로 감사한다.
2. 100개 질문에서 BM25와 dense+rereanker의 per-query 승패를 측정한다.
3. 두 경로가 서로 다른 질문에서 이기는지 oracle saving을 계산한다.
4. 같은 절차를 ObliQA 100개에 적용해 데이터 효과와 domain 효과를 분리한다.
5. 두 후보 중 capability gap과 실측 절감이 큰 쪽만 본 실험 후보로 유지한다.

## 8. 제한

이번 탐색은 systematic review가 아니라 후보 선정을 위한 V1 scan이다. 숫자와 방법 세부는 관련 원문을 V2 전문 검토하기 전 제출 논문의 확정 인용으로 사용하지 않는다. AI 도구가 검색·분류·요약에 사용됐다.
