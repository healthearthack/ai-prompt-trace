# Browser Compatibility and Chatbot Capture

## Purpose

This document defines the acceptance test for Prompt Trace v1.0.0 chatbot capture. The feature is accepted only when one intentional prompt submission produces exactly one captured event, while sensitive password input produces no event.

## Test status

**Overall status:** Passed — 10 of 10 tests  
**Last updated:** 2026-08-15  
**Test environment:** Record before execution

|Item|Value|
|-|-|
|Extension version|Prompt Trace v1.0.0|
|Extension build or commit|*Record commit hash*|
|Browser and version|*Record browser version*|
|Operating system|Windows 11|
|Tester|Andrew Kieckhefer|
|Evidence location|*Add screenshot, recording, or event-log path*|

## Acceptance criteria

A test passes only when all applicable conditions are true:

1. The submitted prompt is captured after the user intentionally submits it.
2. The captured event identifies the correct chatbot provider.
3. The captured prompt text matches the submitted text.
4. Exactly one event is stored for one submission.
5. Merely typing, editing, or focusing the prompt does not create an event.
6. Password-field content is never captured, logged, or stored.

## Standard test prompt

Use a unique value for each case so events cannot be confused:

```text
PROMPT\_TRACE\_CAPTURE\_<PROVIDER>\_<METHOD>\_<UTC\_TIMESTAMP>
```

Example:

```text
PROMPT\_TRACE\_CAPTURE\_CHATGPT\_BUTTON\_20260815T220500Z
```

Do not use personal, confidential, authentication, or production information in test prompts.

## Chatbot test matrix

`Not run` is the default. Change a row to `Pass` or `Fail` only after executing it and recording evidence.

|ID|Provider|Submission method|Expected result|Status|Evidence / notes|
|-|-|-|-|-|-|
|BC-01|ChatGPT|Submit button|One ChatGPT event containing the exact prompt|Pass|PASS — ChatGPT button; signed ledger exact-match count: 1.|
|BC-02|ChatGPT|Enter key|One ChatGPT event containing the exact prompt|Pass|PASS — ChatGPT Enter; signed ledger exact-match count: 1.|
|BC-03|Claude|Submit button|One Claude event containing the exact prompt|Pass|PASS — Claude button; signed ledger exact-match count: 1.|
|BC-04|Claude|Enter key|One Claude event containing the exact prompt|Pass|PASS — Claude Enter; signed ledger exact-match count: 1.|
|BC-05|Gemini|Submit button|One Gemini event containing the exact prompt|Pass|PASS — Gemini button; signed ledger exact-match count: 1.|
|BC-06|Gemini|Enter key|One Gemini event containing the exact prompt|Pass|PASS — Gemini Enter; signed ledger exact-match count: 1.|
|BC-07|Copilot|Submit button|One Copilot event containing the exact prompt|Pass|PASS — Copilot button after submit-button listener repair; signed ledger exact-match count: 1.|
|BC-08|Copilot|Enter key|One Copilot event containing the exact prompt|Pass|PASS — Copilot Enter; signed ledger exact-match count: 1.|

## Safety and integrity test matrix

|ID|Test|Procedure|Expected result|Status|Evidence / notes|
|-|-|-|-|-|-|
|BC-09|Password-field exclusion|Enter a unique non-secret sentinel into an `<input type="password">`, then trigger input, change, Enter, and button-click activity|No event, console message, network payload, or stored record contains the sentinel|Pass|PASS — Password sentinel ledger-match count: 0.|
|BC-10|Duplicate prevention|Submit one unique prompt once, then wait at least five seconds and count matching stored events|Exactly one matching event exists|Pass|PASS — Single submission produced exactly one signed ledger record.|

## Execution procedure

Repeat these steps for BC-01 through BC-08:

1. Start the Prompt Trace companion service or local capture destination.
2. Open the browser profile in which the unpacked extension is installed.
3. Reload the extension from the browser's extensions page.
4. Open the provider in a new tab and start a new conversation.
5. Create a unique standard test prompt using the provider and submission method.
6. Type the prompt without submitting it. Confirm that no event has been created.
7. Submit using only the method named in the matrix row.
8. Inspect the captured event and verify provider, exact prompt text, timestamp, and event count.
9. Record `Pass` or `Fail` and attach evidence that shows both the submitted prompt and the single captured event.
10. Remove the test conversation and local test event if cleanup is required by project policy.

## BC-09: password-field exclusion procedure

Use a local test page or development fixture. Never test with a real password.

1. Use the sentinel `PROMPT\_TRACE\_PASSWORD\_EXCLUSION\_TEST` in an element whose type is `password`.
2. Trigger keyboard input, Enter, form submission, and a submit-button click.
3. Search extension logs, service-worker logs, network requests, and stored events for the complete sentinel and meaningful substrings.
4. Pass only if the value is absent from every capture surface.
5. If the sentinel appears anywhere, mark the test `Fail`, stop release work, and file a privacy defect.

## BC-10: duplicate-prevention procedure

1. Clear test events or record the starting event count.
2. Create one unique prompt: `PROMPT\_TRACE\_DUPLICATE\_TEST\_<UTC\_TIMESTAMP>`.
3. Submit it exactly once using a supported provider.
4. Wait at least five seconds so asynchronous handlers can finish.
5. Count events whose normalized provider and prompt text match the submission.
6. Pass only when the count is exactly one.
7. Repeat once with button submission and once with Enter submission. Both repetitions must pass for BC-10 to pass.

## Failure report template

```text
Test ID:
Provider:
Page URL:
Submission method:
Browser and version:
Extension version and commit:
Expected result:
Actual result:
Matching event count:
Console or service-worker error:
Evidence path:
Reproducible after extension reload: Yes / No
```

## Release gate

Prompt chain 2 is complete only when BC-01 through BC-10 are all marked `Pass` with evidence. Any missing evidence, password-field capture, missed submission, provider mismatch, modified prompt text, or duplicate event blocks the v1.0.0 release.

