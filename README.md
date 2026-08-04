# Prompt Trace Local

**Cryptographically signed breadcrumbs for AI-assisted work.**

Prompt Trace is a local provenance helper that follows the Windows PowerShell prompt like a spellcheck indicator. When enabled, a green `PT●` appears beside the command-line needle. Each completed command boundary leaves a signed breadcrumb containing the actor, timestamp, working path, project, Git repository, branch, commit, workflow, exit code, and a one-way command hash.

It does **not** store raw commands, prompt text, command output, keystrokes, clipboard contents, environment-variable values, file contents, or credentials. A hash can prove that disclosed text matches a prior event without publishing that text in the ledger.

## Install on Windows

Open PowerShell in this repository:

```powershell
.\install.ps1 -Actor "your-name" -Marker "I-WAS-HERE" -Capture command-hash
```

Open a new PowerShell window. The prompt becomes:

```text
I-WAS-HERE PS C:\your\project>
```

Every command completion adds a signed event to:

```text
%LOCALAPPDATA%\PromptTrace\breadcrumbs.jsonl
```

Every user chooses their own actor identity and visible marker. Use `-Capture path-only` to record workflow/path boundaries without even retaining a command hash. `command-hash` is the default and proves later-disclosed command text without storing it.

## Prove it works

```powershell
prompt-trace status
Set-Location C:\path\to\ai-productivity-ledger
git status
prompt-trace verify
```

The `git status` boundary produces a breadcrumb tied to that repository path, branch, and current commit. `verify` checks every Ed25519 signature and the append-only hash chain. Editing or reordering a breadcrumb causes verification to fail.

## Manual AI-work breadcrumb

Agents and integrations can add a named checkpoint without exposing content:

```powershell
prompt-trace checkpoint --workflow codex --action ai-task-completed --path $PWD
```

## Uninstall the helper

```powershell
.\uninstall.ps1
```

Uninstalling removes the PowerShell prompt hook but intentionally leaves the signed identity and ledger in LocalAppData. Delete those separately only if you intend to destroy the local provenance history.

## Security status

This developer release uses the operating system's OpenSSH Ed25519 implementation. The private key remains local and is never written into a breadcrumb. A production release should additionally support Windows Hello/TPM-backed keys, encrypted raw-prompt vaults as a separate opt-in feature, key rotation, revocation records, and third-party security review.
