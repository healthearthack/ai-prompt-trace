"""Compatibility bridge from the original prompt builder to Prompt Trace v2."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prompt_trace import append_entry


def log_prompt(version):
    """Sign a prompt-builder submission in the same canonical ledger."""
    return append_entry(
        version["prompt_text"],
        "prompt-builder",
        metadata={
            "framework": version.get("framework"),
            "versionId": version.get("version_id"),
        },
    )
