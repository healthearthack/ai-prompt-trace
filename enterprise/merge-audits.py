#!/usr/bin/env python3
"""Merge manager-authorized Prompt Trace CSV exports by record ID."""

import argparse
import csv
import pathlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_folder")
    parser.add_argument("destination")
    args = parser.parse_args()
    source = pathlib.Path(args.source_folder).expanduser().resolve()
    destination = pathlib.Path(args.destination).expanduser().resolve()
    records = {}
    fields = []
    for path in sorted(source.glob("prompt-trace-*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames and not fields:
                fields = [*reader.fieldnames, "sourceExport"]
            for row in reader:
                row["sourceExport"] = path.name
                records[row.get("recordId") or f"{path.name}:{reader.line_num}"] = row
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or ["recordId", "sourceExport"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(records.values(), key=lambda row: row.get("timestampIso", "")))
    print(f"Merged {len(records)} unique records into {destination}")


if __name__ == "__main__":
    main()
