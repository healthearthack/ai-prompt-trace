# Prompt Trace metadata policy

Prompt Trace deliberately generates provenance metadata. Avoiding all metadata would make cross-device identity, verification, consent history, and collaborative accountability impossible.

## Central by default

- Permanent account and author identifiers
- Device identifier, public key fingerprint, state, and last-seen time
- Personal or organization workspace identifier
- Submission and receipt timestamps
- Source product, such as PowerShell or Gemini
- Entry hash and previous-record hash
- Code-signature identifier and signature
- Redaction status and count
- Consent notice version and granted/revoked times
- Verification time and security outcome

## Local by default

- Raw submitted prompt or terminal-command text
- Private signing keys
- Unsubmitted text and keystrokes
- Command output
- Clipboard and arbitrary file content
- Passwords, passcodes, tokens, and detected secrets

## Optional encrypted central content

Raw submitted text may be synchronized only when the workspace is configured as `full_content`, `retain_raw_content` is true, consent covers that scope, and the application supplies ciphertext plus a managed encryption-key reference. The database never accepts a raw-text column.

## Continuity

The permanent account timeline spans devices and employers. When raw employer content cannot travel, a signed cryptographic receipt remains in the continuity view according to policy. This proves that an attributed event existed without moving the employer's confidential text into a personal workspace.

## Cyber CV curation

Cyber CV selection is opt-in. Entries are excluded until the account owner includes them. Excluding an entry removes it from the rendered portfolio without mutating the signed source ledger. A future cryptographic-erasure workflow may destroy an entry-specific content key while preserving a signed deletion receipt.
