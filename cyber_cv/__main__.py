import argparse
import json
import pathlib

from .exporter import export_bundle

parser = argparse.ArgumentParser(description="Export a Terminal Prompt Trace Curriculum Vitae")
parser.add_argument("input", help="Curated JSON input")
parser.add_argument("--out", required=True, help="Destination ZIP")
args = parser.parse_args()
source = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8-sig"))
print(export_bundle(source, pathlib.Path(args.out).expanduser().resolve()))
