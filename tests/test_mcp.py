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
SERVER = ROOT / "mcp_server.py"


@unittest.skipUnless(shutil.which("ssh-keygen"), "OpenSSH required")
class PromptTraceMCPTest(unittest.TestCase):
    def test_stdio_server_lists_records_and_reads_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            home = pathlib.Path(folder) / "device"
            env = {**os.environ, "PROMPT_TRACE_HOME": str(home)}
            initialized = subprocess.run(
                [sys.executable, CLI, "init", "--actor", "AC", "--consent"],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            requests = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "prompt_trace_record_submission", "arguments": {"text": "Build a weather card", "source": "chatgpt-desktop:mcp", "activityType": "prompt"}}},
                {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "prompt_trace_recent", "arguments": {"limit": 1}}},
            ]
            completed = subprocess.run(
                [sys.executable, SERVER], env=env,
                input="".join(json.dumps(item) + "\n" for item in requests),
                text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            responses = [json.loads(line) for line in completed.stdout.splitlines()]
            self.assertEqual(responses[0]["result"]["serverInfo"]["version"], "4.0.1")
            names = {tool["name"] for tool in responses[1]["result"]["tools"]}
            self.assertIn("prompt_trace_record_submission", names)
            recorded = responses[2]["result"]["structuredContent"]
            self.assertEqual(recorded["stamp"], "[PT:AC]")
            self.assertEqual(recorded["entryText"], "Build a weather card")
            recent = responses[3]["result"]["structuredContent"]
            self.assertEqual(recent[0]["recordId"], recorded["recordId"])


if __name__ == "__main__":
    unittest.main()
