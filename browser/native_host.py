#!/usr/bin/env python3
"""Chrome Native Messaging bridge for the local Prompt Trace ledger."""

import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from prompt_trace import append_entry, load_config


def read_message():
    length = sys.stdin.buffer.read(4)
    if not length:
        return None
    size = struct.unpack("<I", length)[0]
    return json.loads(sys.stdin.buffer.read(size).decode("utf-8"))


def write_message(message):
    payload = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(payload)))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


while True:
    request = read_message()
    if request is None:
        break
    try:
        if request.get("type") == "status":
            config = load_config()
            write_message({"ok": True, "actor": config["actor"], "organization": config.get("currentOrganization"), "codeSignatureId": config["codeSignatureId"], "redaction": True})
        elif request.get("type") == "record":
            event = append_entry(
                str(request.get("text", "")),
                str(request.get("source", "browser")),
                metadata={"pageOrigin": request.get("pageOrigin", "")},
                quiet=True,
            )
            write_message({"ok": True, "recordId": event["recordId"], "codeSignatureId": event["codeSignatureId"]})
        else:
            raise ValueError("Unsupported message")
    except Exception as error:
        write_message({"ok": False, "error": str(error)})
