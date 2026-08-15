# Prompt Trace v3.1.0

## Critical provenance correction

Earlier v3 builds displayed `[PT:AUTHOR]` beside the composer but did not preserve it in the transmitted message. v3.1.0 inserts the title at the submission boundary using native input behavior, so the tag remains in Gemini, ChatGPT, Claude, and Copilot conversation history and matches the locally signed ledger.

- Supports Enter-key, form, and recognized send-button submissions.
- Avoids duplicate tags when an entry is already titled.
- Preserves the 1–8-character alphanumeric author-ID rule.
- Retains debounced page observation for dynamic applications.
- Keeps password fields excluded and sensitive-value redaction active.
