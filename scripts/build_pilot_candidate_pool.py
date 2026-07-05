"""Build and freeze the metadata-only PILOT-0001 candidate pool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.pilot.selection import build_candidate_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pages",
        type=Path,
        default=Path("sources/primary/manifests/pages.jsonl"),
    )
    parser.add_argument(
        "--foldout-relations",
        type=Path,
        default=Path("sources/primary/manifests/foldout-panel-relations.csv"),
    )
    parser.add_argument(
        "--jsonl-output",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidates.jsonl"),
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidates.csv"),
    )
    parser.add_argument(
        "--freeze-output",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidate-freeze.json"),
    )
    args = parser.parse_args()

    result = build_candidate_files(
        pages_path=args.pages.resolve(),
        foldout_relations_path=args.foldout_relations.resolve(),
        jsonl_output=args.jsonl_output.resolve(),
        csv_output=args.csv_output.resolve(),
        freeze_output=args.freeze_output.resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
