"""Build deterministic blank observation packages for PILOT-0001 candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.observation.work_queue import write_work_queue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidates",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidates.jsonl"),
    )
    parser.add_argument(
        "--pages",
        type=Path,
        default=Path("sources/primary/manifests/pages.jsonl"),
    )
    parser.add_argument(
        "--candidate-freeze",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/candidate-freeze.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("corpus/pilots/PILOT-0001/observation-work-queue"),
    )
    parser.add_argument("--batch-count", type=int, default=5)
    args = parser.parse_args()

    manifest = write_work_queue(
        candidates_path=args.candidates.resolve(),
        pages_path=args.pages.resolve(),
        candidate_freeze_path=args.candidate_freeze.resolve(),
        output_root=args.output_root.resolve(),
        batch_count=args.batch_count,
    )
    print(
        json.dumps(
            {
                "queue_id": manifest["queue_id"],
                "package_count": manifest["package_count"],
                "batch_count": manifest["batch_count"],
                "package_set_sha256": manifest["package_set_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
