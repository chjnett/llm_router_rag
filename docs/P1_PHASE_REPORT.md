# P1 Capability / Oracle Phase Report

## Verdict

**P1 Gate: FAIL. P2 router training remains locked.**

The frozen PyMuPDF/Docling pair can save at most **9.86%** under a zero-overhead oracle, below the pre-declared 15% target. The result does not reject capability-aware routing in general; it rejects advancing this parser pair to router training under the present sufficiency contract.

## Frozen Protocol

- Cohort: 300 document-disjoint PubTables-1M validation pages
- Evaluable: 245 pages; 55 pages lacked matching structure XML and were reported separately
- Sufficient only when all conditions hold:
  - predicted table count equals ground truth
  - mean GriTS-Top >= 0.80
  - mean GriTS-Loc >= 0.50
- Cost: P0 uncached p50 latency, Cheap 91.6441 ms and Strong 667.2213 ms
- Gate: oracle saving >= 15%, Cheap/Strong cost ratio < 0.50, Strong coverage > Cheap coverage

The criteria were committed before the calculation (`d67f35e`). They were not changed after observing the result.

## Results

| Measure | Result | Interpretation |
|---|---:|---|
| Cheap sufficient | 28/245 (11.43%) | Only these pages can use Cheap without violating the frozen rule |
| Strong sufficient | 143/245 (58.37%) | Strong improves coverage, but does not solve a large fraction |
| Strong needed | 123/245 (50.20%) | Cheap fails and Strong passes |
| Both fail | 94/245 (38.37%) | Neither parser satisfies the contract |
| Strong regression | 8/245 (3.27%) | Cheap passes while Strong fails |
| Either parser sufficient | 151/245 (61.63%) | Best achievable sufficiency with page-level oracle selection |
| Cheap/Strong cost ratio | 0.1374 | Cost separation passes the gate |
| Oracle normalized cost | 0.9014 | Includes Cheap for all 28 Cheap-pass pages, including 8 Strong regressions |
| Oracle saving | **9.86%** | Fails the 15% target |

The mutually exclusive label count called `cheap_sufficient` is 20 (both parsers pass). Total Cheap-pass coverage is 28 because it also includes the 8 Strong-regression pages.

## Diagnosis

The cost ratio is favorable, but Cheap coverage is too low. Even a perfect and free router sends 217 of 245 pages to Strong, limiting savings to 9.86%. More importantly, 94 pages fail both paths, so router optimization cannot repair the underlying extraction quality.

## Decision and Next Step

Do not train P2 classifiers and do not relax the primary threshold after seeing the result. Return to a controlled P1 model-pair screening:

1. improve or replace the Cheap path while preserving a large latency gap;
2. improve or replace the Strong path to reduce the 38.37% both-fail rate;
3. rerun the same frozen cohort and sufficiency rule;
4. advance to P2 only if the pre-declared gate passes.

Sensitivity analyses may be reported separately, but cannot replace this primary negative result.
