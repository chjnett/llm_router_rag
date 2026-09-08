# P1 Cheap Parser Repair Report

## Verdict

**All three zero-download PyMuPDF variants failed the frozen P1 Gate.** PyMuPDF option tuning is not sufficient; P2 remains locked.

| Cheap candidate | p50 | Cheap sufficient | Oracle saving | Gate |
|---|---:|---:|---:|---|
| Existing default | 91.64 ms | 11.43% | 9.86% | FAIL |
| union + refine | 90.94 ms | 10.61% | 9.17% | FAIL |
| text/text | 282.64 ms | 0.00% | 0.00% | FAIL |
| raw lines | 94.45 ms | 11.43% | 9.81% | FAIL |

The text strategy achieved table-count proxy 0.931, but no page passed the exact-count plus GriTS-Top/Loc contract. This demonstrates why detection-count proxy must not be substituted for structural quality.

## Next Decision

Stop tuning PyMuPDF heuristics. Screen a genuinely different lightweight table parser on a small frozen preflight subset, then run all 300 pages only if it shows structural improvement while keeping Cheap/Strong p50 below 0.50. The Strong both-fail problem remains a separate repair track.

## Independent Parser Preflight

`pdfplumber 0.11.10` line strategy completed 20/20 pages with p50 95.97 ms and p95 158.73 ms, but table-count proxy was only 0.183. It showed no quality-improvement signal, so the pre-declared expansion rule stopped the 300-page run. Four malformed PDF color-operator warnings were observed without page failures.
