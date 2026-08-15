import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cyber_cv import TITLE, WATERMARK
from cyber_cv.exporter import normalize, render_html, render_markdown


class CyberCvTest(unittest.TestCase):
    def test_standardized_title_raw_input_and_watermark(self):
        data = normalize({"profile": {"displayName": "Andrew", "authorId": "AC"}, "entries": [{"rawInput": "Build the system", "timestamp": "2026", "verified": True}]})
        for rendered in (render_markdown(data), render_html(data)):
            self.assertIn(TITLE, rendered)
            self.assertIn("Build the system", rendered)
            self.assertIn(WATERMARK, rendered)
            self.assertIn("[PT:AC]", rendered)

    def test_empty_inputs_are_never_exported(self):
        data = normalize({"profile": {}, "entries": [{"rawInput": "   "}]})
        self.assertEqual(data["entries"], [])


if __name__ == "__main__":
    unittest.main()
