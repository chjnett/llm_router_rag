# P1 Parser-Pair Repair Plan

## Goal

P1 primary Gate 실패 원인이었던 낮은 Cheap sufficient coverage를 추가 모델 다운로드 없이 개선한다. P2 router는 계속 잠근다.

## Frozen Cohort and Quality Contract

- P1과 동일한 document-disjoint 300 pages, structure 대응 245 pages
- exact table count
- mean GriTS-Top >= 0.80
- mean GriTS-Loc >= 0.50
- Strong baseline은 Docling 2.126.0 cache로 고정

## Cheap Candidates

| ID | PyMuPDF find_tables 설정 | 목적 |
|---|---|---|
| `pymupdf_union_refine` | lines, layout union, grid refine | layout/line 후보 결합 및 누락된 행·열 복구 |
| `pymupdf_text` | vertical=text, horizontal=text, no layout | 선 없는 표를 text 정렬로 탐지 |
| `pymupdf_lines_raw` | lines, no layout | layout gate가 놓친 선 기반 표 회수 |

기존 `pymupdf` default가 대조군이다. 후보 선택 전에 모든 후보를 동일 300페이지에서 실행하며 parser output을 cache한다.

## Candidate Gate

1. Cheap sufficient coverage가 기존 11.43%보다 높아야 한다.
2. 새 Cheap p50 / 기존 Strong p50 < 0.50이어야 한다.
3. 기존 Strong과 결합한 zero-overhead Oracle saving >= 15%여야 한다.
4. primary sufficiency threshold는 변경하지 않는다.

통과 후보가 여러 개면 Oracle saving을 우선하고, 그 다음 p95 latency를 사용한다. 모두 실패하면 새 lightweight parser 도입을 검토한다.
