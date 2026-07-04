import json
from dataclasses import asdict
from pathlib import Path

import pytest

from voynich.acquisition.byte_store import acquire_one, object_path, write_records
from voynich.acquisition.freeze import FreezeValidationError, build_freeze, validate_records

MANIFEST_SHA = "a" * 64


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def asset(sequence_index: int, child_oid: str, source: Path) -> dict:
    return {
        "sequence_index": sequence_index,
        "child_oid": child_oid,
        "canvas_id": f"canvas-{child_oid}",
        "label": f"{sequence_index}r",
        "image_url": source.as_uri(),
    }


def test_acquire_one_streams_and_retains_content_addressed_object(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(b"voynich-image-bytes")
    store = tmp_path / "store"

    record = acquire_one(
        asset(1, "1001", source),
        source_manifest_sha256=MANIFEST_SHA,
        store_root=store,
    )

    assert record.status == "verified"
    assert record.byte_count == len(b"voynich-image-bytes")
    assert record.sha256 is not None
    assert record.stored_path is not None
    stored = store / record.stored_path
    assert stored.read_bytes() == b"voynich-image-bytes"
    assert stored == object_path(store, record.sha256, "jpg")


def test_freeze_requires_complete_verified_inventory_and_stored_objects(tmp_path: Path) -> None:
    source_a = tmp_path / "a.jpg"
    source_b = tmp_path / "b.jpg"
    source_a.write_bytes(b"alpha")
    source_b.write_bytes(b"beta")
    store = tmp_path / "store"
    assets = [asset(1, "1001", source_a), asset(2, "1002", source_b)]
    assets_path = tmp_path / "assets.jsonl"
    write_jsonl(assets_path, assets)

    records = [
        acquire_one(row, source_manifest_sha256=MANIFEST_SHA, store_root=store)
        for row in assets
    ]
    records_path = tmp_path / "records.jsonl"
    write_records(records_path, records)
    output = tmp_path / "freeze.json"

    freeze = build_freeze(
        freeze_id="SOURCE-FREEZE-TEST",
        assets_path=assets_path,
        record_paths=[records_path],
        expected_manifest_sha256=MANIFEST_SHA,
        output_path=output,
        require_stored_bytes=True,
        store_root=store,
        path_root=tmp_path,
    )

    assert freeze["status"] == "frozen"
    assert freeze["expected_assets"] == 2
    assert freeze["stored_objects_verified"] == 2
    assert freeze["asset_inventory_path"] == "assets.jsonl"
    assert freeze["byte_record_paths"] == ["records.jsonl"]
    assert output.is_file()


def test_freeze_rejects_missing_record(tmp_path: Path) -> None:
    source = tmp_path / "a.jpg"
    source.write_bytes(b"alpha")
    assets_path = tmp_path / "assets.jsonl"
    write_jsonl(
        assets_path,
        [asset(1, "1001", source), asset(2, "1002", source)],
    )
    record = acquire_one(
        asset(1, "1001", source),
        source_manifest_sha256=MANIFEST_SHA,
        store_root=tmp_path / "store",
        retain_bytes=False,
    )
    records_path = tmp_path / "records.jsonl"
    write_jsonl(records_path, [asdict(record)])

    with pytest.raises(FreezeValidationError, match="missing records"):
        validate_records(
            assets_path=assets_path,
            record_paths=[records_path],
            expected_manifest_sha256=MANIFEST_SHA,
        )
