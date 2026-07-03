"""Build explicit asset-to-side relation tables from Yale institutional labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.acquisition.relations import build_relation_tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--assets",
        type=Path,
        default=Path("sources/primary/yale/assets.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("sources/primary/manifests"),
    )
    args = parser.parse_args()
    result = build_relation_tables(args.assets.resolve(), args.output_dir.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
