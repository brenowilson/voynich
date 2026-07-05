import json
from pathlib import Path

from voynich.pilot.selection import (
    build_candidate_freeze,
    build_candidate_records,
    canonical_records_sha256,
)


def page(index: int, *, composition: str = "single_side_or_unspecified", candidate_type=None, support=False):
    oid = str(2000 + index)
    return {
        "record_type": "support_view" if support else "manuscript_image",
        "photographic_panel_id": f"YDC-PANEL-{oid}",
        "institutional_id": oid,
        "institutional_label": f"{index}r" if not support else "[Cover]",
        "sequence_index": index,
        "source_url": f"https://example.org/{oid}.jpg",
        "source_sha256": f"{index % 16:x}" * 64,
        "byte_count": 1000 + index,
        "width_px": 1000,
        "height_px": 1200,
        "stored_path": f"sha256/aa/{'a' * 64}.jpg",
        "physical_parent_ids": [] if support else [f"{index}r"],
        "composition_status": "support_view" if support else composition,
        "candidate_type": candidate_type,
        "acquisition_status": "verified",
        "reading_order": None,
    }


def relation(panel_index: int, complex_id: str, *, leaf_id: str = ""):
    oid = str(2000 + panel_index)
    return {
        "photographic_panel_id": f"YDC-PANEL-{oid}",
        "complex_id": complex_id,
        "physical_leaf_id": leaf_id,
    }


def test_candidate_pool_is_metadata_only_stratified_and_deterministic() -> None:
    pages = [page(index) for index in range(1, 21)]
    pages += [
        page(21, composition="composite_candidate", candidate_type="fragmented_side_asset"),
        page(22, composition="composite_candidate", candidate_type="fragmented_side_asset"),
        page(23, composition="composite_candidate", candidate_type="multi_side_asset"),
        page(24, composition="composite_candidate", candidate_type="multi_side_asset"),
        page(25, support=True),
    ]
    leaf_id = "MS408-Q14-FOLDOUT-LEAF-SEXTUPLE-01"
    relations = [
        relation(21, "MS408-Q14-FOLDOUT-COMPLEX", leaf_id=leaf_id),
        relation(22, "MS408-Q14-FOLDOUT-COMPLEX", leaf_id=leaf_id),
        relation(23, "MS408-Q10-FOLDOUT-COMPLEX"),
        relation(24, "MS408-Q11-FOLDOUT-COMPLEX"),
    ]

    records, summary = build_candidate_records(pages=pages, foldout_relations=relations)
    reversed_records, reversed_summary = build_candidate_records(
        pages=list(reversed(pages)), foldout_relations=list(reversed(relations))
    )

    assert records == reversed_records
    assert summary == reversed_summary
    assert summary["explicit_leaf_panel_count"] == 2
    assert summary["foldout_complexes_represented"] == 3
    assert summary["sequence_bins_represented"] == 8
    assert summary["ordinary_candidate_count"] == 16
    assert all(record["visual_review_status"] == "pending" for record in records)
    assert not any(record["external_transliteration_consulted"] for record in records)
    assert "YDC-PANEL-2025" not in {record["photographic_panel_id"] for record in records}
    assert {record["candidate_id"] for record in records} == {
        f"PILOT-0001-CAND-{index:03d}" for index in range(1, len(records) + 1)
    }


def test_candidate_freeze_is_hash_stable(tmp_path: Path) -> None:
    pages = [page(index) for index in range(1, 17)]
    records, _ = build_candidate_records(pages=pages, foldout_relations=[])
    pages_path = tmp_path / "pages.jsonl"
    relations_path = tmp_path / "relations.csv"
    pages_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in pages),
        encoding="utf-8",
    )
    relations_path.write_text(
        "photographic_panel_id,complex_id,physical_leaf_id\n",
        encoding="utf-8",
    )

    freeze = build_candidate_freeze(
        records=records,
        pages_path=pages_path,
        foldout_relations_path=relations_path,
    )

    assert freeze["candidate_set_sha256"] == canonical_records_sha256(records)
    assert freeze["visual_outcomes_used"] is False
    assert freeze["external_transliterations_used"] is False
    assert freeze["status"] == "frozen"
