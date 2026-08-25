# PromptHub Provenance Benchmark v1.0

## Status

**PENDING EXECUTION**

No reliability percentage is claimed until all 100 scenarios have been executed.

## Benchmark design

| Category | Planned scenarios | Passed |
|---|---:|---:|
| Capture accuracy | 25 | Pending |
| Duplicate prevention | 15 | Pending |
| Password-field exclusion | 15 | Pending |
| Provenance verification | 20 | Pending |
| Export integrity | 15 | Pending |
| Tamper detection | 10 | Pending |
| **Total** | **100** | **Pending** |

## Scoring

Overall reliability is calculated as:

`passed scenarios / 100 × 100`

Example only:

`94 passed / 100 scenarios = 94.0%`

Example scores are not benchmark results.

## Reproducibility requirements

The completed benchmark record must include:

- PromptHub release/version
- Git commit SHA
- operating system
- runtime versions
- all 100 scenario identifiers
- pass/fail result for every scenario
- category totals
- overall score
- execution date

## Intended durable metric

Once executed, this benchmark may support a statement such as:

> PromptHub v1 achieved X% provenance reliability across 100 controlled workflow scenarios.

The value of X must come directly from the recorded benchmark results.
