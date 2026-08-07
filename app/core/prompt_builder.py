# Responsible for creating structured prompts and versioning

from datetime import datetime
from .trace_logger import log_prompt

class PromptBuilder:
    def __init__(self):
        self.versions = []

    def create_prompt(self, question: str, framework: str):
        timestamp = datetime.utcnow().isoformat()
        prompt_text = f"[Framework: {framework}] {question}"
        version = {
            "timestamp": timestamp,
            "question": question,
            "framework": framework,
            "prompt_text": prompt_text,
            "version_id": len(self.versions)+1
        }
        self.versions.append(version)
        log_prompt(version)
        return prompt_text, version

