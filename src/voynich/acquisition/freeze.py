"""Validate image-byte inventories and build immutable source-freeze records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .byte_store import hash_file, load_jsonl


class FreezeValidationError(RuntimeError):
    """Raised when a candidate source freeze is incomplete or inconsistent."""


@dataclass(frozen=True)
class FreezeSummary:
    expected_assets: int
    verified_records: int
    total_bytes: int
    record_set_sha256: str
    stored_objects_verified: int


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def canonical_record_bytes(records: Iterable[dict[str, Any]]) -> bytes:
    normalized = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    normalized.sort()
    return ("\n".join(normalized) + "\n").encode("utf-8")


def validate_records(
    *,
    assets_path: Path,
    record_paths: list[Path],
    expected_manifest_sha256: str,
    representation: str = "iiif-full-jpeg",
    require_stored_bytes: bool = False,
    store_root: Path | None = None,
) -> tuple[list[dict[str, Any]], FreezeSummary]:
    assets = load_jsonl(assets_path)
    expected_keys = {
        (int(asset["sequence_index"]), str(asset.get("child_oid") or "")) for asset in assets
    }
    if len(expected_keys) != len(assets):
        raise FreezeValidationError("asset inventory contains duplicate sequence/child keys")

    records: list[dict[str, Any]] = []
    for path in record_paths:
        records.extend(load_jsonl(path))

    relevant = [record for record in records if record.get("representation") == representation]
    seen: dict[tuple[int, str], dict[str, Any]] = {}
    errors: list[str] = []
    stored_verified = 0

    for record in relevant:
        key = (int(record["sequence_index"]), str(record.get("child_oid") or ""))
        if key in seen:
            errors.append(f"duplicate byte record for {key}")
            continue
        seen[key] = record

        if record.get("source_manifest_sha256") != expected_manifest_sha256:
            errors.append(f"manifest hash mismatch for {key}")
        if record.get("status") != "verified":
            errors.append(f"non-verified status for {key}: {record.get('status')}")
        digest = record.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"invalid sha256 for {key}")
        if int(record.get("byte_count") or 0) <= 0:
            errors.append(f"zero byte count for {key}")

        stored_path = record.get("stored_path")
        if require_stored_bytes:
            if store_root is None:
                raise FreezeValidationError("store_root is required when stored bytes are mandatory")
            if not stored_path:
                errors.append(f"missing stored_path for {key}")
            else:
                object_file = store_root / str(stored_path)
                if not object_file.is_file():
                    errors.append(f"stored object not found for {key}: {object_file}")
                else:
                    actual_digest, actual_size = hash_file(object_file)
                    if actual_digest != digest or actual_size != int(record["byte_count"]):
                        errors.append(f"stored object verification failed for {key}")
                    else:
                        stored_verified += 1

    missing = sorted(expected_keys - set(seen))
    unexpected = sorted(set(seen) - expected_keys)
    if missing:
        errors.append(f"missing records: {missing[:10]}{'...' if len(missing) > 10 else ''}")
    if unexpected:
        errors.append(f"unexpected records: {unexpected[:10]}{'...' if len(unexpected) > 10 else ''}")
    if errors:
        raise FreezeValidationError("; ".join(errors))

    ordered = [seen[key] for key in sorted(expected_keys)]
    record_set_sha = hashlib.sha256(canonical_record_bytes(ordered)).hexdigest()
    summary = FreezeSummary(
        expected_assets=len(assets),
        verified_records=len(ordered),
        total_bytes=sum(int(record["byte_count"]) for record in ordered),
        record_set_sha256=record_set_sha,
        stored_objects_verified=stored_verified,
    )
    return ordered, summary


def build_freeze(
    *,
    freeze_id: str,
    assets_path: Path,
    record_paths: list[Path],
    expected_manifest_sha256: str,
    output_path: Path,
    require_stored_bytes: bool = True,
    store_root: Path | None = None,
) -> dict[str, Any]:
    records, summary = validate_records(
        assets_path=assets_path,
        record_paths=record_paths,
        expected_manifest_sha256=expected_manifest_sha256,
        require_stored_bytes=require_stored_bytes,
        store_root=store_root,
    )
    freeze = {
        "freeze_id": freeze_id,
        "schema_version": "0.1.0",
        "created_at": utc_now(),
        "institution": "Yale University Library / Beinecke Rare Book and Manuscript Library",
        "shelfmark": "Beinecke MS 408",
        "representation": "iiif-full-jpeg",
        "source_manifest_sha256": expected_manifest_sha256,
        "expected_assets": summary.expected_assets,
        "verified_records": summary.verified_records,
        "total_bytes": summary.total_bytes,
        "record_set_sha256": summary.record_set_sha256,
        "stored_objects_verified": summary.stored_objects_verified,
        "stored_bytes_required": require_stored_bytes,
        "asset_inventory_path": assets_path.as_posix(),
        "byte_record_paths": [path.as_posix() for path in record_paths],
        "status": "frozen" if require_stored_bytes else "verification-only",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(freeze, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return freeze
