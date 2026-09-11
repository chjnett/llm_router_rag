# 산업 RAG 및 선택 처리 선행연구 지도

## 검토 범위

2026-09-12에 공식 학회 페이지, 공식 데이터셋 카드, arXiv 초록을 중심으로 1차 스크리닝했다. 아래 “읽은 범위”가 초록인 문헌은 방법과 수치를 논문 본문까지 재검증하기 전에는 인용 문장을 확정하지 않는다.

## 1. 직접 경쟁하는 축

| 연구 | 확인된 핵심 | 본 연구에 주는 제약 | 읽은 범위 |
|---|---|---|---|
| [Adaptive-RAG, NAACL 2024](https://aclanthology.org/2024.naacl-long.389/) | 질문 복잡도에 따라 no/single/iterative retrieval 선택 | “질문별 RAG 경로 선택” 자체는 새롭지 않음 | 공식 초록 |
| [RouteLLM, ICLR 2025](https://arxiv.org/abs/2406.18665) | 약한/강한 LLM을 preference 기반으로 라우팅 | Cheap/Strong 모델 라우팅 자체는 새롭지 않음 | 초록 |
| [UniversalRAG, ACL 2026](https://aclanthology.org/2026.acl-long.177/) | modality와 granularity에 맞는 corpus를 동적으로 선택 | “모달리티 라우팅”만으로는 독창성 부족 | 공식 초록 |
| [ColPali, ICLR 2025](https://openreview.net/pdf?id=ogjBpZ8uSi) | 문서 페이지 이미지를 multi-vector로 검색 | visual document retrieval의 강한 baseline 필요 | 논문 PDF 초록·서론 |
| [SuperRAG, NAACL Industry 2025](https://aclanthology.org/2025.naacl-industry.45/) | layout-aware graph로 텍스트·표·그림 관계 보존 | 단순 multimodal graph도 이미 제안됨 | 공식 논문 페이지 |

## 2. 제조업·정비 도메인과 가까운 연구

| 연구 | 도메인/데이터 | 확인된 기여 | 남는 빈틈 | 읽은 범위 |
|---|---|---|---|---|
| [Manufacturing Safety Chatbot](https://arxiv.org/abs/2511.11847) | 밀링머신·CNC·협동로봇 안전 문서 | 전문가 검증 QA와 24개 RAG 구성 비교 | query별 실제 capability routing은 핵심이 아님 | 초록 |
| [Troubleshooting Procedure RAG](https://arxiv.org/abs/2601.08706) | Fincantieri 대형 cyber-physical system 매뉴얼 | 고장 증상에서 절차 검색 가능성과 cross-validation 필요성 | 비용·위험 보정 선택 처리의 체계적 평가 여지 | 초록 |
| [FactoryLLM](https://arxiv.org/abs/2606.14119) | 약 600쪽의 다중 기계 정비 문서 | 로컬/open model과 cross-machine RAG 평가 환경 | 30개 query로 규모가 작고 라우팅 주장이 중심이 아님 | 초록 |
| [Automobile Failure Graph RAG, IEEE BigData 2024](https://ieeexplore.ieee.org/document/10826046/) | 자동차 고장 knowledge graph | 기존 KG에 맞춘 Graph RAG 최적화 | 문서 modality/모델 비용 선택은 별도 문제 | 공식 초록 |
| [공정 규격 Tree RAG, CCL 2025](https://aclanthology.org/2025.ccl-1.12/) | 구조화된 공정 규격 문서 | 고정 길이 chunk 대신 문단 계층 활용 | 어떤 query에 비싼 경로가 필요한지는 다루지 않음 | 공식 초록 |

## 3. 분야의 공개 문제

| 근거 | 공개 문제 | CapRoute 연결 |
|---|---|---|
| [Multimodal RAG Survey, ACL 2026](https://aclanthology.org/2026.acl-long.204/) | 효율, 세밀한 표현, 강건성이 여전히 과제 | 실제 GPU 비용과 실패 위험을 함께 평가 |
| [Ask in Any Modality, ACL Findings 2025](https://aclanthology.org/2025.findings-acl.861/) | cross-modal alignment와 reasoning의 고유 난점 | 텍스트/표/도면별 capability-aware 경로 필요 |
| [FactoryBench dataset card](https://huggingface.co/datasets/FactoryBench/FactoryBench) | 상태에서 반사실·의사결정까지 난이도 층 존재 | 모델 크기뿐 아니라 필요한 처리 능력에 따라 라우팅 |

## 4. 선행연구에서 확실히 배워야 할 것

### 증거

- Adaptive-RAG와 UniversalRAG는 각각 retrieval strategy와 modality/corpus 선택을 이미 제안한다.
- 제조업 안전·고장·공정 규격 RAG도 이미 공개돼 있다.
- ColPali와 SuperRAG는 visual/layout 정보를 쓰는 강한 비텍스트 baseline을 제공한다.

### 추론

따라서 논문의 중심 문장을 “제조업에 RAG를 적용했다” 또는 “질문마다 모델을 라우팅했다”로 두면 약하다. 새 주장은 **비싼 처리 결과를 보기 전에**, 어떤 문항을 저비용 처리로 안전하게 끝낼 수 있는지 **보지 않은 산업군에서**, **실측 자원과 위험 상한**으로 인증한다는 데 있어야 한다.

### 권고

비교군에는 Always Cheap, Always Strong, random budget matching, 단순 max-prob threshold, Adaptive-RAG식 complexity classifier, 제안 risk-calibrated router를 포함한다. 산업 매뉴얼 단계에서는 BM25, dense, ColPali 계열 visual retrieval, hybrid/graph를 경로별 baseline으로 둔다.

## 5. 아직 확인이 필요한 항목

1. 각 preprint의 최종 출판 여부와 버전 변화
2. 공개 코드·데이터의 실제 실행 가능성
3. 제조업 RAG 연구가 비용을 token/API 가격으로만 측정했는지 GPU 시간까지 측정했는지
4. selective prediction의 Clopper–Pearson 위험 상한을 산업 multimodal RAG에 적용한 직접 선행연구 존재 여부
5. MME-Industry 산업별 원본 분포와 이미지 중복 여부
