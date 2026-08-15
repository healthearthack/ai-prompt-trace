# Browser companion installation

1. Complete `setup-wizard.ps1` first.
2. Open the extensions page in the Chromium browser you use (`chrome://extensions`, `edge://extensions`, or `brave://extensions`), enable **Developer mode**, choose **Load unpacked**, and select `browser/extension`.
3. Copy the displayed 32-character extension ID.
4. Run `./browser/setup-native-host.ps1 -ExtensionId YOUR_ID`.
5. Restart that browser completely.

When connected, supported chatbot composers display your issued ID, such as `[PT:AC]`, immediately before the typing caret. At the submission boundary, v4.0.1 inserts that title into the actual transmitted prompt, waits for reactive editor state before activating send, and records the same title in the signed local ledger. The tag therefore remains visible in conversation history and collaborative chats.

Other contributors running v4.0.1 transmit their own enrolled IDs, so the same conversation can visibly distinguish `[PT:AC]`, `[PT:SARAPENN]`, and `[PT:JOESPACK]`. The platform must actually synchronize the conversation between those users. Validate authorship against signed ledger or manager-audit records; visible text alone can be manually imitated.

## Connection states

- `[PT:…]` — the content script is starting and waiting for extension status.
- `[PT:OFF]` — the native signing host did not connect.
- `[PT:AC]` (or your issued ID) — the browser, native host, and local identity are connected.

After updating the extension or native host, choose **Reload** on the browser's extensions page, close every window of that exact browser, reopen it, and hard-refresh the AI page. Disable older Prompt Trace copies so only v4.0.1 is active. The extension debounces dynamic-page scans and uses browser-native input events at submission so Gemini's editor model receives the persistent tag.

The extension operates only on ChatGPT, Claude, Gemini, and Microsoft Copilot. It captures text at the submit boundary, not every keystroke. The selectors are deliberately generic and may require maintenance as those sites change. Always verify important activity using `prompt-trace status`, `prompt-trace verify`, and a CSV export.
