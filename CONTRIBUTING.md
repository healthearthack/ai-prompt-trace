# Contributing to Prompt Trace

Thank you for helping make authorship provenance clear, local-first, and usable.

## Start here

1. Fork the repository and create a focused branch.
2. Install Python 3.10+ and OpenSSH (`ssh-keygen`).
3. Run `python -m unittest discover -s tests -v` before and after your change.
4. Keep capture explicit. Never add keylogging, password-field access, clipboard collection, hidden network transmission, or silent enrollment.
5. Add tests and documentation for behavior changes.
6. Open a pull request explaining the problem, safety impact, and test evidence.

## Identity rules

- IDs contain 1–8 ASCII letters or numbers and normalize to uppercase.
- `AC` is permanently claimed and must never be offered as a default or reassigned.
- Globally claimed IDs are permanent; credential expiration never releases an ID.
- A registry rejects a different public key attempting to claim an active ID.
- Display names are separate metadata and may contain spaces.
- Private device keys never leave the device through Prompt Trace.

## Help wanted: native setup application

We want to evolve the terminal wizard into an accessible native app. A strong first release should:

- explain capture and redaction before consent;
- collect a display name and validate a 1–8-character author ID;
- support local enrollment and enterprise-issued IDs/tokens;
- configure the browser native host with clear browser/profile guidance;
- show connection status, ledger location, pause/resume, verify, and CSV export;
- preserve local-only private keys and avoid logging sensitive setup values;
- meet keyboard, screen-reader, contrast, and error-recovery requirements;
- ship as a signed Windows installer first, with macOS/Linux tracked separately.

Comment on the `help wanted` issue before starting a large implementation so contributors can coordinate.

## Universal Integration

Universal Integration means consistent authorship provenance across supported
web, terminal, browser, local-client, and programming-input adapters. It does
not mean system-wide keystroke surveillance.

Every adapter must:

- create or preserve the visible `[PT:AUTHOR]` stamp at submission;
- record completed submitted activity in the canonical signed ledger;
- identify its source and integration type;
- redact detected credentials before hashing, signing, or storage;
- exclude password fields, unsubmitted keystrokes, clipboard contents, output,
  and unrelated files;
- expose pause, status, verification, and failure states;
- add positive integration and negative privacy-boundary tests.

Browser adapters must allow reactive editor state to settle before send.
Terminal adapters must record completed history entries rather than raw key
events. MCP adapters must be described honestly: they can record and return a
stamp, but cannot rewrite text already submitted through a host composer.

## Setup wizard contributions

Wizard changes must install the same ledger and integration entry points without
silently enrolling a user. Preserve an explicit capture notice and affirmative
consent. Browser-native-host and MCP registration must display what they change
and retain a reversible uninstall path.

## Pull-request checklist

- [ ] The change is reviewable and focused.
- [ ] Tests pass locally and new behavior has tests.
- [ ] Consent, privacy, and security effects are documented.
- [ ] User-facing instructions and screenshots are current.
- [ ] No secrets, private ledgers, generated identities, or personal registry files are committed.

Contributions are licensed under the repository's MIT License.
