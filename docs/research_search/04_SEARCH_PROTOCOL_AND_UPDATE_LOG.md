# 문헌 검색 프로토콜 및 갱신 기록

## 1. 검색 목적

CapRoute의 제조업 피벗이 기존 adaptive RAG, multimodal document retrieval, LLM routing, industrial RAG와 어디서 겹치고 무엇을 추가해야 하는지 확인한다.

## 2. 검색일과 범위

- 최초 검색일: 2026-09-12
- 출판 연도 중심 범위: 2024–2026
- 우선 출처: ACL Anthology, IEEE Xplore, OpenReview, 공식 Hugging Face dataset card
- 보조 출처: arXiv. 출판되지 않은 자료는 preprint로 명시한다.
- 언어: 영어 중심, 제조 공정 규격 관련 중국어 논문 1편 포함

## 3. 재현용 검색식

```text
"industrial manual" multimodal RAG benchmark
manufacturing safety chatbot retrieval augmented generation benchmark
industrial troubleshooting procedure RAG technical manuals
adaptive RAG question complexity routing
multimodal RAG modality-aware routing document
weak strong LLM routing cost quality
visual document retrieval ColPali
layout-aware graph multimodal RAG
industrial process specification tree RAG
selective prediction abstention risk calibration RAG
retriever capability routing RAG contrastive
cascaded RAG joint risk calibration
technical support QA technote retrieval benchmark
regulatory multi-passage RAG benchmark
enterprise knowledge RAG benchmark
industrial multimodal benchmark expert labeled QA
robot telemetry causal reasoning benchmark LLM
```

## 4. 포함·제외 기준

### 포함

- 공식 학회/저널 페이지 또는 저자 공개 preprint가 존재
- adaptive retrieval, model routing, multimodal document retrieval, 제조업 QA/RAG 중 하나와 직접 관련
- 데이터·평가·시스템 설계 중 본 연구와 비교 가능한 정보가 있음

### 제외

- 출처를 추적할 수 없는 블로그 요약
- 제품 홍보만 있고 평가 프로토콜이 없는 사례
- 제조업이라는 단어만 등장하고 문서 검색/QA/라우팅과 무관한 연구
- 데이터 라이선스나 정답 생성 경로를 확인할 수 없는 비공개 벤치마크

## 5. 검증 단계

| 등급 | 필요한 확인 | 인용 허용 범위 |
|---|---|---|
| V0 발견 | 제목/URL만 발견 | 후보 목록만 |
| V1 메타데이터 | 저자·연도·venue·초록 확인 | 문제·기여의 요약 |
| V2 전문 검토 | 방법·데이터·표·한계 확인 | 수치와 세부 비교 |
| V3 재현 확인 | 코드/데이터 실행 또는 샘플 감사 | 재현성 및 구현 주장 |

현재 이 폴더의 대다수 선행연구는 V1이고, ColPali 일부만 V2 수준이다. 논문 related work를 확정하기 전 핵심 10편은 V2로 올린다.

## 6. 업데이트 체크리스트

1. 새 문헌을 추가할 때 공식 URL, venue/status, 읽은 범위를 함께 기록한다.
2. 숫자를 옮길 때 표 번호와 평가 split을 적는다.
3. preprint가 출판되면 링크와 상태를 갱신한다.
4. 데이터셋은 commit hash, checksum, license, split을 보존한다.
5. 새로운 선행연구가 novelty를 약화하면 [03_NOVELTY_GAP_AND_RESEARCH_DIRECTION.md](03_NOVELTY_GAP_AND_RESEARCH_DIRECTION.md)의 주장을 먼저 수정한다.

## 7. 변경 기록

| 날짜 | 변경 | 영향 |
|---|---|---|
| 2026-09-12 | MME-Industry, FactoryBench, adaptive/multimodal/industrial RAG 1차 스크리닝 | MME를 final manual RAG가 아닌 preflight로 제한 |
| 2026-09-12 | UniversalRAG와 Adaptive-RAG 확인 | 일반 modality/complexity routing을 novelty에서 제외 |
| 2026-09-12 | 제조 안전·고장 절차·공정 규격 RAG 확인 | 제조업 적용 자체 대신 causal early routing과 risk certification으로 중심 이동 |
| 2026-09-12 | R³AG, RC-RAG, BalanceRAG, SURE-RAG 확인 | capability routing·risk calibration·abstention 자체를 novelty에서 제외 |
| 2026-09-12 | TechQA, ObliQA, EKRAG, FinQA, CTIBench 계열 비교 | 기술지원과 규제 문서를 우선 대체 도메인으로 등록 |

## 8. AI 사용 고지

초기 검색·분류·요약에는 AI 도구를 사용했다. 모든 출처는 공식 링크로 추적 가능하게 기록했지만, 현재 내용은 systematic review가 아니다. 제출 논문에 수치나 강한 비교 주장을 넣기 전 연구자가 원문 PDF와 실험 조건을 직접 확인해야 한다.
