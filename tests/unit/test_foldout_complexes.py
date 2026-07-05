import pytest

from voynich.acquisition.foldout_complexes import (
    FoldoutComplexError,
    build_complexes,
    validate_codicology_profile,
)


def page(
    sequence_index: int,
    oid: str,
    side_ids: list[str],
    *,
    candidate: bool = False,
) -> dict:
    return {
        "sequence_index": sequence_index,
        "record_type": "manuscript_image",
        "institutional_id": oid,
        "institutional_label": " and ".join(side_ids),
        "photographic_panel_id": f"YDC-PANEL-{oid}",
        "physical_parent_ids": side_ids,
        "side_relations": [
            {
                "side_id": side_id,
                "coverage": "full_or_unspecified",
            }
            for side_id in side_ids
        ],
        "composition_status": "composite_candidate" if candidate else "single_side_or_unspecified",
    }


def config(*, reading_order=None) -> dict:
    return {
        "source_url": "https://example.org/catalog",
        "evidence_scope": "institutional collation",
        "folding_leaf_totals": {
            "double": 1,
            "triple": 0,
            "quadruple": 0,
            "sextuple": 0,
        },
        "complexes": [
            {
                "complex_id": "MS408-Q16-FOLDOUT-COMPLEX",
                "quire_id": "XVI",
                "folio_min": 93,
                "folio_max": 96,
                "folding_leaf_profile": {
                    "double": 1,
                    "triple": 0,
                    "quadruple": 0,
                    "sextuple": 0,
                },
                "assignment_status": "quire_profile_supported",
                "geometry_status": "panel_geometry_unresolved",
                "reading_order": reading_order,
                "evidence_note": "one double folding leaf",
            }
        ],
    }


def test_builds_complex_and_panel_relations_without_reading_order() -> None:
    pages = [
        page(1, "1001", ["93r"]),
        page(2, "1002", ["94v", "95r"], candidate=True),
        page(3, "1003", ["96v"]),
    ]
    complexes, relations, summary = build_complexes(pages=pages, config=config())

    assert summary == {
        "complex_count": 1,
        "panel_relation_count": 3,
        "label_candidate_panel_count": 1,
        "folding_leaf_count": 1,
    }
    assert complexes[0]["side_ids"] == ["93r", "94v", "95r", "96v"]
    assert complexes[0]["reading_order"] is None
    assert complexes[0]["panel_count"] == 3
    assert all(row["reading_order"] == "" for row in relations)
    assert all(row["physical_leaf_id"] == "" for row in relations)


def test_rejects_catalog_total_mismatch() -> None:
    value = config()
    value["folding_leaf_totals"]["double"] = 2
    with pytest.raises(FoldoutComplexError, match="do not match totals"):
        validate_codicology_profile(value)


def test_rejects_non_null_reading_order() -> None:
    with pytest.raises(FoldoutComplexError, match="reading order must remain null"):
        validate_codicology_profile(config(reading_order=["93r", "93v"]))


def test_rejects_candidate_outside_catalog_complexes() -> None:
    pages = [
        page(1, "1001", ["93r"]),
        page(2, "1002", ["70v"], candidate=True),
    ]
    with pytest.raises(FoldoutComplexError, match="outside codicological complexes"):
        build_complexes(pages=pages, config=config())


def test_rejects_overlapping_complex_ranges() -> None:
    value = config()
    second = dict(value["complexes"][0])
    second.update(
        {
            "complex_id": "MS408-Q17-FOLDOUT-COMPLEX",
            "quire_id": "XVII",
            "folio_min": 96,
            "folio_max": 102,
            "folding_leaf_profile": {
                "double": 0,
                "triple": 0,
                "quadruple": 0,
                "sextuple": 0,
            },
        }
    )
    value["complexes"].append(second)
    with pytest.raises(FoldoutComplexError, match="overlapping folio ranges"):
        validate_codicology_profile(value)
