import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


def load_schema() -> dict:
    return json.loads(
        Path("schemas/annotation-lifecycle-record.schema.json").read_text(
            encoding="utf-8"
        )
    )


def base_record(state: str) -> dict:
    return {
        "schema_version": "0.1.0",
        "lifecycle_protocol_id": "ANNOTATION-LIFECYCLE-0001",
        "record_id": "OBSLIFE-YDC-PANEL-1006094-000001",
        "state": state,
        "package_id": "OBS-PKG-YDC-PANEL-1006094-R001",
        "package_sha256": "a" * 64,
        "previous_record_id": "OBSLIFE-YDC-PANEL-1006094-000000",
        "actor_id": "OBS-LIFECYCLE-01",
        "occurred_at": "2026-07-07T12:00:00Z",
        "technical_review": None,
        "freeze": None,
        "scientific_adjudication_used": False,
    }


def accepted_review() -> dict:
    fields = [
        "source_identity_verified",
        "source_pixel_coordinates_verified",
        "geometry_validated",
        "entity_ids_validated",
        "revision_events_validated",
        "ambiguities_preserved",
        "prohibited_fields_absent",
        "predecessor_chain_validated",
        "deterministic_revalidation_passed",
    ]
    return {
        "reviewer_id": "OBS-TECH-REVIEWER-02",
        "reviewed_at": "2026-07-07T12:30:00Z",
        "outcome": "accepted",
        "checklist": {field: True for field in fields},
    }


def freeze_record() -> dict:
    return {
        "freeze_id": "OBS-PACKAGE-FREEZE-YDC-PANEL-1006094-R001",
        "frozen_at": "2026-07-07T13:00:00Z",
        "package_sha256": "a" * 64,
        "source_sha256": "b" * 64,
        "predecessor_package_ids": ["OBS-PKG-YDC-PANEL-1006094-R000"],
        "protocol_versions": {
            "observation": "OBSERVATION-PROTOCOL-0001",
            "lifecycle": "ANNOTATION-LIFECYCLE-0001",
            "package_schema": "0.1.0",
        },
        "immutable": True,
    }


def errors(record: dict) -> list:
    validator = Draft202012Validator(load_schema(), format_checker=FormatChecker())
    return list(validator.iter_errors(record))


def test_draft_rejects_review_and_freeze_payloads() -> None:
    record = base_record("draft")
    assert not errors(record)

    record["technical_review"] = accepted_review()
    assert errors(record)


def test_reviewed_requires_review_but_no_freeze() -> None:
    record = base_record("reviewed")
    assert errors(record)

    record["technical_review"] = accepted_review()
    assert not errors(record)

    record["freeze"] = freeze_record()
    assert errors(record)


def test_frozen_requires_review_and_freeze() -> None:
    record = base_record("frozen")
    record["technical_review"] = accepted_review()
    assert errors(record)

    record["freeze"] = freeze_record()
    assert not errors(record)
