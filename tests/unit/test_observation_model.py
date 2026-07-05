from copy import deepcopy

import pytest

from voynich.observation.model import (
    ObservationValidationError,
    build_blank_package,
    canonical_sha256,
    validate_package,
)


def panel() -> dict:
    return {
        "photographic_panel_id": "YDC-PANEL-1006094",
        "institutional_id": "1006094",
        "institutional_label": "10r",
        "source_url": "https://collections.library.yale.edu/iiif/2/1006094/full/full/0/default.jpg",
        "source_sha256": "ab22d0c20cc0c4e754236a32960c650c7275ac9a51e0dd33c91060694cb6ac05",
        "stored_path": "sha256/ab/ab22d0c20cc0c4e754236a32960c650c7275ac9a51e0dd33c91060694cb6ac05.jpg",
        "width_px": 2691,
        "height_px": 3739,
        "acquisition_status": "verified",
    }


def draft_package() -> dict:
    package = build_blank_package(panel())
    package["package_status"] = "draft"
    package["annotator_id"] = "OBS-TEST-01"
    package["revision"]["created_at"] = "2026-07-05T18:30:00Z"
    package["regions"] = [
        {
            "region_id": "OBSREG-YDC-PANEL-1006094-0001",
            "role": "text_bearing",
            "polygon": [[100, 100], [900, 100], [900, 600], [100, 600]],
            "confidence": 0.8,
            "visibility": "clear",
            "observation_status": "active",
            "evidence_note": "Visible bounded mark field.",
        }
    ]
    package["lines"] = [
        {
            "line_id": "OBSLINE-YDC-PANEL-1006094-0001",
            "parent_region_id": "OBSREG-YDC-PANEL-1006094-0001",
            "polygon": [[150, 180], [850, 180], [850, 280], [150, 280]],
            "baseline": [[170, 250], [830, 250]],
            "orientation_degrees": 0.0,
            "confidence": 0.75,
            "visibility": "clear",
            "observation_status": "active",
            "evidence_note": None,
        }
    ]
    package["glyph_candidates"] = [
        {
            "glyph_id": "OBSGLYPH-YDC-PANEL-1006094-000001",
            "parent_region_id": "OBSREG-YDC-PANEL-1006094-0001",
            "parent_line_id": "OBSLINE-YDC-PANEL-1006094-0001",
            "polygon": [[200, 200], [250, 200], [250, 260], [200, 260]],
            "segmentation_state": "uncertain_boundary",
            "confidence": 0.6,
            "visibility": "clear",
            "observation_status": "active",
            "evidence_note": "Boundary is locally ambiguous.",
        },
        {
            "glyph_id": "OBSGLYPH-YDC-PANEL-1006094-000002",
            "parent_region_id": "OBSREG-YDC-PANEL-1006094-0001",
            "parent_line_id": "OBSLINE-YDC-PANEL-1006094-0001",
            "polygon": [[245, 200], [310, 200], [310, 260], [245, 260]],
            "segmentation_state": "possible_join",
            "confidence": 0.55,
            "visibility": "clear",
            "observation_status": "active",
            "evidence_note": "Contact with adjacent candidate.",
        },
    ]
    package["ambiguity_groups"] = [
        {
            "ambiguity_group_id": "OBSAMB-YDC-PANEL-1006094-0001",
            "relation": "possible_join",
            "member_entity_ids": [
                "OBSGLYPH-YDC-PANEL-1006094-000001",
                "OBSGLYPH-YDC-PANEL-1006094-000002",
            ],
            "resolution_status": "unresolved",
            "preferred_entity_ids": [],
            "evidence_note": "Retain both local boundary hypotheses.",
        }
    ]
    return package


def test_blank_package_is_deterministic_and_source_anchored() -> None:
    first = build_blank_package(panel())
    second = build_blank_package(panel())

    assert first == second
    assert first["package_id"] == "OBS-PKG-YDC-PANEL-1006094-R000"
    assert first["source"]["source_sha256"] == panel()["source_sha256"]
    assert first["coordinate_space"]["units"] == "source_pixels"
    assert first["regions"] == []
    assert validate_package(first)["package_status"] == "blank"


def test_valid_draft_preserves_ambiguous_segmentation() -> None:
    summary = validate_package(draft_package())

    assert summary["region_count"] == 1
    assert summary["line_count"] == 1
    assert summary["glyph_candidate_count"] == 2
    assert summary["ambiguity_group_count"] == 1


def test_rejects_forbidden_reading_order_and_transliteration_fields() -> None:
    package = draft_package()
    package["reading_order"] = ["OBSLINE-YDC-PANEL-1006094-0001"]
    with pytest.raises(ObservationValidationError, match="forbidden interpretive field"):
        validate_package(package)

    package = draft_package()
    package["glyph_candidates"][0]["transliteration"] = "x"
    with pytest.raises(ObservationValidationError, match="forbidden interpretive field"):
        validate_package(package)


def test_rejects_out_of_bounds_and_parent_geometry() -> None:
    package = draft_package()
    package["glyph_candidates"][0]["polygon"][0] = [3000, 200]
    with pytest.raises(ObservationValidationError, match="outside"):
        validate_package(package)

    package = draft_package()
    package["lines"][0]["polygon"] = [
        [50, 180],
        [850, 180],
        [850, 280],
        [50, 280],
    ]
    with pytest.raises(ObservationValidationError, match="parent"):
        validate_package(package)


def test_rejects_line_region_parent_disagreement() -> None:
    package = draft_package()
    package["regions"].append(
        {
            "region_id": "OBSREG-YDC-PANEL-1006094-0002",
            "role": "uncertain",
            "polygon": [[1000, 100], [1500, 100], [1500, 600], [1000, 600]],
            "confidence": 0.5,
            "visibility": "uncertain",
            "observation_status": "active",
            "evidence_note": None,
        }
    )
    package["glyph_candidates"][0]["parent_region_id"] = (
        "OBSREG-YDC-PANEL-1006094-0002"
    )
    with pytest.raises(ObservationValidationError, match="parents disagree"):
        validate_package(package)


def test_rejects_forced_preference_in_unresolved_ambiguity() -> None:
    package = draft_package()
    package["ambiguity_groups"][0]["preferred_entity_ids"] = [
        "OBSGLYPH-YDC-PANEL-1006094-000001"
    ]
    with pytest.raises(ObservationValidationError, match="cannot prefer"):
        validate_package(package)


def test_frozen_package_requires_matching_revision_event_hash() -> None:
    package = draft_package()
    package["package_status"] = "frozen"
    region = package["regions"][0]
    package["revision_events"] = [
        {
            "event_id": "OBSEVENT-YDC-PANEL-1006094-000001",
            "event_type": "add",
            "entity_kind": "region",
            "entity_id": region["region_id"],
            "actor_id": "OBS-TEST-01",
            "occurred_at": "2026-07-05T18:31:00Z",
            "previous_entity_sha256": None,
            "resulting_entity_sha256": canonical_sha256(region),
            "reason": "Initial visible-region observation.",
            "uncertainty_change": "not_applicable",
        }
    ]
    assert validate_package(package)["revision_event_count"] == 1

    broken = deepcopy(package)
    broken["revision_events"][0]["resulting_entity_sha256"] = "f" * 64
    with pytest.raises(ObservationValidationError, match="resulting hash"):
        validate_package(broken)
