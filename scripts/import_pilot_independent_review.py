"""Validate and import a completed PILOT-0001 independent-review form."""

from __future__ import annotations

import argparse
from pathlib import Path

from voynich.pilot.independent_review import (
    import_completed_rows,
    read_csv,
    read_jsonl,
    write_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidates.jsonl"),
    )
    parser.add_argument("--completed-form", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/independent-observations.jsonl"),
    )
    args = parser.parse_args()

    observations = import_completed_rows(
        candidates=read_jsonl(args.candidates.resolve()),
        rows=read_csv(args.completed_form.resolve()),
    )
    write_jsonl(args.output.resolve(), observations)
    print(f"imported {len(observations)} independent observations")


if __name__ == "__main__":
    main()
