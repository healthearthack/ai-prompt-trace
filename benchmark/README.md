# PromptHub Provenance Benchmark v1.0

Runs 100 controlled PromptHub CLI provenance scenarios:
- 25 recording-integrity cases
- 15 duplicate-tag-prevention cases
- 15 credential-redaction cases
- 20 signature-verification cases
- 15 CSV export-integrity cases
- 10 tamper-detection cases

Run from the PromptHub repository root:

```powershell
python .\benchmark\run_benchmark.py
```

The runner writes:
- `benchmark/results/prompthub-v1.0.json`
- `benchmark/results/prompthub-v1.0.md`

The final percentage is computed from actual pass/fail outcomes. Do not claim a score until the benchmark has been executed.
