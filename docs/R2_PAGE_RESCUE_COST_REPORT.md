# R2-P Query-Time Page Rescue Cost Report

## 판정

**CONDITIONAL PASS.** `top-5 pages + adjacent ±1` 전략은 질문 간 Strong output cache를 공유하는 34-query workload에서 page evidence recall 0.9706을 유지하면서 고유 Strong 페이지를 22.33%, 측정 Strong 시간을 18.26% 줄여 동결 Gate를 통과했다. 캐시 없는 독립 질의 비용은 Always Strong보다 크므로 무조건적인 효율 주장은 금지한다.

## 실측 환경

- PDFs/pages: 10/103
- Strong: Docling 2.126.0, CUDA, OCR off, table structure on
- GPU: RTX 3090
- page inference output: `cache/r2_docling_pages`에 103/103 저장
- p50/p95: 205.51/1022.44ms per page
- Always Strong measured sum: 37.05s
- observed peak CUDA allocation: 527,224,320 bytes

장시간 단일 프로세스는 첫 실행 100페이지 부근 stall, 두 번째 실행 43페이지에서 native process exit가 발생했다. 20페이지 이하 독립 배치와 latency checkpoint로 103페이지를 실패 없이 복구했다. 에너지는 복구 배치별로 합산되지 않았으므로 총 에너지 결과로 사용하지 않는다.

## 전략 비교

| 전략 | Page Recall | 고유 Strong pages | 페이지 감소 | Strong 시간 | 시간 절감 | Gate |
|---|---:|---:|---:|---:|---:|---|
| Always Strong | 1.0000 | 103 | 0% | 37.05s | 0% | 기준 |
| Top-5 pages | 0.8971 | 61 | 40.78% | 21.41s | 42.21% | 품질 FAIL |
| Top-5 + adjacent ±1 | 0.9706 | 80 | 22.33% | 30.29s | 18.26% | PASS |

Gate는 quality page recall >=0.95, unique Strong page reduction >=20%, Strong latency saving >=10%다.

## 캐시 의존성

| 전략 | 캐시 없는 page calls | 캐시 없는 Strong 시간 | 한 번의 Always Strong 대비 |
|---|---:|---:|---:|
| Top-5 pages | 160 | 54.86s | 48.05% 더 비쌈 |
| Top-5 + adjacent ±1 | 256 | 93.63s | 152.68% 더 비쌈 |

따라서 결과는 지속적인 document/page cache가 있는 서비스에서만 경제적이다. 단발성 질문마다 Strong page를 다시 처리하는 시스템에는 적용하면 안 된다.

## Output evidence 보존

고정 token coverage 0.80 기준으로 63 evidence instances를 확인했다.

| 출력 | Mean coverage | Usable rate |
|---|---:|---:|
| PyMuPDF native text | 0.9639 | 100% |
| Docling Strong text | 0.9632 | 100% |
| Selective Docling | - | 98.41% evidence / 97.06% questions |

QASPER text-control에서는 Strong이 Cheap보다 evidence text를 개선하지 않았다. R2-P의 의미는 page selection/caching feasibility이지 Strong quality gain이 아니다.

## 다음 결정

QASPER에서 추가 GPU 실험을 중단한다. 다음 GPU는 표·그림 evidence가 있는 작은 multimodal subset에서 수행한다. Always Text 대비 visual/Strong path가 실제 retrieval utility를 높이는지 먼저 확인하고, 그렇지 않으면 ColPali/router 확대를 중단한다.
