from copy import deepcopy

import pytest

from voynich.observation.lifecycle import (
    AnnotationLifecycleError,
    all_review_checks,
    validate_lifecycle_chain,
    validate_lifecycle_record,
    validate_transition,
)
from voynich.observation.model import build_blank_package, canonical_sha256


def panel() -> dict:
    return {
        "photographic_panel_id": "YDC-PANEL-1006094",
        "institutional_id": "1006094",
        "institutional_label": "10r",
        "source_url": "https://collections.library.yale.edu/iiif/2/1006094/full/full/0/default.jpg",
        "source_sha256": "ab22d0c20cc0c4e754236a32960c650c7275ac9a51e0dd33c91060694cb6ac05",
        "stored_path": "sha256/ab/ab22d0c20cc0c4e754236a32960c650c7275ac9a51e0dd33be44ba6c4615839.jpg".replace(
            "e5ec7be49ff17b8ea978ecaecd803ae04b6e6f4ee92cdfdd3be44ba6c4615839",
            "ab22d0c20cc0c4e754236a32960c650c7275ac9a51e0dd33c91060694cb6ac05",
        ),
        "width_px": 2691,
        "height_px": 3739,
        "acquisition_status": "verified",
    }


def blank_package() -> dict:
    return build_blank_package(panel())


def region(visibility: str = "uncertain") -> dict:
    return {
        "region_id": "OBSREG-YDC-PANEL-1006094-0001",
        "role": "text_bearing",
        "polygon": [[100, 100], [900, 100], [900, 600], [100, 600]],
        "confidence": 0.7,
        "visibility": visibility,
        "observation_status": "active",
        "evidence_note": "Visible bounded mark field.",
    }


def draft_from(previous: dict, revision: int, *, visibility: str = "uncertain") -> dict:
    package = deepcopy(previous)
    package["package_id"] = f"OBS-PKG-YDC-PANEL-1006094-R{revision:03d}"
    package["package_status"] = "draft"
    package["annotator_id"] = "OBS-ANNOTATOR-01"
    package["revision"] = {
        "revision_number": revision,
        "supersedes_package_id": previous["package_id"],
        "created_at": f"2026-07-07T0{revision}:00:00Z",
    }
    previous_regions = {item["region_id"]: item for item in previous.get("regions", [])}
    current_region = region(visibility)
    package["regions"] = [current_region]
    package["lines"] = []
    package["glyph_candidates"] = []
    package["ambiguity_groups"] = []
    if current_region["region_id"] not in previous_regions:
        package["revision_events"] = [
            {
                "event_id": f"OBSEVENT-YDC-PANEL-1006094-{revision:06d}",
                "event_type": "add",
                "entity_kind": "region",
                "entity_id": current_region["region_id"],
                "actor_id": "OBS-ANNOTATOR-01",
                "occurred_at": f"2026-07-07T0{revision}:01:00Z",
                "previous_entity_sha256": None,
                "resulting_entity_sha256": canonical_sha256(current_region),
                "reason": "Initial visible-region observation.",
                "uncertainty_change": "not_applicable",
            }
        ]
    else:
        previous_region = previous_regions[current_region["region_id"]]
        package["revision_events"] = [
            {
                "event_id": f"OBSEVENT-YDC-PANEL-1006094-{revision:06d}",
                "event_type": "uncertainty_update",
                "entity_kind": "region",
                "entity_id": current_region["region_id"],
                "actor_id": "OBS-ANNOTATOR-01",
                "occurred_at": f"2026-07-07T0{revision}:01:00Z",
                "previous_entity_sha256": canonical_sha256(previous_region),
                "resulting_entity_sha256": canonical_sha256(current_region),
                "reason": "Boundary visibility clarified from the source image.",
                "uncertainty_change": "decreased",
            }
        ]
    return package


def frozen_from(reviewed_package: dict, revision: int) -> dict:
    package = deepcopy(reviewed_package)
    package["package_id"] = f"OBS-PKG-YDC-PANEL-1006094-R{revision:03d}"
    package["package_status"] = "frozen"
    package["revision"] = {
        "revision_number": revision,
        "supersedes_package_id": reviewed_package["package_id"],
        "created_at": f"2026-07-07T0{revision}:00:00Z",
    }
    return package


def review() -> dict:
    return {
        "reviewer_id": "OBS-TECH-REVIEWER-02",
        "reviewed_at": "2026-07-07T03:00:00Z",
        "outcome": "accepted",
        "checklist": all_review_checks(),
    }


def record(
    number: int,
    state: str,
    package: dict,
    previous_record_id: str | None,
    *,
    technical_review=None,
    freeze=None,
) -> dict:
    return {
        "schema_version": "0.1.0",
        "lifecycle_protocol_id": "ANNOTATION-LIFECYCLE-0001",
        "record_id": f"OBSLIFE-YDC-PANEL-1006094-{number:06d}",
        "state": state,
        "package_id": package["package_id"],
        "package_sha256": canonical_sha256(package),
        "previous_record_id": previous_record_id,
        "actor_id": "OBS-LIFECYCLE-01",
        "occurred_at": f"2026-07-07T{number:02d}:00:00Z",
        "technical_review": technical_review,
        "freeze": freeze,
        "scientific_adjudication_used": False,
    }


