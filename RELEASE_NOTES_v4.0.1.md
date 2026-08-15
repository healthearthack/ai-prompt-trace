# Prompt Trace v4.0.1

Version 4.0.1 focuses only on reliable submitted-activity integration.

## Fixed

- Browser submission waits for modern chatbot editor state to accept the visible
  Prompt Trace stamp before the site's send action proceeds.
- ChatGPT, Claude, Gemini, and Copilot receive the author stamp as transmitted
  message text when their supported Chromium composer is used.
- One tested formatter prevents duplicate personal and organization stamps.

## Added

- A local Model Context Protocol (MCP) server for ChatGPT desktop, Codex
  command-line interface, and supported integrated development environments.
- MCP tools for status, explicit submitted-activity recording, and recent
  signed-entry inspection.
- A `prompt-trace recent` command.
- Automated MCP protocol and browser-stamp tests.
- Universal Integration contribution guidance.

## Capture and security boundary

Prompt Trace signs completed activity at the submission boundary. It does not
install a system-wide keyboard hook and does not capture unsubmitted keystrokes,
password fields, clipboard contents, command output, or arbitrary files.

The browser extension can transmit the visible author stamp as part of a
supported web-chat message. A desktop MCP client can call Prompt Trace tools and
display the returned stamp and record identifier, but MCP does not rewrite the
user's already-submitted desktop composer text.
