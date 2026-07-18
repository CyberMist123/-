#!/usr/bin/env python3
"""Extract Cachito-correlated 710002 service UUID samples from a scanner log.

This is read-only analysis. It does not scan, connect, advertise, or write BLE data.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

CAPTURE_RE = re.compile(
    r"^===== CAPTURE START (\d+)/(\d+) \| .*? \| (\d+)s \| (.*?) =====$"
)
END_RE = re.compile(r"^===== CAPTURE END")
UUID_RE = re.compile(
    r"710002[0-9a-f]{2}-0400-265d-(0302|050a|0601)-([0-9a-f]{12})",
    re.I,
)


def parse(path: Path):
    current = None
    address = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = CAPTURE_RE.match(line)
        if match:
            current = {
                "step": int(match.group(1)),
                "duration": int(match.group(3)),
                "action": match.group(4),
            }
            continue
        if END_RE.match(line):
            current = None
            continue
        if line.startswith("Address: "):
            address = line.split(": ", 1)[1]
            continue
        if current and line.startswith("Service UUIDs: "):
            for mode, tail in UUID_RE.findall(line):
                yield {
                    **current,
                    "address": address,
                    "mode": mode.lower(),
                    "value_hex": tail[:2].upper(),
                    "value_decimal": int(tail[:2], 16),
                    "tail": tail.lower(),
                }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    rows = list(parse(args.log))
    fields = [
        "step",
        "duration",
        "action",
        "address",
        "mode",
        "value_hex",
        "value_decimal",
        "tail",
    ]

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    else:
        writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
