#!/usr/bin/env python3
"""Prompt Trace: consented, signed provenance breadcrumbs for local AI work."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import uuid

SCHEMA = "prompt-trace.breadcrumb.v1"
HOME = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home() / ".local")) / "PromptTrace"
CONFIG = HOME / "config.json"
LEDGER = HOME / "breadcrumbs.jsonl"
KEY = HOME / "identity_ed25519"


def run(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, capture_output=True, check=False)


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_config() -> dict:
    if not CONFIG.exists():
        raise SystemExit("Prompt Trace is not initialized. Run: prompt-trace init --actor YOUR_NAME")
    return json.loads(CONFIG.read_text(encoding="utf-8-sig"))


def git_context(path: pathlib.Path) -> dict:
    top = run("git", "-C", str(path), "rev-parse", "--show-toplevel")
    if top.returncode:
        return {"project": path.name, "repository": None, "branch": None, "head": None}
    root = pathlib.Path(top.stdout.strip())
    branch = run("git", "-C", str(root), "branch", "--show-current").stdout.strip() or None
    head = run("git", "-C", str(root), "rev-parse", "HEAD").stdout.strip() or None
    remote = run("git", "-C", str(root), "remote", "get-url", "origin").stdout.strip() or None
    return {"project": root.name, "repository": remote, "branch": branch, "head": head}


def sign(payload: bytes) -> str:
    with tempfile.TemporaryDirectory() as folder:
        message = pathlib.Path(folder) / "message.json"
        message.write_bytes(payload)
        result = run("ssh-keygen", "-Y", "sign", "-f", str(KEY), "-n", "prompt-trace", str(message))
        if result.returncode:
            raise SystemExit(f"Signing failed: {result.stderr.strip()}")
        return base64.b64encode((pathlib.Path(str(message) + ".sig")).read_bytes()).decode()


def init_identity(actor: str, marker: str, capture: str, consent: bool) -> None:
    if not consent:
        raise SystemExit("Consent required. Review the data notice, then initialize with --consent.")
    HOME.mkdir(parents=True, exist_ok=True)
    if not KEY.exists():
        result = run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"prompt-trace:{actor}", "-f", str(KEY))
        if result.returncode:
            raise SystemExit(f"Key creation failed: {result.stderr.strip()}")
    public_key = pathlib.Path(str(KEY) + ".pub").read_text(encoding="utf-8").strip()
    CONFIG.write_text(json.dumps({"actor": actor, "publicKey": public_key, "marker": marker, "capture": capture, "rawCapture": False, "consentVersion": "local-metadata-v1", "consentedAt": int(time.time())}, indent=2), encoding="utf-8")
    print(f"Prompt Trace initialized for {actor}\nPublic identity: {public_key}")


def checkpoint(args: argparse.Namespace) -> None:
    config = load_config()
    path = pathlib.Path(args.path or os.getcwd()).resolve()
    context = git_context(path)
    event = {
        "schema": SCHEMA,
        "id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "actor": config["actor"],
        "action": args.action,
        "workflow": args.workflow or "terminal",
        "path": str(path),
        "project": context["project"],
        "repository": context["repository"],
        "branch": context["branch"],
        "head": context["head"],
        "commandHash": args.command_hash,
        "exitCode": args.exit_code,
        "publicKey": config["publicKey"],
        "previousHash": None,
    }
    if LEDGER.exists():
        lines = [line for line in LEDGER.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if lines:
            event["previousHash"] = hashlib.sha256(lines[-1].encode()).hexdigest()
    event["signature"] = sign(canonical(event))
    with LEDGER.open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(event, separators=(",", ":")) + "\n")
    if not args.quiet:
        print(f"PT signed {context['project']} | {args.workflow or 'terminal'} | {event['id'][:8]}")


def verify() -> None:
    config = load_config()
    if not LEDGER.exists():
        raise SystemExit("No breadcrumbs found")
    lines = [line for line in LEDGER.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    previous = None
    with tempfile.TemporaryDirectory() as folder:
        allowed = pathlib.Path(folder) / "allowed_signers"
        allowed.write_text(f"{config['actor']} {config['publicKey']}\n", encoding="utf-8")
        for index, line in enumerate(lines, 1):
            event = json.loads(line)
            signature = base64.b64decode(event.pop("signature"))
            if event.get("previousHash") != previous:
                raise SystemExit(f"Broken chain at breadcrumb {index}")
            sig_file = pathlib.Path(folder) / "event.sig"
            sig_file.write_bytes(signature)
            result = run("ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I", config["actor"], "-n", "prompt-trace", "-s", str(sig_file), input_text=canonical(event).decode())
            if result.returncode:
                raise SystemExit(f"Invalid signature at breadcrumb {index}: {result.stderr.strip()}")
            previous = hashlib.sha256(line.encode()).hexdigest()
    print(f"Verified {len(lines)} signed breadcrumbs for {config['actor']}")


def status() -> None:
    config = load_config()
    count = len(LEDGER.read_text(encoding="utf-8-sig").splitlines()) if LEDGER.exists() else 0
    print(json.dumps({"enabled": True, "actor": config["actor"], "marker": config.get("marker", "PT"), "capture": config.get("capture", "command-hash"), "breadcrumbs": count, "ledger": str(LEDGER), "rawCapture": False}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="prompt-trace", description="Signed, privacy-preserving AI-work provenance")
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--actor", required=True)
    initialize.add_argument("--marker", default="PT")
    initialize.add_argument("--capture", choices=("path-only", "command-hash"), default="command-hash")
    initialize.add_argument("--consent", action="store_true")
    trace = commands.add_parser("checkpoint")
    trace.add_argument("--path")
    trace.add_argument("--action", default="command-completed")
    trace.add_argument("--workflow")
    trace.add_argument("--command-hash")
    trace.add_argument("--exit-code", type=int)
    trace.add_argument("--quiet", action="store_true")
    commands.add_parser("verify")
    commands.add_parser("status")
    args = parser.parse_args()
    if args.command == "init": init_identity(args.actor, args.marker, args.capture, args.consent)
    elif args.command == "checkpoint": checkpoint(args)
    elif args.command == "verify": verify()
    elif args.command == "status": status()


if __name__ == "__main__":
    main()
