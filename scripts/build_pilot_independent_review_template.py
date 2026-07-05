"""Export the blinded PILOT-0001 independent-review form."""

from __future__ import annotations

import argparse
from pathlib import Path

from voynich.pilot.independent_review import read_jsonl, write_template


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidates.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/independent-review-template.csv"),
    )
    args = parser.parse_args()
    write_template(args.output.resolve(), read_jsonl(args.candidates.resolve()))


if __name__ == "__main__":
    main()
