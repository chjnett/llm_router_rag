# R1-P Complete-PDF Evidence Page Mapping Report

## 판정

**PREFLIGHT PASS.** 고정된 calibration 10편/36문항 중 10편 PDF를 모두 파싱했고, evidence page가 자동 매핑된 34문항에서 page Recall@5 0.8971을 얻었다. 이는 paragraph retrieval Gate 실패를 뒤집는 최종 결과가 아니라, 실제 query-time rescue 단위인 page에서 후속 검증할 가치가 있다는 근거다.

## 표본과 매핑

| 항목 | 결과 | Gate | 판정 |
|---|---:|---:|---|
| PDF parse success | 10/10 | >=8/10 | PASS |
| 총 페이지 | 103 | - | - |
| Canonical paragraphs | 497 | - | - |
| Exact / approximate | 121 / 334 | - | - |
| Ambiguous / unmapped | 26 / 16 | - | 보존 |
| Evidence paragraphs mapped | 57/59 (96.61%) | >=80% | PASS |
| Mapped questions | 34 | >=30 | PASS |

Approximate mapping은 결과 전에 고정한 token coverage >=0.80, best-second page margin >=0.10만 허용했다. Evidence mapping 중 exact 14, approximate 43, ambiguous/unmapped 2였다. 허용 approximate evidence의 coverage 중앙값은 0.9630, 최솟값은 0.8125였다.

## 페이지 검색 결과

| 지표 | 결과 | Gate | 판정 |
|---|---:|---:|---|
| Page Recall@5 | 0.8971 | >=0.65 | PASS |
| Page Hit@5 | 0.9118 | - | - |
| Top-5 page + adjacent ±1 Recall | 0.9706 | - | 참고 |
| Top-5 page + adjacent ±1 Hit | 0.9706 | - | 참고 |
| 평균 adjacent candidate pages | 7.53 | - | 비용 필요 |
| Native scan p50/p95 | 2.58/3.61 ms/page | - | CPU extraction |

Paragraph Recall@5 0.6303보다 page Recall@5가 높은 이유는 top-ranked non-evidence paragraph가 실제 evidence와 같은 페이지에 있을 수 있기 때문이다. Page rescue는 그 페이지 전체를 Strong/VLM 처리하므로 이 차이는 아키텍처적으로 의미가 있다. 하지만 adjacent 결과는 평균 7.53페이지를 처리하므로 품질만 보고 비용 절감을 주장할 수 없다.

## 감사와 한계

- Lowest-coverage accepted mapping 5개를 canonical/PDF text로 대조했다.
- 수식 `INLINEFORM` placeholder, 실제 수식 문자, 인용 치환, line-break hyphen 차이가 주요 원인이었다.
- 다섯 사례 모두 선택된 PDF page 내용과 대응했지만 전체 43 approximate evidence를 사람이 검수한 것은 아니다.
- 10 papers / 34 mapped questions의 calibration preflight다.
- Certification/Final 결과가 아니며 ColPali 또는 Strong/VLM 품질을 측정하지 않았다.

## 다음 단계

같은 10편에서 Always Text page retrieval과 query-time Strong rescue의 실제 비용 계약을 구현한다. Strong 처리는 top-5 retrieved pages와 필요 시 adjacent pages로 제한하고, Always Strong 대비 GPU seconds와 wall latency를 측정한다. 비용 상한을 확인하기 전 Router는 학습하지 않는다.