def valid_chain():
    blank = blank_package()
    draft = draft_from(blank, 1)
    reviewed = draft
    frozen = frozen_from(reviewed, 2)

    r0 = record(0, "blank", blank, None)
    r1 = record(1, "draft", draft, r0["record_id"])
    r2 = record(2, "reviewed", reviewed, r1["record_id"], technical_review=review())
    freeze_data = {
        "freeze_id": "OBS-PACKAGE-FREEZE-YDC-PANEL-1006094-R002",
        "frozen_at": "2026-07-07T04:00:00Z",
        "package_sha256": canonical_sha256(frozen),
        "source_sha256": frozen["source"]["source_sha256"],
        "predecessor_package_ids": [blank["package_id"], draft["package_id"]],
        "protocol_versions": {
            "observation": "OBSERVATION-PROTOCOL-0001",
            "lifecycle": "ANNOTATION-LIFECYCLE-0001",
            "package_schema": "0.1.0",
        },
        "immutable": True,
    }
    r3 = record(
        3,
        "frozen",
        frozen,
        r2["record_id"],
        technical_review=review(),
        freeze=freeze_data,
    )
    return [r0, r1, r2, r3], [blank, draft, reviewed, frozen]


def test_valid_blank_draft_reviewed_frozen_chain() -> None:
    records, packages = valid_chain()
    summary = validate_lifecycle_chain(records=records, packages=packages)

    assert summary["initial_state"] == "blank"
    assert summary["final_state"] == "frozen"
    assert summary["record_count"] == 4
    assert summary["package_revision_count"] == 3


def test_reviewed_state_references_identical_draft_bytes() -> None:
    records, packages = valid_chain()
    result = validate_transition(
        previous_record=records[1],
        current_record=records[2],
        previous_package=packages[1],
        current_package=packages[2],
    )
    assert result["from"] == "draft"
    assert result["to"] == "reviewed"

    changed = deepcopy(packages[2])
    changed["regions"][0]["confidence"] = 0.9
    records[2]["package_sha256"] = canonical_sha256(changed)
    with pytest.raises(AnnotationLifecycleError, match="identical immutable package bytes"):
        validate_transition(
            previous_record=records[1],
            current_record=records[2],
            previous_package=packages[1],
            current_package=changed,
        )


def test_rejects_direct_draft_to_frozen_transition() -> None:
    records, packages = valid_chain()
    with pytest.raises(AnnotationLifecycleError, match="forbidden lifecycle transition"):
        validate_transition(
            previous_record=records[1],
            current_record=records[3],
            previous_package=packages[1],
            current_package=packages[3],
        )


def test_rejects_reviewer_equal_to_annotator_or_failed_checklist() -> None:
    records, packages = valid_chain()
    same_person = deepcopy(records[2])
    same_person["technical_review"]["reviewer_id"] = "OBS-ANNOTATOR-01"
    with pytest.raises(AnnotationLifecycleError, match="must differ"):
        validate_lifecycle_record(same_person, packages[2])

    failed = deepcopy(records[2])
    failed["technical_review"]["checklist"]["geometry_validated"] = False
    with pytest.raises(AnnotationLifecycleError, match="checklist failed"):
        validate_lifecycle_record(failed, packages[2])


def test_rejects_silent_entity_disappearance() -> None:
    records, packages = valid_chain()
    previous = packages[1]
    current = draft_from(previous, 2)
    current["regions"] = []
    current["revision_events"] = []
    current_record = record(4, "draft", current, records[1]["record_id"])

    with pytest.raises(AnnotationLifecycleError, match="disappeared"):
        validate_transition(
            previous_record=records[1],
            current_record=current_record,
            previous_package=previous,
            current_package=current,
        )


def test_reduced_uncertainty_requires_explicit_event() -> None:
    records, packages = valid_chain()
    previous = packages[1]
    current = draft_from(previous, 2, visibility="clear")
    current_record = record(4, "draft", current, records[1]["record_id"])
    validate_transition(
        previous_record=records[1],
        current_record=current_record,
        previous_package=previous,
        current_package=current,
    )

    current["revision_events"][0]["event_type"] = "modify"
    current_record["package_sha256"] = canonical_sha256(current)
    with pytest.raises(AnnotationLifecycleError, match="uncertainty_update"):
        validate_transition(
            previous_record=records[1],
            current_record=current_record,
            previous_package=previous,
            current_package=current,
        )


def test_frozen_package_cannot_return_to_editable_state() -> None:
    records, packages = valid_chain()
    draft = draft_from(packages[3], 3)
    draft_record = record(4, "draft", draft, records[3]["record_id"])
    with pytest.raises(AnnotationLifecycleError, match="forbidden lifecycle transition"):
        validate_transition(
            previous_record=records[3],
            current_record=draft_record,
            previous_package=packages[3],
            current_package=draft,
        )


def test_freeze_requires_complete_predecessor_chain_and_provenance() -> None:
    records, packages = valid_chain()
    records[3]["freeze"]["predecessor_package_ids"] = [packages[1]["package_id"]]
    with pytest.raises(AnnotationLifecycleError, match="predecessor chain"):
        validate_lifecycle_chain(records=records, packages=packages)

    records, packages = valid_chain()
    packages[1]["revision_events"] = []
    packages[2] = packages[1]
    records[1]["package_sha256"] = canonical_sha256(packages[1])
    records[2]["package_sha256"] = canonical_sha256(packages[2])
    packages[3] = frozen_from(packages[2], 2)
    records[3]["package_id"] = packages[3]["package_id"]
    records[3]["package_sha256"] = canonical_sha256(packages[3])
    records[3]["freeze"]["package_sha256"] = canonical_sha256(packages[3])
    with pytest.raises(AnnotationLifecycleError):
        validate_lifecycle_chain(records=records, packages=packages)
