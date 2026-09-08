# R0 QASPER Evidence Audit Report

## 판정

**PASS.** 동결된 QASPER validation 표본 100문항에서 텍스트 검색 기준선을 구축할 수 있을 만큼 증거-단락 정렬이 확인됐다. 이 판정은 멀티모달 표·그림 RAG 성능을 의미하지 않는다.

## 고정 조건

- 데이터: QASPER v0.3 validation (`qasper-dev-v0.3.json`)
- 선택: paper id, question id 오름차순의 첫 100개 answerable question
- seed: 42
- 증거 중복: 여러 annotator가 같은 단락을 선택한 경우 정규화 문자열 기준 1회만 계산
- 매핑: 공백 정규화와 case folding 후 abstract/full-text canonical paragraph와 완전 일치
- tie: 같은 정규화 단락이 논문 안에 반복될 경우 명시적 tie로 허용
- `FLOAT SELECTED`: 표·그림 증거로 분리하며 텍스트 매핑률 분모에서 제외

## 결과

| 지표 | 결과 | Gate | 판정 |
|---|---:|---:|---|
| 고정 문항 | 100 | 100 | PASS |
| 사용 가능한 증거 문항 | 100 | >=80 | PASS |
| 텍스트 증거 | 174 | - | - |
| 매핑된 텍스트 증거 | 163 | - | - |
| 텍스트 증거 매핑률 | 93.68% | >=90% | PASS |
| 고유 매핑 / tie / 미매핑 | 163 / 0 / 11 | tie 기록 | PASS |
| paragraph / float / mixed 문항 | 100 / 0 / 0 | - | 제한 확인 |

## 해석

R1에서 동일 canonical paragraph를 이용해 Oracle, BM25, dense, hybrid 검색을 비교할 수 있다. 11개 미매핑 증거는 원 데이터의 표현 차이나 단락 결합 여부를 분석 대상으로 보존한다. 첫 표본에 `FLOAT SELECTED`가 없으므로 R0는 텍스트-control Gate일 뿐이다. 표·그림 주장은 후속 SPIQA test-A subset 없이는 하지 않는다.

## 재현

```powershell
.venv\Scripts\python.exe -m caproute.cli.audit_qasper --config configs\r0_qasper_audit.yaml
```

원시 결과와 고정 question-id manifest는 `outputs/r0_qasper_audit/`에 생성되며 Git에는 포함하지 않는다. 결과 JSON에는 config/archive SHA-256, Git 상태 및 실행 환경이 기록된다.
