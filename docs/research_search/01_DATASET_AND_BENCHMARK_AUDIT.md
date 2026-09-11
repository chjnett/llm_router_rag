# 데이터셋 및 벤치마크 검증

## 1. 빠른 판단

| 후보 | 입력/과제 | 정답 라벨 | CapRoute에서의 역할 | 현재 판단 |
|---|---|---|---|---|
| MME-Industry | 산업 이미지 + A–E 객관식 질문 | 있음 | Cheap/Strong/Abstain 라우팅 preflight | **즉시 사용** |
| FactoryBench | 산업 로봇 시계열·텍스트, 인과 QA | 다수 형식 | 문서 밖의 산업 능력 라우팅 확장 | **파일 무결성 확인 후** |
| 자체 산업 매뉴얼 QA | PDF의 텍스트·표·도면·절차 | 직접 구축 필요 | 최종 산업 RAG 주장 | **후속 핵심 벤치마크** |

## 2. MME-Industry

### 확인된 사실

- 공식 배포: [Hugging Face dataset](https://huggingface.co/datasets/Ajax102/MME-Industry), [논문](https://arxiv.org/abs/2501.16688)
- 이미지 기반 산업 QA이며 영어와 중국어 annotation을 제공한다.
- 약 1,050문항, 21개 산업 분야, 산업별 약 50문항이다.
- A–E 객관식이며 `E`는 “그림에 해당 특징이 없음”이라는 정상 정답 후보다.
- Apache-2.0이며 배포 크기는 약 447MB다.
- 공식 Hub에는 하나의 약 1.05k split만 노출된다.

### 이 데이터로 답할 수 있는 질문

> 작은 VLM의 답을 그대로 수락할지, 큰 VLM으로 보낼지, 시스템이 답변을 보류할지를 보지 않은 산업군에서도 조기에 결정할 수 있는가?

### 답할 수 없는 질문

- PDF 매뉴얼에서 올바른 페이지나 절차를 검색하는가?
- 현장 고장 진단과 안전 조치를 생성하는가?
- 실제 공장 문서의 OCR, 표 구조, 도면 참조를 처리하는가?

### 분할 권고

공식 split을 학습과 시험에 임의 혼합하지 않는다. 산업 분야 자체를 묶어 다음처럼 고정한다.

| 용도 | 산업 수 | 예상 문항 수 | 허용 작업 |
|---|---:|---:|---|
| Development | 12 | 약 600 | 특징·모델·학습 방법 개발 |
| Calibration | 4 | 약 200 | 임계값과 보류율 선택 |
| Certification | 5 | 약 250 | 잠근 정책의 최종 1회 평가 |

이는 공식 leaderboard 점수가 아니라 **custom domain-heldout study**로 보고해야 한다.

## 3. FactoryBench

### 확인된 사실

- 공식 카드: [FactoryBench/FactoryBench](https://huggingface.co/datasets/FactoryBench/FactoryBench)
- 산업 로봇 telemetry를 이용한 상태·개입·반사실·의사결정 QA를 표방한다.
- 카드에는 70,918 QA, UR3와 KUKA KR10 데이터, 27개 fault mechanism, train/validation/test 구성이 기재돼 있다.
- 라이선스는 CC BY 4.0이고 전체 파일 크기는 약 5.22GB로 표시된다.

### 주의할 점

2026-09-12 확인 당시 Hub viewer는 dataset generation error를 표시했고, 카드의 일부 자동 메타데이터도 본문과 일관되지 않았다. 따라서 다음을 통과하기 전에는 주 실험 데이터로 잠그지 않는다.

1. 파일 목록과 checksum 저장
2. JSONL/Parquet 실제 행 수 검증
3. episode 중복과 split 누수 검사
4. 정답 생성 방식과 LLM-as-judge 의존성 확인
5. 50~100개 샘플 수동 감사

### 프로젝트에서의 위치

FactoryBench는 PDF/RAG 데이터가 아니다. 다만 이미지 QA에서 얻은 라우팅 정책이 telemetry/causal reasoning에도 통하는지 보는 **다른 modality의 외부 검증**으로 가치가 있다.

## 4. 최종 산업 매뉴얼 벤치마크 설계

### 문항 유형

| 유형 | 예시 | 기대 검색 경로 | 자동 평가 |
|---|---|---|---|
| Exact identifier | “Alarm E-104의 의미는?” | BM25/text | 정답 문자열·근거 페이지 |
| Symptom | “축 진동과 과열이 함께 발생” | dense/hybrid | 원인·절차 ID |
| Procedure | “재가동 전 점검 순서” | hierarchy/tree | 단계 순서·필수 단계 |
| Table/spec | “허용 토크 범위” | layout/table | 수치+단위 exact match |
| Diagram/panel | “이 표시등 위치는?” | visual retriever | 영역·페이지·선택지 |
| Cross-document | “모델별 조치 차이” | hybrid/graph | 문서별 근거와 결론 |
| Safety conflict | 상충하는 조치 | abstain/human | 위험 수락률 |

### 최소 라벨 스키마

`question_id`, `machine_family`, `document_id`, `page_id`, `evidence_region`, `answer`, `answer_type`, `required_modality`, `risk_level`, `allowed_abstain`, `annotator_agreement`를 저장한다.

## 5. 권고된 순서

1. MME-Industry로 모델 간 capability gap과 oracle 절감 가능성을 먼저 측정한다.
2. Gate가 통과하면 domain-heldout router를 평가한다.
3. FactoryBench는 다운로드·무결성 감사 뒤 외부 검증 후보로 둔다.
4. 주 논문을 산업 매뉴얼 RAG로 확장할 때 소형이지만 정확한 gold benchmark를 구축한다.
