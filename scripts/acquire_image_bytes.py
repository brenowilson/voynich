"""Stream Yale image bytes, hash them and optionally retain them outside Git."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from voynich.acquisition.byte_store import acquire_assets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=Path("sources/primary/yale/assets.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--store-root", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--discard-bytes", action="store_true")
    args = parser.parse_args()

    result = acquire_assets(
        assets_path=args.assets.resolve(),
        output_path=args.output.resolve(),
        store_root=args.store_root.resolve(),
        source_manifest_sha256=args.manifest_sha256,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
        retain_bytes=not args.discard_bytes,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
