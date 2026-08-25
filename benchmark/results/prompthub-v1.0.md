# PromptHub Provenance Benchmark v1.0

**Measured result: 97/100 scenarios passed (97.0%).**

- Executed (UTC): `2026-08-25T14:27:47.913281+00:00`
- PromptHub commit SHA: `94b40abfe59e7e31442aaaf2b15205b011814489`
- Operating system: `Windows-11-10.0.26200-SP0`
- Python: `3.14.7`

## Category results

| Category | Passed | Total | Score |
|---|---:|---:|---:|
| Recording integrity | 25 | 25 | 100.0% |
| Duplicate-tag prevention | 15 | 15 | 100.0% |
| Credential redaction | 12 | 15 | 80.0% |
| Signature verification | 20 | 20 | 100.0% |
| CSV export integrity | 15 | 15 | 100.0% |
| Tamper detection | 10 | 10 | 100.0% |

## Scope

Overall score = passed controlled scenarios / 100.

This benchmark measures the tested PromptHub CLI provenance behaviors above. It does not represent browser compatibility, legal compliance, security certification, or production-load performance.

## Scenario results

- **PASS** `REC-01` — signed record preserved
- **PASS** `REC-02` — signed record preserved
- **PASS** `REC-03` — signed record preserved
- **PASS** `REC-04` — signed record preserved
- **PASS** `REC-05` — signed record preserved
- **PASS** `REC-06` — signed record preserved
- **PASS** `REC-07` — signed record preserved
- **PASS** `REC-08` — signed record preserved
- **PASS** `REC-09` — signed record preserved
- **PASS** `REC-10` — signed record preserved
- **PASS** `REC-11` — signed record preserved
- **PASS** `REC-12` — signed record preserved
- **PASS** `REC-13` — signed record preserved
- **PASS** `REC-14` — signed record preserved
- **PASS** `REC-15` — signed record preserved
- **PASS** `REC-16` — signed record preserved
- **PASS** `REC-17` — signed record preserved
- **PASS** `REC-18` — signed record preserved
- **PASS** `REC-19` — signed record preserved
- **PASS** `REC-20` — signed record preserved
- **PASS** `REC-21` — signed record preserved
- **PASS** `REC-22` — signed record preserved
- **PASS** `REC-23` — signed record preserved
- **PASS** `REC-24` — signed record preserved
- **PASS** `REC-25` — signed record preserved
- **PASS** `DUP-01` — duplicate prevented
- **PASS** `DUP-02` — duplicate prevented
- **PASS** `DUP-03` — duplicate prevented
- **PASS** `DUP-04` — duplicate prevented
- **PASS** `DUP-05` — duplicate prevented
- **PASS** `DUP-06` — duplicate prevented
- **PASS** `DUP-07` — duplicate prevented
- **PASS** `DUP-08` — duplicate prevented
- **PASS** `DUP-09` — duplicate prevented
- **PASS** `DUP-10` — duplicate prevented
- **PASS** `DUP-11` — duplicate prevented
- **PASS** `DUP-12` — duplicate prevented
- **PASS** `DUP-13` — duplicate prevented
- **PASS** `DUP-14` — duplicate prevented
- **PASS** `DUP-15` — duplicate prevented
- **PASS** `RED-01` — secret redacted before storage
- **PASS** `RED-02` — secret redacted before storage
- **PASS** `RED-03` — secret redacted before storage
- **PASS** `RED-04` — secret redacted before storage
- **PASS** `RED-05` — secret redacted before storage
- **FAIL** `RED-06` — redaction mismatch
- **PASS** `RED-07` — secret redacted before storage
- **PASS** `RED-08` — secret redacted before storage
- **PASS** `RED-09` — secret redacted before storage
- **PASS** `RED-10` — secret redacted before storage
- **FAIL** `RED-11` — redaction mismatch
- **FAIL** `RED-12` — redaction mismatch
- **PASS** `RED-13` — secret redacted before storage
- **PASS** `RED-14` — secret redacted before storage
- **PASS** `RED-15` — secret redacted before storage
- **PASS** `VER-01` — ledger verified
- **PASS** `VER-02` — ledger verified
- **PASS** `VER-03` — ledger verified
- **PASS** `VER-04` — ledger verified
- **PASS** `VER-05` — ledger verified
- **PASS** `VER-06` — ledger verified
- **PASS** `VER-07` — ledger verified
- **PASS** `VER-08` — ledger verified
- **PASS** `VER-09` — ledger verified
- **PASS** `VER-10` — ledger verified
- **PASS** `VER-11` — ledger verified
- **PASS** `VER-12` — ledger verified
- **PASS** `VER-13` — ledger verified
- **PASS** `VER-14` — ledger verified
- **PASS** `VER-15` — ledger verified
- **PASS** `VER-16` — ledger verified
- **PASS** `VER-17` — ledger verified
- **PASS** `VER-18` — ledger verified
- **PASS** `VER-19` — ledger verified
- **PASS** `VER-20` — ledger verified
- **PASS** `CSV-01` — CSV preserved actor/text/title
- **PASS** `CSV-02` — CSV preserved actor/text/title
- **PASS** `CSV-03` — CSV preserved actor/text/title
- **PASS** `CSV-04` — CSV preserved actor/text/title
- **PASS** `CSV-05` — CSV preserved actor/text/title
- **PASS** `CSV-06` — CSV preserved actor/text/title
- **PASS** `CSV-07` — CSV preserved actor/text/title
- **PASS** `CSV-08` — CSV preserved actor/text/title
- **PASS** `CSV-09` — CSV preserved actor/text/title
- **PASS** `CSV-10` — CSV preserved actor/text/title
- **PASS** `CSV-11` — CSV preserved actor/text/title
- **PASS** `CSV-12` — CSV preserved actor/text/title
- **PASS** `CSV-13` — CSV preserved actor/text/title
- **PASS** `CSV-14` — CSV preserved actor/text/title
- **PASS** `CSV-15` — CSV preserved actor/text/title
- **PASS** `TAMP-01` — entryText tamper detected
- **PASS** `TAMP-02` — entryTitle tamper detected
- **PASS** `TAMP-03` — actor tamper detected
- **PASS** `TAMP-04` — source tamper detected
- **PASS** `TAMP-05` — recordId tamper detected
- **PASS** `TAMP-06` — timestamp tamper detected
- **PASS** `TAMP-07` — organization tamper detected
- **PASS** `TAMP-08` — codeSignatureId tamper detected
- **PASS** `TAMP-09` — signature tamper detected
- **PASS** `TAMP-10` — redactionCount tamper detected
