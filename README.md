# Prompt Trace

### Cryptographically signed breadcrumbs for AI-assisted work

Prompt Trace is a consent-first provenance layer that follows your terminal workflow and leaves verifiable evidence of where AI-assisted work happened—without publishing the prompts, commands, files, or outputs that produced it.

```text
[PT] PS C:\work\ai-productivity-ledger> git status
```

The small `[PT]` marker is the visible promise: tracing is active. After a command completes, Prompt Trace records a minimal project checkpoint, signs it with the user’s local Ed25519 identity, and links it to the previous checkpoint. The resulting ledger can answer **who participated, where, when, and against which Git state** while keeping the underlying work private.

> **Developer preview:** the Windows terminal tracer, local signing identity, append-only ledger, consent gate, and end-to-end verification are working. Browser capture, encrypted prompt vaults, hardware-backed keys, packaged binaries, and independent security review remain future work.

## The idea

Git records how code changed. Prompt Trace records the provenance surrounding AI-assisted work.

Think of it as a trail keeper’s field journal:

- A **checkpoint** is a small cairn marking that a participant passed through a workflow.
- The **private key** is the keeper’s stamp and never enters the journal.
- The **signature** is the seal proving who stamped the page.
- The **hash chain** binds every page to the one before it.
- The visible **`[PT]` marker** is the porch light showing that the keeper is awake.

This metaphor also appears in the code comments so maintainers can understand the security model without translating a wall of cryptographic vocabulary.

## What a breadcrumb contains

```json
{
  "schema": "prompt-trace.breadcrumb.v1",
  "actor": "your-name",
  "action": "command-completed",
  "workflow": "powershell",
  "path": "C:\\work\\project",
  "project": "project",
  "repository": "https://github.com/example/project.git",
  "branch": "main",
  "head": "abc123...",
  "commandHash": "sha256-fingerprint-or-null",
  "exitCode": 0,
  "previousHash": "prior-page-fingerprint",
  "publicKey": "ssh-ed25519 ...",
  "signature": "base64-encoded-sshsig"
}
```

### Recorded locally

- User-chosen actor identity and visible marker
- Timestamp and workflow name
- Working path and Git project context
- Repository remote, branch, and current commit
- Command exit code
- Optional one-way command hash
- Public key, previous-event hash, and signature

### Never recorded by default

- Raw commands or prompts
- Command or model output
- Keystrokes or clipboard contents
- Environment-variable values or credentials
- File contents
- Browser history

The command hash can later prove that disclosed text matches a checkpoint. It does not put that text in the ledger.

## Install on Windows

Requirements: Python, Git, Windows PowerShell, and OpenSSH `ssh-keygen`.

```powershell
git clone https://github.com/healthearthack/prompt-trace.git
cd prompt-trace
.\install.ps1 -Actor "your-name" -Marker "[PT]" -Capture command-hash
```

The installer displays the complete data scope and stops until the user types exactly:

```text
I CONSENT
```

Open a new PowerShell window after installation. The prompt will include the chosen marker:

```text
[PT] PS C:\your\project>
```

Each completed command boundary now creates one signed breadcrumb in:

```text
%LOCALAPPDATA%\PromptTrace\breadcrumbs.jsonl
```

### Choose the privacy scope

```powershell
# Project paths and workflow boundaries; no command fingerprint
.\install.ps1 -Actor "your-name" -Marker "[PT]" -Capture path-only

# Adds a one-way command fingerprint without storing the command
.\install.ps1 -Actor "your-name" -Marker "[PT]" -Capture command-hash
```

`-AcceptConsent` is available for reviewed organizational deployment scripts. Administrators remain responsible for obtaining the user’s informed consent.

## Prove it works

```powershell
prompt-trace status
Set-Location C:\path\to\your-project
git status
prompt-trace verify
```

Expected verification:

```text
Verified 2 signed breadcrumbs for your-name
```

Editing, deleting, or reordering a ledger entry breaks either its Ed25519 signature or the chain connecting it to neighboring entries.

## Mark an AI workflow explicitly

Agents and integrations can leave a named checkpoint without exposing task content:

```powershell
prompt-trace checkpoint `
  --workflow codex `
  --action ai-task-completed `
  --path $PWD
```

This is the integration point for Codex, local agents, CI jobs, browser companions, and future provider adapters.

## Architecture

```text
PowerShell prompt bell
        │
        ▼
Minimal workflow metadata ──► Canonical JSON
                                      │
                         local Ed25519 signature
                                      │
                                      ▼
                         Append-only JSONL ledger
                                      │
                                      ▼
                         Chain + signature verifier
```

The private key remains under `%LOCALAPPDATA%\PromptTrace`. Only the public key and detached signature enter a breadcrumb.

## Consent and control

- Installation does not imply consent.
- Tracing is visible in every instrumented prompt.
- The user chooses their actor identity, marker, and capture scope.
- Raw capture is unavailable in this release.
- Uninstallation removes the prompt helper without silently destroying provenance history.

```powershell
.\uninstall.ps1
```

The identity and signed ledger remain local after uninstall so evidence is not accidentally erased. Deleting them should be a separate deliberate action.

## Current security boundary

Prompt Trace proves that the holder of a local private key signed a particular breadcrumb and that the ledger order has not changed. It does not yet prove:

- That a human personally executed every underlying action
- That the workstation or private key was uncompromised
- That a path or repository name describes the work truthfully
- That undisclosed prompt text was safe or accurate
- That the ledger was continuously active between recorded checkpoints

Production hardening should add Windows Hello or TPM-backed identities, key rotation and revocation, encrypted optional prompt storage, timestamp authority integration, signed release artifacts, and independent security assessment.

## Test

```powershell
python -m unittest discover -s tests -v
```

The integration test creates a disposable identity, signs a real checkpoint, verifies the complete chain, and confirms that command text never enters the ledger.

## Roadmap

- Signed Windows installer and packaged CLI
- Browser companion with a persistent consent indicator
- Codex and agent lifecycle adapters
- Encrypted, separately consented prompt vault
- Git commit and pull-request attestations
- Public verification bundles
- Hardware-backed identity support
- Cross-platform shell hooks

## License

© 2026 ThePolka.Cloud contributors

Prompt Trace™ and its branding are trademarks of ThePolka.Cloud.
The source code is licensed under the [MIT License](LICENSE).
