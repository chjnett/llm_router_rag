# 연구 방향 보드

## 보드 규칙

- `EXPLORE`: 검토 중이며 주제로 확정하지 않음
- `PREFLIGHT`: 짧은 데이터/실험 검증 진행 가능
- `HOLD`: 가치가 없다는 뜻이 아니라 선행 조건이 부족함
- `DROP`: 반증 또는 실행 불가능성 때문에 중단
- `LOCKED`: Topic Lock Gate를 통과한 최종 주제

## 현재 후보

| ID | 방향 | 해결하려는 실제 문제 | 평가 가능한 데이터 | 가장 큰 장점 | 가장 큰 위험 | 상태 |
|---|---|---|---|---|---|---|
| D1 | Scientific PDF capability routing | 모든 질의에 visual retriever를 쓰는 낭비 | QASPER, SciVQA, SPIQA 계열 | 기존 코드와 결과가 가장 많음 | 현재 비용 Gate가 미달했고 architecture 중심으로 보일 수 있음 | HOLD |
| D2 | 산업 이미지 Cheap/Strong/Abstain | 산업 이미지마다 필요한 VLM 능력이 다름 | MME-Industry | 정답 라벨과 산업군 분리가 명확함 | 매뉴얼 RAG가 아니라 image QA임 | PREFLIGHT |
| D3 | 산업 매뉴얼 troubleshooting RAG | 알람·증상·표·도면에 맞는 처리 경로 선택 | 공개 매뉴얼 + 자체 gold QA 필요 | 사용 문제와 기존 CapRoute가 직접 연결됨 | 라벨 구축과 전문가 검증 비용이 큼 | EXPLORE |
| D4 | 산업 telemetry reasoning routing | 상태 확인과 반사실/조치 판단에 필요한 능력이 다름 | FactoryBench 후보 | 난이도·인과 수준이 명시됨 | PDF/RAG 중심 관심에서 멀어지고 데이터 무결성 확인이 필요함 | HOLD |
| D5 | 기술지원 evidence-aware RAG | 오류 코드·증상·다중 원인에 같은 검색 비용을 쓰는 낭비 | TechQA, TechQA-RAG-Eval | 실제 사용자 질문·gold 문서·낮은 윤리 부담 | 오래된 단일 기업 corpus와 대규모 색인 | PREFLIGHT |
| D6 | 규제 문서 capability routing | 단일 의무 검색과 multi-passage 해석의 비용 차이 | ObliQA, LegalBench-RAG | gold passage/span과 결정론적 retrieval 평가 | 이미 강한 LTR/hybrid 연구, 법률 전문성 필요 | EXPLORE |
| D7 | 기업 지식 path routing | 제품·기술·재무 문서 질문별 처리 요구 차이 | EKRAG | 실제 기업 문서와 multi-hop 질문 | judge 의존 평가와 배포 라이선스 확인 필요 | HOLD |
| D8 | CTI knowledge routing | exact CVE/CWE와 multi-source 위협 분석의 능력 차이 | CTIBench, CTIConnect | task label과 실용성이 높음 | 직접 RAG benchmark가 이미 존재하고 dual-use 위험 | HOLD |

## 비교 기준

| 기준 | 질문 |
|---|---|
| Problem value | 실제 사용자가 비용 또는 실패 때문에 겪는 문제가 분명한가? |
| Measurability | gold label과 자동 지표로 성공·실패를 판정할 수 있는가? |
| Novelty | 제조업 적용이나 라우팅 자체를 넘어 새 검증 축이 있는가? |
| Feasibility | RTX 3090 24GB 한 장과 현재 기간으로 실행 가능한가? |
| Paper story | 하나의 명확한 RQ와 반증 가능한 주장으로 설명되는가? |

## 다음 비교 행동

D2와 D5의 데이터 접근성부터 CPU로 비교한다. 이후 각각 100개 이내에서 Cheap–Strong capability gap과 oracle saving을 측정한다. 이 preflight는 후보를 자동 채택하는 절차가 아니라, 긴 GPU 실험 전에 신호가 없는 방향을 제거하는 과정이다.

## 새 후보 템플릿

```markdown
| D? | 방향 | 실제 문제 | 데이터 | 장점 | 치명적 위험 | EXPLORE |
```
