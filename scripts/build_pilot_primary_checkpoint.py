"""Validate PILOT-0001 primary visual observations and build a checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.pilot.observations import write_primary_checkpoint


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidates.jsonl"),
    )
    parser.add_argument(
        "--observations",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/visual-observations.jsonl"),
    )
    parser.add_argument(
        "--candidate-freeze",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidate-freeze.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/primary-observation-checkpoint.json"),
    )
    args = parser.parse_args()

    checkpoint = write_primary_checkpoint(
        candidates_path=args.candidates.resolve(),
        observations_path=args.observations.resolve(),
        candidate_freeze_path=args.candidate_freeze.resolve(),
        output_path=args.output.resolve(),
    )
    print(json.dumps(checkpoint, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
