"""Freeze a completed observation draft and write its freeze record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.observation.lifecycle import freeze_draft


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--frozen-at", required=True)
    parser.add_argument("--package-output", type=Path, required=True)
    parser.add_argument("--freeze-output", type=Path, required=True)
    args = parser.parse_args()

    draft = json.loads(args.input.read_text(encoding="utf-8"))
    frozen, freeze_record = freeze_draft(draft, frozen_at=args.frozen_at)
    write_json(args.package_output, frozen)
    write_json(args.freeze_output, freeze_record)
    print(
        json.dumps(
            {
                "freeze_id": freeze_record["freeze_id"],
                "package_id": freeze_record["package_id"],
                "package_sha256": freeze_record["package_sha256"],
                "entity_counts": freeze_record["entity_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
