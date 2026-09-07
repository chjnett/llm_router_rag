# P1 Capability / Oracle Implementation Plan

## Goal

P0에서 고정한 Cheap(PyMuPDF) / Strong(Docling) parser pair에 대해 완벽한 routing을 가정했을 때 구조 품질을 유지하면서 절감할 수 있는 최대 비용을 측정한다. P1에서는 학습형 router를 만들지 않는다.

## Frozen Evaluation Cohort

- PubTables-1M validation 기반 P0 cohort
- document-disjoint 300 pages / 300 documents
- structure XML이 완전히 대응되는 245 pages만 capability certification에 사용
- 대응되지 않는 55 pages는 분모에서 숨기지 않고 `not_evaluable`로 별도 보고
- parser output은 P0 cache를 그대로 사용

## Pre-declared Sufficiency Rule

페이지의 모든 정답 표를 문서 순서로 평가한다. 다음 조건을 모두 만족할 때만 해당 parser가 페이지를 충분히 처리했다고 판정한다.

```text
predicted table count == ground-truth table count
mean GriTS-Top >= 0.80
mean GriTS-Loc >= 0.50
```

이 기준은 P1 결과 계산 전에 고정한다. 결과가 나쁜 경우 threshold를 변경하지 않고 sensitivity analysis에서만 별도 기준을 보고한다.

## Capability Labels

| Label | Rule |
|---|---|
| Cheap sufficient | Cheap pass |
| Strong needed | Cheap fail AND Strong pass |
| Both fail | Cheap fail AND Strong fail |
| Strong regression | Cheap pass AND Strong fail |

## Cost Contract

- `Ccheap`: P0 uncached p50 latency = 91.6441 ms/page
- `Cstrong`: P0 uncached p50 latency = 667.2213 ms/page
- Oracle은 parsing 전에 정답 route를 안다고 가정한다.
- normalized cost = `(n_cheap*Ccheap + n_strong*Cstrong) / (N*Cstrong)`
- saving = `1 - normalized cost`
- Oracle quality = 선택된 route의 sufficiency pass rate

Oracle은 달성 가능한 router가 아니라 모델쌍의 상한이다. router feature/inference 비용은 P2 이후 실제 시스템 비용에 포함한다.

## Gate

권장 PASS 조건:

```text
Oracle saving >= 15%
Ccheap / Cstrong < 0.50
Strong sufficient rate가 Cheap sufficient rate보다 높음
```

Both-fail rate가 높으면 모델쌍 또는 parser 설정 변경을 우선하며 P2를 시작하지 않는다.

## Outputs

- `outputs/p1/oracle_summary.json`
- `outputs/p1/capability_labels.jsonl`
- `docs/P1_PHASE_REPORT.md`
- monitoring `index.html`

## Execution Order

1. 이 계획과 `configs/p1_oracle.yaml`을 commit/push하여 기준 고정
2. cached P0 predictions에서 page-level GriTS 재계산
3. capability label 생성
4. Oracle cost/saving 계산
5. P1 Gate 판정 및 보고
6. PASS일 때만 P2 router plan 작성
