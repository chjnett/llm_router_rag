# CapRoute-Industry 연구 서치 묶음

## 목적

이 폴더는 **제조업 도메인으로 CapRoute를 확장할 근거**를 설계 문서와 분리해 보존한다. 검색일은 2026-09-12이며, 현재 문헌 검토는 공식 논문 페이지·데이터셋 카드·초록 수준의 1차 스크리닝이다. 논문 전문을 모두 정독한 체계적 문헌고찰로 간주하지 않는다.

이 근거를 이용해 어떤 주제를 유지·중단·피벗할지는 [../research_incubation/README.md](../research_incubation/README.md)에서 관리한다.

## 읽는 순서

| 순서 | 문서 | 답하는 질문 |
|---:|---|---|
| 1 | [01_DATASET_AND_BENCHMARK_AUDIT.md](01_DATASET_AND_BENCHMARK_AUDIT.md) | 어떤 데이터셋으로 무엇을 검증할 수 있는가? |
| 2 | [02_INDUSTRIAL_RAG_PRIOR_WORK.md](02_INDUSTRIAL_RAG_PRIOR_WORK.md) | 이미 나온 연구와 어디서 겹치는가? |
| 3 | [03_NOVELTY_GAP_AND_RESEARCH_DIRECTION.md](03_NOVELTY_GAP_AND_RESEARCH_DIRECTION.md) | 논문에서 방어 가능한 새 기여는 무엇인가? |
| 4 | [04_SEARCH_PROTOCOL_AND_UPDATE_LOG.md](04_SEARCH_PROTOCOL_AND_UPDATE_LOG.md) | 검색을 어떻게 재현하고 갱신하는가? |

실험 설계와 Gate는 [../../MME_INDUSTRY_RESEARCH_DESIGN.md](../../MME_INDUSTRY_RESEARCH_DESIGN.md)를 따른다.

## 현재 결론

1. MME-Industry는 **산업 매뉴얼 RAG가 아니라 산업 이미지 객관식 QA**이다.
2. 따라서 MME-Industry는 Cheap/Strong/Abstain 라우팅의 저비용 preflight로 쓴다.
3. “질문 복잡도 라우팅”이나 “모달리티 라우팅”만으로는 새롭지 않다.
4. 방어 가능한 핵심은 **Strong 출력을 보지 않는 조기 라우팅 + 보지 않은 산업군 평가 + 실제 GPU 비용 + 위험 보정 보류**의 결합이다.
5. 최종 제조업 RAG 논문은 매뉴얼의 알람 코드·절차·표·도면을 대상으로 한 별도 retrieval benchmark가 필요하다.

## 증거 표기

- **확인됨**: 공식 학회 페이지, 공식 데이터셋 카드 또는 출판 메타데이터에서 직접 확인
- **초록 수준**: 초록과 공개 메타데이터만 확인했으며 세부 실험표는 미검증
- **추론**: 확인된 사실에서 본 프로젝트에 맞게 도출한 해석
- **권고**: 앞으로 실행할 연구 선택이며 아직 결과가 아님
