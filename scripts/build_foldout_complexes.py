"""Build quire-level foldout complexes from canonical page records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.acquisition.foldout_complexes import build_foldout_complex_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pages",
        type=Path,
        default=Path("sources/primary/manifests/pages.jsonl"),
    )
    parser.add_argument(
        "--codicology",
        type=Path,
        default=Path("sources/primary/yale/foldout-codicology.json"),
    )
    parser.add_argument(
        "--complexes-output",
        type=Path,
        default=Path("sources/primary/manifests/foldout-complexes.jsonl"),
    )
    parser.add_argument(
        "--relations-output",
        type=Path,
        default=Path("sources/primary/manifests/foldout-panel-relations.csv"),
    )
    args = parser.parse_args()

    result = build_foldout_complex_files(
        pages_path=args.pages.resolve(),
        codicology_path=args.codicology.resolve(),
        complexes_output=args.complexes_output.resolve(),
        relations_output=args.relations_output.resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
