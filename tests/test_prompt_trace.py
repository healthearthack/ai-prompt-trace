import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / "prompt_trace.py"


@unittest.skipUnless(subprocess.run(["where", "ssh-keygen"], capture_output=True).returncode == 0, "OpenSSH required")
class PromptTraceTest(unittest.TestCase):
    def test_signed_chain_verifies_and_omits_command_text(self):
        with tempfile.TemporaryDirectory() as folder:
            env = {**os.environ, "LOCALAPPDATA": folder}
            init = subprocess.run([sys.executable, CLI, "init", "--actor", "test-user"], env=env, text=True, capture_output=True)
            self.assertEqual(init.returncode, 0, init.stderr)
            trace = subprocess.run([sys.executable, CLI, "checkpoint", "--path", str(ROOT), "--workflow", "test", "--command-hash", "abc123"], env=env, text=True, capture_output=True)
            self.assertEqual(trace.returncode, 0, trace.stderr)
            ledger = pathlib.Path(folder) / "PromptTrace" / "breadcrumbs.jsonl"
            event = json.loads(ledger.read_text())
            self.assertEqual(event["commandHash"], "abc123")
            self.assertNotIn("commandText", event)
            verify = subprocess.run([sys.executable, CLI, "verify"], env=env, text=True, capture_output=True)
            self.assertEqual(verify.returncode, 0, verify.stderr)
            self.assertIn("Verified 1", verify.stdout)


if __name__ == "__main__":
    unittest.main()
