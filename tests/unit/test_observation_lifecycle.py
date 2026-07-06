from copy import deepcopy

import pytest

from voynich.observation.lifecycle import (
    ObservationLifecycleError,
    freeze_draft,
    start_draft,
    validate_freeze_record,
)
from voynich.observation.model import build_blank_package, canonical_sha256


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


def blank() -> dict:
    return build_blank_package(panel())


def draft_with_region() -> dict:
    draft = start_draft(
        blank(),
        annotator_id="OBS-TEST-01",
        created_at="2026-07-06T22:30:00Z",
    )
    region = {
        "region_id": "OBSREG-YDC-PANEL-1006094-0001",
        "role": "uncertain",
        "polygon": [[100, 100], [300, 100], [300, 300], [100, 300]],
        "confidence": 0.5,
        "visibility": "clear",
        "observation_status": "active",
        "evidence_note": "Synthetic unit-test geometry.",
    }
    draft["regions"] = [region]
    draft["revision_events"] = [
        {
            "event_id": "OBSEVENT-YDC-PANEL-1006094-000001",
            "event_type": "add",
            "entity_kind": "region",
            "entity_id": region["region_id"],
            "actor_id": "OBS-TEST-01",
            "occurred_at": "2026-07-06T22:45:00Z",
            "previous_entity_sha256": None,
            "resulting_entity_sha256": canonical_sha256(region),
            "reason": "Add synthetic region for lifecycle validation.",
            "uncertainty_change": "not_applicable",
        }
    ]
    return draft


def test_blank_starts_deterministic_r001_without_source_change() -> None:
    source = blank()
    source_copy = deepcopy(source)

    first = start_draft(
        source,
        annotator_id="OBS-TEST-01",
        created_at="2026-07-06T22:30:00Z",
    )
    second = start_draft(
        source,
        annotator_id="OBS-TEST-01",
        created_at="2026-07-06T22:30:00Z",
    )

    assert first == second
    assert source == source_copy
    assert first["package_id"] == "OBS-PKG-YDC-PANEL-1006094-R001"
    assert first["package_status"] == "draft"
    assert first["revision"]["supersedes_package_id"] == source["package_id"]
    assert first["source"] == source["source"]
    assert first["coordinate_space"] == source["coordinate_space"]
    assert first["revision_events"] == []


def test_freeze_is_deterministic_and_hash_bound() -> None:
    draft = draft_with_region()

    frozen, record = freeze_draft(
        draft,
        frozen_at="2026-07-06T23:00:00Z",
    )
    repeated_frozen, repeated_record = freeze_draft(
        draft,
        frozen_at="2026-07-06T23:00:00Z",
    )

    assert frozen == repeated_frozen
    assert record == repeated_record
    assert frozen["package_status"] == "frozen"
    assert record["freeze_id"] == "OBS-FREEZE-YDC-PANEL-1006094-R001"
    assert record["package_sha256"] == canonical_sha256(frozen)
    assert record["entity_counts"]["regions"] == 1
    assert validate_freeze_record(frozen, record)["entity_count"] == 1


def test_frozen_revision_starts_r002_without_mutating_r001() -> None:
    frozen, _ = freeze_draft(
        draft_with_region(),
        frozen_at="2026-07-06T23:00:00Z",
    )
    frozen_copy = deepcopy(frozen)

    next_draft = start_draft(
        frozen,
        annotator_id="OBS-TEST-02",
        created_at="2026-07-07T00:00:00Z",
    )

    assert frozen == frozen_copy
    assert next_draft["package_id"] == "OBS-PKG-YDC-PANEL-1006094-R002"
    assert next_draft["revision"]["supersedes_package_id"] == frozen["package_id"]
    assert next_draft["regions"] == frozen["regions"]
    assert next_draft["revision_events"] == []
    assert next_draft["source"] == frozen["source"]


def test_rejects_starting_from_draft_or_invalid_identity() -> None:
    draft = start_draft(
        blank(),
        annotator_id="OBS-TEST-01",
        created_at="2026-07-06T22:30:00Z",
    )
    with pytest.raises(ObservationLifecycleError, match="blank or frozen"):
        start_draft(
            draft,
            annotator_id="OBS-TEST-02",
            created_at="2026-07-06T23:00:00Z",
        )

    with pytest.raises(ObservationLifecycleError, match="annotator_id"):
        start_draft(
            blank(),
            annotator_id="human-1",
            created_at="2026-07-06T22:30:00Z",
        )

    with pytest.raises(ObservationLifecycleError, match="timezone"):
        start_draft(
            blank(),
            annotator_id="OBS-TEST-01",
            created_at="2026-07-06T22:30:00",
        )


def test_rejects_freeze_without_observations_or_events() -> None:
    empty = start_draft(
        blank(),
        annotator_id="OBS-TEST-01",
        created_at="2026-07-06T22:30:00Z",
    )
    with pytest.raises(ObservationLifecycleError, match="without observations"):
        freeze_draft(empty, frozen_at="2026-07-06T23:00:00Z")

    no_events = draft_with_region()
    no_events["revision_events"] = []
    with pytest.raises(ObservationLifecycleError, match="without revision events"):
        freeze_draft(no_events, frozen_at="2026-07-06T23:00:00Z")


def test_rejects_actor_hash_and_time_failures() -> None:
    wrong_actor = draft_with_region()
    wrong_actor["revision_events"][0]["actor_id"] = "OBS-OTHER-01"
    with pytest.raises(ObservationLifecycleError, match="actor differs"):
        freeze_draft(wrong_actor, frozen_at="2026-07-06T23:00:00Z")

    wrong_hash = draft_with_region()
    wrong_hash["revision_events"][0]["resulting_entity_sha256"] = "f" * 64
    with pytest.raises(ObservationLifecycleError, match="latest event hash"):
        freeze_draft(wrong_hash, frozen_at="2026-07-06T23:00:00Z")

    with pytest.raises(ObservationLifecycleError, match="precedes"):
        freeze_draft(
            draft_with_region(),
            frozen_at="2026-07-06T22:00:00Z",
        )


def test_rejects_uncovered_entity_and_tampered_record() -> None:
    uncovered = draft_with_region()
    second = deepcopy(uncovered["regions"][0])
    second["region_id"] = "OBSREG-YDC-PANEL-1006094-0002"
    second["polygon"] = [[400, 100], [600, 100], [600, 300], [400, 300]]
    uncovered["regions"].append(second)
    with pytest.raises(ObservationLifecycleError, match="no revision-event coverage"):
        freeze_draft(uncovered, frozen_at="2026-07-06T23:00:00Z")

    frozen, record = freeze_draft(
        draft_with_region(),
        frozen_at="2026-07-06T23:00:00Z",
    )
    tampered = deepcopy(record)
    tampered["package_sha256"] = "0" * 64
    with pytest.raises(ObservationLifecycleError, match="package_sha256"):
        validate_freeze_record(frozen, tampered)
