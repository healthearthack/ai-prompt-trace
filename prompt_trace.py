#!/usr/bin/env python3
"""Prompt Trace: consented author attribution for prompts and terminal entries."""

from __future__ import annotations

import argparse
import base64
import csv
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import re
import secrets
import shlex
import subprocess
import sys
import tempfile
import time
import uuid

SCHEMA = "prompt-trace.entry.v4"
VERSION = "4.0.1"
HOME = pathlib.Path(os.environ.get("PROMPT_TRACE_HOME") or (pathlib.Path(os.environ["LOCALAPPDATA"]) / "PromptTrace" if os.environ.get("LOCALAPPDATA") else pathlib.Path.home() / ".prompt-trace"))
CONFIG = HOME / "config.json"
LEDGER = HOME / "prompt-ledger.jsonl"
KEY = HOME / "identity_ed25519"
DEFAULT_REGISTRY = HOME / "actors.json"


def credential_expiry_iso() -> str:
    """Return the credential expiry exactly 100 calendar years from today."""
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        expiry = now.replace(year=now.year + 100)
    except ValueError:  # February 29 in a non-leap expiry year
        expiry = now.replace(year=now.year + 100, day=28)
    return expiry.isoformat().replace("+00:00", "Z")


def run(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, capture_output=True, check=False)


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


REDACTION_RULES = (
    ("private-key", re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", re.IGNORECASE | re.DOTALL)),
    ("authorization", re.compile(r"(?i)(\bAuthorization\s*:\s*(?:Bearer|Basic)\s+)[^\s,;]+")),
    ("credential-url", re.compile(r"(?i)(\b[a-z][a-z0-9+.-]*://[^\s:/@]+:)[^\s@/]+(@)")),
    ("named-secret-json", re.compile(r'''(?ix)(["'](?:password|passwd|pwd|passcode|pin|secret|api[-_]?key|access[-_]?token|auth[-_]?token|client[-_]?secret)["']\s*:\s*["'])[^"']*(["'])''')),
    ("named-secret", re.compile(r'''(?ix)(\b(?:--?|/)?(?:password|passwd|pwd|passcode|pin|secret|api[-_]?key|access[-_]?key|access[-_]?token|auth[-_]?token|client[-_]?secret)\b\s*(?:=|:)?\s*["']?)[^\s,"']+(["']?)''')),
    ("environment-secret", re.compile(r'''(?ix)(\b[A-Z0-9_]*(?:PASSWORD|PASSCODE|SECRET|TOKEN|API_KEY|ACCESS_KEY)[A-Z0-9_]*\s*=\s*["']?)[^\s,"']+(["']?)''')),
    ("provider-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})\b")),
)


def redact_sensitive(text: str) -> tuple[str, list[str]]:
    """Remove likely credentials before hashing, signing, or writing to disk."""
    redacted = text
    categories: list[str] = []
    for category, pattern in REDACTION_RULES:
        def replace(match: re.Match) -> str:
            categories.append(category)
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}****{match.group(2)}"
            if match.lastindex:
                return f"{match.group(1)}****"
            return "****"
        redacted = pattern.sub(replace, redacted)
    return redacted, categories


