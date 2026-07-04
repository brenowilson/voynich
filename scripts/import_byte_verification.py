"""Import a completed CI byte-verification artifact into repository records."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--workflow-run-id", type=int, required=True)
    parser.add_argument("--workflow-head-sha", required=True)
    parser.add_argument("--artifact-sha256", required=True)
    args = parser.parse_args()

    records = [
        json.loads(line)
        for line in args.records.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records.sort(key=lambda row: (int(row["sequence_index"]), str(row["child_oid"])))
    if len(records) != 213:
        raise SystemExit(f"expected 213 byte records, found {len(records)}")
    if any(row.get("status") != "verified" for row in records):
        raise SystemExit("artifact contains a non-verified record")

    output_root = args.output_root.resolve()
    records_path = output_root / "sources/primary/yale/image-byte-records.jsonl"
    checksum_path = output_root / "sources/primary/checksums/iiif-full-jpeg.sha256"
    freeze_path = output_root / "sources/primary/freezes/SOURCE-FREEZE-0001-verification.json"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.parent.mkdir(parents=True, exist_ok=True)

    records_text = "".join(canonical_json(row) + "\n" for row in records)
    records_path.write_text(records_text, encoding="utf-8")
    checksums_text = "".join(
        f'{row["sha256"]}  {int(row["sequence_index"]):03d}-{row["child_oid"]}.jpg\n'
        for row in records
    )
    checksum_path.write_text(checksums_text, encoding="utf-8")

    original_freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    canonical_record_set = (
        "\n".join(sorted(canonical_json(row) for row in records)) + "\n"
    ).encode("utf-8")
    stable_content_rows = [
        {
            key: row.get(key)
            for key in (
                "source_manifest_sha256",
                "sequence_index",
                "child_oid",
                "canvas_id",
                "institutional_label",
                "representation",
                "source_url",
                "resolved_url",
                "sha256",
                "byte_count",
                "media_type",
            )
        }
        for row in records
    ]
    stable_content = (
        "\n".join(sorted(canonical_json(row) for row in stable_content_rows)) + "\n"
    ).encode("utf-8")

    freeze = {
        "freeze_id": "SOURCE-FREEZE-0001-VERIFICATION",
        "schema_version": "0.1.0",
        "created_at": original_freeze["created_at"],
        "institution": original_freeze["institution"],
        "shelfmark": original_freeze["shelfmark"],
        "representation": original_freeze["representation"],
        "source_manifest_sha256": original_freeze["source_manifest_sha256"],
        "asset_inventory_path": "sources/primary/yale/assets.jsonl",
        "byte_record_path": "sources/primary/yale/image-byte-records.jsonl",
        "checksum_path": "sources/primary/checksums/iiif-full-jpeg.sha256",
        "expected_assets": 213,
        "verified_records": 213,
        "unique_child_oids": len({row["child_oid"] for row in records}),
        "unique_byte_sha256": len({row["sha256"] for row in records}),
        "total_bytes": sum(int(row["byte_count"]) for row in records),
        "minimum_asset_bytes": min(int(row["byte_count"]) for row in records),
        "maximum_asset_bytes": max(int(row["byte_count"]) for row in records),
        "median_asset_bytes": int(statistics.median(int(row["byte_count"]) for row in records)),
        "record_set_sha256": sha256_bytes(canonical_record_set),
        "content_inventory_sha256": sha256_bytes(stable_content),
        "record_file_sha256": sha256_bytes(records_text.encode("utf-8")),
        "workflow_run_id": args.workflow_run_id,
        "workflow_head_sha": args.workflow_head_sha,
        "workflow_artifact_sha256": args.artifact_sha256,
        "stored_bytes_required": False,
        "stored_objects_verified": 0,
        "status": "verification-only",
        "storage_status": (
            "All byte streams were fully downloaded and hashed in CI, then discarded. "
            "Durable content-addressed storage is still required before SOURCE-FREEZE-0001 "
            "can be declared frozen."
        ),
    }
    freeze_path.write_text(
        json.dumps(freeze, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(freeze, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
