"""Build the canonical Yale asset and physical-side manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.acquisition.page_manifest import build_page_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=Path("sources/primary/yale/assets.jsonl"))
    parser.add_argument(
        "--byte-records",
        type=Path,
        default=Path("sources/primary/yale/image-byte-records-stored.jsonl"),
    )
    parser.add_argument(
        "--relations",
        type=Path,
        default=Path("sources/primary/manifests/asset-side-relations.csv"),
    )
    parser.add_argument(
        "--composites",
        type=Path,
        default=Path("sources/primary/manifests/foldouts.csv"),
    )
    parser.add_argument(
        "--rights",
        type=Path,
        default=Path("sources/primary/yale/rights.json"),
    )
    parser.add_argument(
        "--jsonl-output",
        type=Path,
        default=Path("sources/primary/manifests/pages.jsonl"),
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("sources/primary/manifests/pages.csv"),
    )
    args = parser.parse_args()

    result = build_page_manifest(
        assets_path=args.assets.resolve(),
        byte_records_path=args.byte_records.resolve(),
        relations_path=args.relations.resolve(),
        composites_path=args.composites.resolve(),
        rights_path=args.rights.resolve(),
        jsonl_output=args.jsonl_output.resolve(),
        csv_output=args.csv_output.resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
