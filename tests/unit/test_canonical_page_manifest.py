import pytest

from voynich.acquisition.page_manifest import PageManifestError, build_records


def asset(sequence_index: int, child_oid: str, label: str) -> dict:
    return {
        "sequence_index": sequence_index,
        "child_oid": child_oid,
        "canvas_id": f"https://example.org/canvas/{child_oid}",
        "label": label,
        "image_url": f"https://example.org/image/{child_oid}.jpg",
        "width_px": 1000,
        "height_px": 1200,
    }


def byte_record(sequence_index: int, child_oid: str) -> dict:
    return {
        "sequence_index": sequence_index,
        "child_oid": child_oid,
        "source_url": f"https://example.org/image/{child_oid}.jpg",
        "sha256": (child_oid[-1] if child_oid[-1] in "abcdef" else "a") * 64,
        "byte_count": 100 + sequence_index,
        "stored_path": f"sha256/aa/{'a' * 64}.jpg",
        "status": "verified",
        "acquired_at": "2026-07-04T00:00:00+00:00",
    }


def relation(child_oid: str, index: int, side_id: str, coverage: str) -> dict[str, str]:
    return {
        "child_oid": child_oid,
        "relation_index": str(index),
        "side_id": side_id,
        "coverage": coverage,
        "parse_status": "explicit_label_token",
    }


def test_manifest_preserves_simple_composite_and_support_assets() -> None:
    assets = [
        asset(1, "1001", "1r"),
        asset(2, "1002", "69v and 70r"),
        asset(3, "1003", "[Front cover]"),
    ]
    records = build_records(
        assets=assets,
        byte_records=[byte_record(1, "1001"), byte_record(2, "1002"), byte_record(3, "1003")],
        side_relations=[
            relation("1001", 1, "1r", "full_or_unspecified"),
            relation("1002", 1, "69v", "full_or_unspecified"),
            relation("1002", 2, "70r", "full_or_unspecified"),
        ],
        composite_candidates=[
            {
                "child_oid": "1002",
                "candidate_type": "multi_side_asset",
            }
        ],
        rights_record_path="sources/primary/yale/rights.json",
        rights_status="policy-documented-item-license-unspecified",
    )

    simple, composite, support = records
    assert simple["folio_id"] == "1r"
    assert simple["physical_parent_ids"] == ["1r"]
    assert simple["composition_status"] == "single_side_or_unspecified"

    assert composite["folio_id"] is None
    assert composite["physical_parent_ids"] == ["69v", "70r"]
    assert composite["composition_status"] == "composite_candidate"
    assert composite["candidate_type"] == "multi_side_asset"
    assert composite["reading_order"] is None

    assert support["record_type"] == "support_view"
    assert support["physical_parent_ids"] == []
    assert support["side_relations"] == []
    assert support["folio_id"] is None


def test_part_asset_is_not_promoted_to_complete_folio() -> None:
    records = build_records(
        assets=[asset(1, "1001", "70v (part)")],
        byte_records=[byte_record(1, "1001")],
        side_relations=[relation("1001", 1, "70v", "part")],
        composite_candidates=[
            {
                "child_oid": "1001",
                "candidate_type": "fragmented_side_asset",
            }
        ],
        rights_record_path="sources/primary/yale/rights.json",
        rights_status="policy-documented-item-license-unspecified",
    )
    assert records[0]["folio_id"] is None
    assert records[0]["side_relations"][0]["coverage"] == "part"


def test_manifest_rejects_missing_byte_record() -> None:
    with pytest.raises(PageManifestError, match="asset/byte key mismatch"):
        build_records(
            assets=[asset(1, "1001", "1r")],
            byte_records=[],
            side_relations=[relation("1001", 1, "1r", "full_or_unspecified")],
            composite_candidates=[],
            rights_record_path="sources/primary/yale/rights.json",
            rights_status="policy-documented-item-license-unspecified",
        )


def test_manifest_rejects_unverified_byte_record() -> None:
    row = byte_record(1, "1001")
    row["status"] = "failed"
    with pytest.raises(PageManifestError, match="not verified"):
        build_records(
            assets=[asset(1, "1001", "1r")],
            byte_records=[row],
            side_relations=[relation("1001", 1, "1r", "full_or_unspecified")],
            composite_candidates=[],
            rights_record_path="sources/primary/yale/rights.json",
            rights_status="policy-documented-item-license-unspecified",
        )
