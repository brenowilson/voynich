"""Build a deterministic blank observation package for one frozen Yale panel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.observation.model import write_blank_package


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pages",
        type=Path,
        default=Path("sources/primary/manifests/pages.jsonl"),
    )
    parser.add_argument("--panel-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    package = write_blank_package(
        pages_path=args.pages.resolve(),
        panel_id=args.panel_id,
        output_path=args.output.resolve(),
    )
    print(json.dumps({
        "package_id": package["package_id"],
        "source_sha256": package["source"]["source_sha256"],
        "width_px": package["source"]["width_px"],
        "height_px": package["source"]["height_px"],
        "status": package["package_status"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
