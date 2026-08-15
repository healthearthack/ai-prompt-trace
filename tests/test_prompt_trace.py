import csv
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / "prompt_trace.py"


@unittest.skipUnless(shutil.which("ssh-keygen"), "OpenSSH required")
class PromptTraceTest(unittest.TestCase):
    def call(self, home, *args, input_text=None):
        env = {**os.environ, "PROMPT_TRACE_HOME": str(home)}
        return subprocess.run([sys.executable, CLI, *args], env=env, input=input_text, text=True, capture_output=True)

    def test_ac_prompt_is_signed_verified_and_exported(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder) / "device"
            init = self.call(home, "init", "--actor", "AC", "--consent")
            self.assertEqual(init.returncode, 0, init.stderr)
            record = self.call(home, "record", "--source", "ai-composer", input_text="Design a weather risk card")
            self.assertEqual(record.returncode, 0, record.stderr)
            event = json.loads((home / "prompt-ledger.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(event["actor"], "AC")
            self.assertEqual(event["entryText"], "Design a weather risk card")
            self.assertEqual(event["entryTitle"], "[PT:AC] Design a weather risk card")
            self.assertTrue(event["codeSignatureId"].startswith("AC:"))
            self.assertTrue(event["signature"])
            verify = self.call(home, "verify")
            self.assertEqual(verify.returncode, 0, verify.stderr)
            export_path = pathlib.Path(folder) / "activity.csv"
            export = self.call(home, "export-csv", str(export_path))
            self.assertEqual(export.returncode, 0, export.stderr)
            with export_path.open(encoding="utf-8-sig", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["actor"], "AC")
            self.assertEqual(row["entryText"], "Design a weather risk card")
            self.assertEqual(row["entryTitle"], "[PT:AC] Design a weather risk card")

    def test_display_name_and_eight_character_author_id_are_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder)
            init = self.call(home, "init", "--actor", "SARAPENN", "--display-name", "Sara Penny", "--consent")
            self.assertEqual(init.returncode, 0, init.stderr)
            record = self.call(home, "record", "--text", "Review the release", "--source", "test")
            self.assertEqual(record.returncode, 0, record.stderr)
            event = json.loads((home / "prompt-ledger.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(event["entryTitle"], "[PT:SARAPENN] Review the release")
            status = self.call(home, "status")
            status_data = json.loads(status.stdout)
            self.assertEqual(status_data["displayName"], "Sara Penny")
            expires = datetime.datetime.fromisoformat(status_data["credentialExpiresAt"].replace("Z", "+00:00"))
            self.assertGreaterEqual(expires.year, datetime.datetime.now(datetime.timezone.utc).year + 99)

    def test_author_id_is_strictly_one_to_eight_alphanumeric_characters(self):
        with tempfile.TemporaryDirectory() as folder:
            for actor in ("TOO-LONG", "NINECHARS", "JOE SPACK", "AC!"):
                result = self.call(pathlib.Path(folder) / actor.replace("/", "_"), "init", "--actor", actor, "--consent")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("1-8 alphanumeric", result.stderr)

    def test_enterprise_admin_issues_single_use_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            registry = root / "team" / "actors.json"
            admin = self.call(root / "admin", "issue-id", "--actor", "EMP0042", "--display-name", "Employee Forty Two", "--registry", str(registry))
            self.assertEqual(admin.returncode, 0, admin.stderr)
            token = admin.stdout.split("One-time enrollment token: ", 1)[1].splitlines()[0]
            enrollment = self.call(root / "device", "init", "--actor", "EMP0042", "--display-name", "Employee Forty Two", "--registry", str(registry), f"--enrollment-token={token}", "--consent")
            self.assertEqual(enrollment.returncode, 0, enrollment.stderr)
            duplicate = self.call(root / "other", "init", "--actor", "EMP0042", "--registry", str(registry), f"--enrollment-token={token}", "--consent")
            self.assertNotEqual(duplicate.returncode, 0)
            unissued = self.call(root / "unissued", "init", "--actor", "EMP0043", "--registry", str(registry), "--consent")
            self.assertNotEqual(unissued.returncode, 0)
            self.assertIn("has not been issued", unissued.stderr)

    def test_existing_browser_authorship_title_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder)
            self.assertEqual(self.call(home, "init", "--actor", "AC", "--consent").returncode, 0)
            record = self.call(home, "record", "--text", "[PT:AC] Shared prompt contribution", "--source", "browser:chatgpt.com")
            self.assertEqual(record.returncode, 0, record.stderr)
            event = json.loads((home / "prompt-ledger.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(event["entryTitle"], "[PT:AC] Shared prompt contribution")
            self.assertNotIn("[PT:AC] [PT:AC]", event["entryTitle"])

    def test_organization_context_persists_in_authorship_title(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder)
            self.assertEqual(self.call(home, "init", "--actor", "AC", "--consent").returncode, 0)
            context = self.call(home, "set-context", "--organization", "ADP")
            self.assertEqual(context.returncode, 0, context.stderr)
            record = self.call(home, "record", "--text", "Review payroll integration", "--source", "test")
            self.assertEqual(record.returncode, 0, record.stderr)
            event = json.loads((home / "prompt-ledger.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(event["organization"], "ADP")
            self.assertEqual(event["entryTitle"], "[PT:AC · ADP] Review payroll integration")

    def test_shared_registry_rejects_second_ac_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            registry = root / "shared" / "actors.json"
            first = self.call(root / "one", "init", "--actor", "AC", "--registry", str(registry), "--consent")
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.call(root / "two", "init", "--actor", "AC", "--registry", str(registry), "--consent")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already reserved", second.stderr)

    def test_modified_prompt_breaks_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder)
            self.assertEqual(self.call(home, "init", "--actor", "AC", "--consent").returncode, 0)
            self.assertEqual(self.call(home, "record", "--text", "original", "--source", "test").returncode, 0)
            ledger = home / "prompt-ledger.jsonl"
            event = json.loads(ledger.read_text(encoding="utf-8"))
            event["entryText"] = "changed"
            ledger.write_text(json.dumps(event) + "\n", encoding="utf-8")
            verify = self.call(home, "verify")
            self.assertNotEqual(verify.returncode, 0)
            self.assertIn("Entry text mismatch", verify.stderr)

    def test_sensitive_values_are_redacted_before_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder)
            self.assertEqual(self.call(home, "init", "--actor", "AC", "--consent").returncode, 0)
            sensitive = "deploy --password hunter2 --api-key sk-abcdefghijklmnop Authorization: Bearer secret-token"
            record = self.call(home, "record", "--source", "powershell", input_text=sensitive)
            self.assertEqual(record.returncode, 0, record.stderr)
            ledger_text = (home / "prompt-ledger.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("hunter2", ledger_text)
            self.assertNotIn("sk-abcdefghijklmnop", ledger_text)
            self.assertNotIn("secret-token", ledger_text)
            event = json.loads(ledger_text)
            self.assertIn("****", event["entryText"])
            self.assertTrue(event["redactionApplied"])
            self.assertGreaterEqual(event["redactionCount"], 3)
            self.assertEqual(self.call(home, "verify").returncode, 0)


if __name__ == "__main__":
    unittest.main()
