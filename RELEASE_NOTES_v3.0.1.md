# Prompt Trace v3.0.1

- Introduces the hot-pink quill/caret identity and extension icons.
- Separates full display names from permanent 1–8-character alphanumeric author IDs.
- Records `AC` as founding reservation 1; it is never a reusable default.
- Adds managed company issuance with one-time enrollment tokens.
- Adds on-demand/latest audit CSVs, opt-in live sync, a live-author manager dashboard, and roster-level CSV merging.
- Adds the PostgreSQL model required for cross-company global uniqueness.
- Makes author IDs permanent while signing credentials expire after 100 years.
- Adds actual wizard screenshots, a full README, contributor guidance, and CI.
- Prevents the browser companion from rewriting controlled editors and debounces dynamic-page observation, fixing Gemini stability risk.

Worldwide uniqueness becomes enforceable only when the authoritative directory is deployed with verified claims. v3.0.1 local/shared registries enforce uniqueness within their configured registry.
