#!/usr/bin/env python3
"""Local Prompt Trace Model Context Protocol server.

The server uses newline-delimited JSON-RPC over standard input/output so the
ChatGPT desktop app, Codex command-line interface, and IDE extension can launch
it without a network listener.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from prompt_trace import VERSION, append_entry, public_entry, read_entries, status_data

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "prompt-trace", "version": VERSION}
INSTRUCTIONS = (
    "Prompt Trace records explicitly submitted activity, never raw keystrokes. "
    "When the user asks to sign or record a completed prompt, command, or work "
    "activity, call prompt_trace_record_submission before continuing. Return the "
    "visible stamp and record ID. Use prompt_trace_recent only when the user asks "
    "to inspect their ledger."
)

TOOLS = [
    {
        "name": "prompt_trace_status",
        "description": "Read local Prompt Trace identity, stamp, connection status, and signed-entry count.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "prompt_trace_record_submission",
        "description": (
            "Sign and record one completed user-submitted prompt, terminal command, "
            "or programming activity. This is explicit submission capture, not keylogging."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "minLength": 1, "maxLength": 200000},
                "source": {"type": "string", "default": "chatgpt-desktop:mcp"},
                "activityType": {
                    "type": "string",
                    "enum": ["prompt", "command", "programming-input", "other"],
                    "default": "prompt",
                },
            },
            "required": ["text"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "prompt_trace_recent",
        "description": "Read the newest signed Prompt Trace ledger entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                "includeText": {"type": "boolean", "default": True},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
]


def text_result(data: Any) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}],
        "structuredContent": data,
        "isError": False,
    }


def error_result(message: str) -> dict:
    return {
        "content": [{"type": "text", "text": message}],
        "isError": True,
    }


def call_tool(name: str, arguments: dict) -> dict:
    if name == "prompt_trace_status":
        return text_result(status_data())
    if name == "prompt_trace_recent":
        limit = arguments.get("limit", 20)
        include_text = arguments.get("includeText", True)
        return text_result([
            public_entry(event, include_text=include_text)
            for event in read_entries(limit)
        ])
    if name == "prompt_trace_record_submission":
        text = arguments.get("text")
        if not isinstance(text, str) or not text.strip():
            return error_result("text must be a non-empty string")
        source = arguments.get("source", "chatgpt-desktop:mcp")
        activity_type = arguments.get("activityType", "prompt")
        event = append_entry(
            text,
            str(source),
            metadata={"activityType": activity_type, "integration": "mcp"},
            quiet=True,
        )
        result = public_entry(event)
        result["stamp"] = status_data()["stamp"]
        return text_result(result)
    return error_result(f"Unknown tool: {name}")


def handle(request: dict) -> dict | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        result = {
            "protocolVersion": request.get("params", {}).get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": INSTRUCTIONS,
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = request.get("params", {})
        result = call_tool(str(params.get("name", "")), params.get("arguments") or {})
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = handle(json.loads(line))
        except Exception as error:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(error)},
            }
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":"), ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
