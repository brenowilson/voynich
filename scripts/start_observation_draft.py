"""Start a deterministic observation draft revision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.observation.lifecycle import start_draft


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--annotator-id", required=True)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8"))
    draft = start_draft(
        source,
        annotator_id=args.annotator_id,
        created_at=args.created_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(draft, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "package_id": draft["package_id"],
                "status": draft["package_status"],
                "supersedes_package_id": draft["revision"]["supersedes_package_id"],
                "source_sha256": draft["source"]["source_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
