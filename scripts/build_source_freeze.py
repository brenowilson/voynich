"""Validate image-byte records and build a source-freeze document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.acquisition.freeze import FreezeValidationError, build_freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-id", default="SOURCE-FREEZE-0001")
    parser.add_argument("--assets", type=Path, default=Path("sources/primary/yale/assets.jsonl"))
    parser.add_argument("--records", type=Path, nargs="+", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--verification-only", action="store_true")
    args = parser.parse_args()

    try:
        result = build_freeze(
            freeze_id=args.freeze_id,
            assets_path=args.assets.resolve(),
            record_paths=[path.resolve() for path in args.records],
            expected_manifest_sha256=args.manifest_sha256,
            output_path=args.output.resolve(),
            require_stored_bytes=not args.verification_only,
            store_root=args.store_root.resolve() if args.store_root else None,
        )
    except FreezeValidationError as exc:
        raise SystemExit(f"freeze validation failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
