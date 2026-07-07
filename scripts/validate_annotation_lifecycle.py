from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.observation.lifecycle import validate_lifecycle_chain


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, nargs="+", required=True)
    parser.add_argument("--packages", type=Path, nargs="+", required=True)
    args = parser.parse_args()
    if len(args.records) != len(args.packages):
        raise SystemExit("record and package counts differ")
    summary = validate_lifecycle_chain(
        records=[load_json(path) for path in args.records],
        packages=[load_json(path) for path in args.packages],
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