def load_json(path: pathlib.Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_config() -> dict:
    if not CONFIG.exists():
        raise SystemExit("Prompt Trace is not initialized. Run the setup wizard or use: prompt-trace init --actor YOURID --consent")
    return load_json(CONFIG, {})


def public_key_fingerprint(public_key: str) -> str:
    return sha256_text(public_key)[:16]


def validate_actor(actor: str) -> str:
    actor = actor.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{1,8}", actor):
        raise SystemExit("Author ID must contain 1-8 alphanumeric characters only")
    return actor


def validate_organization(organization: str) -> str:
    organization = organization.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{2,12}", organization):
        raise SystemExit("Organization code must contain 2-12 alphanumeric characters only")
    return organization


def reserve_actor(actor: str, public_key: str, registry_path: pathlib.Path, display_name: str = "", enrollment_token: str | None = None) -> None:
    """Reserve an author ID in one local or shared registry."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry = load_json(registry_path, {"schema": "prompt-trace.actors.v2", "mode": "open", "actors": {}})
    actors = registry.setdefault("actors", {})
    fingerprint = public_key_fingerprint(public_key)
    existing = actors.get(actor)
    if existing and existing.get("state") == "issued":
        supplied_hash = sha256_text(enrollment_token or "")
        if not hmac.compare_digest(existing.get("enrollmentTokenHash", ""), supplied_hash):
            raise SystemExit(f"Author ID {actor!r} requires the valid enterprise enrollment token")
        existing.update({
            "state": "active",
            "publicKey": public_key,
            "publicKeyFingerprint": fingerprint,
            "activatedAt": int(time.time()),
            "credentialExpiresAt": credential_expiry_iso(),
        })
        existing.pop("enrollmentTokenHash", None)
        registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        return
    if existing and existing.get("publicKeyFingerprint") != fingerprint:
        raise SystemExit(f"Author ID {actor!r} is already reserved by another identity in {registry_path}")
    if not existing:
        if registry.get("mode") == "managed":
            raise SystemExit(f"Author ID {actor!r} has not been issued by the enterprise registry administrator")
        actors[actor] = {
            "state": "active",
            "displayName": display_name or actor,
            "publicKey": public_key,
            "publicKeyFingerprint": fingerprint,
            "reservedAt": int(time.time()),
            "credentialExpiresAt": credential_expiry_iso(),
        }
        registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def issue_actor(actor: str, display_name: str, registry_value: str) -> None:
    actor = validate_actor(actor)
    display_name = display_name.strip()
    if not display_name or len(display_name) > 80:
        raise SystemExit("Display name must contain 1-80 characters")
    registry_path = pathlib.Path(registry_value).expanduser().resolve()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry = load_json(registry_path, {"schema": "prompt-trace.actors.v2", "mode": "managed", "actors": {}})
    if registry.get("mode") != "managed":
        raise SystemExit("Enterprise issuance requires a dedicated managed registry")
    actors = registry.setdefault("actors", {})
    if actor in actors:
        raise SystemExit(f"Author ID {actor!r} is already issued or active")
    token = secrets.token_urlsafe(24)
    actors[actor] = {
        "state": "issued",
        "displayName": display_name,
        "enrollmentTokenHash": sha256_text(token),
        "issuedAt": int(time.time()),
    }
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"Issued author ID: {actor}\nDisplay name: {display_name}\nOne-time enrollment token: {token}\nRegistry: {registry_path}")


def init_identity(actor: str, display_name: str | None, consent: bool, registry: str | None, enrollment_token: str | None) -> None:
    actor = validate_actor(actor)
    display_name = (display_name or actor).strip()
    if not display_name or len(display_name) > 80:
        raise SystemExit("Display name must contain 1-80 characters")
    if not consent:
        raise SystemExit("Consent required. Review the data notice, then add --consent.")
    HOME.mkdir(parents=True, exist_ok=True)
    current = load_json(CONFIG, {})
    if current and current.get("actor") != actor:
        raise SystemExit(f"This installation is already bound to author ID {current.get('actor')!r}")
    if not KEY.exists():
        result = run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"prompt-trace:{actor}", "-f", str(KEY))
        if result.returncode:
            raise SystemExit(f"Identity creation failed. OpenSSH ssh-keygen is required: {result.stderr.strip()}")
    public_key = pathlib.Path(str(KEY) + ".pub").read_text(encoding="utf-8").strip()
    registry_path = pathlib.Path(registry).expanduser().resolve() if registry else DEFAULT_REGISTRY
    reserve_actor(actor, public_key, registry_path, display_name, enrollment_token)
    code_signature_id = f"{actor}:{public_key_fingerprint(public_key)}"
    config = {
        "schema": "prompt-trace.config.v3",
        "actor": actor,
        "displayName": display_name,
        "codeSignatureId": code_signature_id,
        "publicKey": public_key,
        "registry": str(registry_path),
        "captureNotice": "Exact submitted entries are stored locally",
        "consentVersion": "exact-entry-v3",
        "consentedAt": int(time.time()),
        "credentialExpiresAt": credential_expiry_iso(),
    }
    CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Prompt Trace initialized\nDisplay name: {display_name}\nAuthor ID: {actor}\nCode signature: {code_signature_id}\nRegistry: {registry_path}")


def sign(payload: bytes) -> str:
    with tempfile.TemporaryDirectory() as folder:
        message = pathlib.Path(folder) / "entry.json"
        message.write_bytes(payload)
        result = run("ssh-keygen", "-Y", "sign", "-f", str(KEY), "-n", "prompt-trace", str(message))
        if result.returncode:
            raise SystemExit(f"Signing failed: {result.stderr.strip()}")
        return base64.b64encode(pathlib.Path(str(message) + ".sig").read_bytes()).decode("ascii")


def git_context(path: pathlib.Path) -> dict:
    top = run("git", "-C", str(path), "rev-parse", "--show-toplevel")
    if top.returncode:
        return {"project": path.name, "repository": None, "branch": None, "head": None}
    root = pathlib.Path(top.stdout.strip())
    return {
        "project": root.name,
        "repository": run("git", "-C", str(root), "remote", "get-url", "origin").stdout.strip() or None,
        "branch": run("git", "-C", str(root), "branch", "--show-current").stdout.strip() or None,
        "head": run("git", "-C", str(root), "rev-parse", "HEAD").stdout.strip() or None,
    }


def read_entry_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read().rstrip("\r\n")
    raise SystemExit("Provide --text or pipe the submitted entry through standard input")


def append_entry(text: str, source: str, path_value: str | None = None, metadata: dict | None = None, quiet: bool = False) -> dict:
    config = load_config()
    registry_path = pathlib.Path(config["registry"])
    reserve_actor(config["actor"], config["publicKey"], registry_path, config.get("displayName", config["actor"]))
    if not text.strip():
        raise SystemExit("Empty entries are not recorded")
    safe_text, redaction_categories = redact_sensitive(text)
    title_excerpt = " ".join(safe_text.split())[:72]
    organization = config.get("currentOrganization")
    author_prefix = f"[PT:{config['actor']} · {organization}]" if organization else f"[PT:{config['actor']}]"
    entry_title = title_excerpt if title_excerpt.startswith(author_prefix) else f"{author_prefix} {title_excerpt}"
    path = pathlib.Path(path_value or os.getcwd()).resolve()
    context = git_context(path)
    previous_hash = None
    if LEDGER.exists():
        lines = [line for line in LEDGER.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if lines:
            previous_hash = hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()
    event = {
        "schema": SCHEMA,
        "recordId": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "timestampIso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actor": config["actor"],
        "organization": organization,
        "codeSignatureId": config["codeSignatureId"],
        "entryTitle": entry_title,
        "source": source,
        "entryText": safe_text,
        "entryHash": sha256_text(safe_text),
        "redactionApplied": bool(redaction_categories),
        "redactionCount": len(redaction_categories),
        "redactionCategories": sorted(set(redaction_categories)),
        "path": str(path),
        "project": context["project"],
        "repository": context["repository"],
        "branch": context["branch"],
        "head": context["head"],
        "metadata": metadata or {},
        "previousHash": previous_hash,
        "publicKey": config["publicKey"],
    }
    event["signature"] = sign(canonical(event))
    with LEDGER.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n")
    if not quiet:
        print(f"Signed {event['recordId']} | {event['codeSignatureId']} | {source}")
    return event


def read_entries(limit: int = 20) -> list[dict]:
    """Return the newest signed entries without exposing the private key."""
    load_config()
    if not LEDGER.exists():
        return []
    bounded_limit = max(1, min(int(limit), 100))
    rows = [
        json.loads(line)
        for line in LEDGER.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    return rows[-bounded_limit:][::-1]


def public_entry(event: dict, include_text: bool = True) -> dict:
    """Return model-safe provenance fields for local integrations."""
    result = {
        "recordId": event["recordId"],
        "timestampIso": event["timestampIso"],
        "actor": event["actor"],
        "organization": event.get("organization"),
        "codeSignatureId": event["codeSignatureId"],
        "entryTitle": event["entryTitle"],
        "source": event["source"],
        "entryHash": event["entryHash"],
        "redactionApplied": event["redactionApplied"],
        "project": event.get("project"),
        "repository": event.get("repository"),
        "branch": event.get("branch"),
    }
    if include_text:
        result["entryText"] = event["entryText"]
    return result


def status_data() -> dict:
    config = load_config()
    count = len([
        line for line in LEDGER.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]) if LEDGER.exists() else 0
    organization = config.get("currentOrganization")
    stamp = f"[PT:{config['actor']} · {organization}]" if organization else f"[PT:{config['actor']}]"
    return {
        "enabled": True,
        "version": VERSION,
        "displayName": config.get("displayName", config["actor"]),
        "actor": config["actor"],
        "organization": organization,
        "stamp": stamp,
        "codeSignatureId": config["codeSignatureId"],
        "credentialExpiresAt": config.get("credentialExpiresAt"),
        "entries": count,
        "ledger": str(LEDGER),
        "registry": config["registry"],
        "submittedEntryCapture": True,
        "sensitiveValueRedaction": True,
        "rawKeystrokeCapture": False,
    }


def record_command(args: argparse.Namespace) -> None:
    text = read_entry_text(args)
    append_entry(text, args.source, args.path, {"exitCode": args.exit_code}, args.quiet)


def run_command(args: argparse.Namespace) -> None:
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("Provide a command after --")
    display = shlex.join(command)
    completed = subprocess.run(command, check=False)
    append_entry(display, args.source, args.path, {"exitCode": completed.returncode})
    raise SystemExit(completed.returncode)


def verify() -> None:
    config = load_config()
    if not LEDGER.exists():
        raise SystemExit("No prompt entries found")
    lines = [line for line in LEDGER.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    previous = None
    with tempfile.TemporaryDirectory() as folder:
        allowed = pathlib.Path(folder) / "allowed_signers"
        allowed.write_text(f"{config['actor']} {config['publicKey']}\n", encoding="utf-8")
        for index, line in enumerate(lines, 1):
            event = json.loads(line)
            signature = base64.b64decode(event.pop("signature"))
            if event.get("previousHash") != previous:
                raise SystemExit(f"Broken chain at entry {index}")
            if event.get("entryHash") != sha256_text(event.get("entryText", "")):
                raise SystemExit(f"Entry text mismatch at entry {index}")
            if event.get("actor") != config["actor"] or event.get("codeSignatureId") != config["codeSignatureId"]:
                raise SystemExit(f"Author mismatch at entry {index}")
            sig_file = pathlib.Path(folder) / "entry.sig"
            sig_file.write_bytes(signature)
            result = run("ssh-keygen", "-Y", "verify", "-f", str(allowed), "-I", config["actor"], "-n", "prompt-trace", "-s", str(sig_file), input_text=canonical(event).decode("utf-8"))
            if result.returncode:
                raise SystemExit(f"Invalid signature at entry {index}")
            previous = hashlib.sha256(line.encode("utf-8")).hexdigest()
    print(f"Verified {len(lines)} signed entries for {config['codeSignatureId']}")


def export_csv(destination: str) -> None:
    load_config()
    rows = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8-sig").splitlines() if line.strip()] if LEDGER.exists() else []
    path = pathlib.Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["recordId", "timestampIso", "actor", "organization", "codeSignatureId", "entryTitle", "source", "entryText", "entryHash", "redactionApplied", "redactionCount", "project", "repository", "branch", "head", "path", "signature"]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} signed entries to {path}")


def set_context(organization: str | None) -> None:
    config = load_config()
    config["currentOrganization"] = validate_organization(organization) if organization else None
    CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Prompt Trace context: {config.get('currentOrganization') or 'Personal'}")


def status() -> None:
    print(json.dumps(status_data(), indent=2))


def recent(args: argparse.Namespace) -> None:
    print(json.dumps([
        public_entry(event, include_text=not args.no_text)
        for event in read_entries(args.limit)
    ], indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(prog="prompt-trace", description="Author-signed prompt and terminal-entry ledger")
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--actor", required=True)
    initialize.add_argument("--display-name")
    initialize.add_argument("--registry", help="Local or shared actors.json path")
    initialize.add_argument("--enrollment-token")
    initialize.add_argument("--consent", action="store_true")
    issue = commands.add_parser("issue-id")
    issue.add_argument("--actor", required=True)
    issue.add_argument("--display-name", required=True)
    issue.add_argument("--registry", required=True)
    record = commands.add_parser("record")
    record.add_argument("--text")
    record.add_argument("--source", default="composer")
    record.add_argument("--path")
    record.add_argument("--exit-code", type=int)
    record.add_argument("--quiet", action="store_true")
    execute = commands.add_parser("run")
    execute.add_argument("--source", default="terminal-wrapper")
    execute.add_argument("--path")
    execute.add_argument("command", nargs=argparse.REMAINDER)
    export = commands.add_parser("export-csv")
    export.add_argument("destination")
    commands.add_parser("verify")
    commands.add_parser("status")
    recent_entries = commands.add_parser("recent")
    recent_entries.add_argument("--limit", type=int, default=20)
    recent_entries.add_argument("--no-text", action="store_true")
    context = commands.add_parser("set-context")
    context.add_argument("--organization")
    args = parser.parse_args()
    if args.command == "init":
        init_identity(args.actor, args.display_name, args.consent, args.registry, args.enrollment_token)
    elif args.command == "issue-id":
        issue_actor(args.actor, args.display_name, args.registry)
    elif args.command == "record":
        record_command(args)
    elif args.command == "run":
        run_command(args)
    elif args.command == "export-csv":
        export_csv(args.destination)
    elif args.command == "verify":
        verify()
    elif args.command == "status":
        status()
    elif args.command == "recent":
        recent(args)
    elif args.command == "set-context":
        set_context(args.organization)


if __name__ == "__main__":
    main()
