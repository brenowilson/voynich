"""Validate annotation lifecycle transitions and package freeze gates."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .model import canonical_sha256, validate_package


class AnnotationLifecycleError(RuntimeError):
    """Raised when an annotation package lifecycle rule is violated."""


ALLOWED_TRANSITIONS = {
    ("blank", "draft"),
    ("draft", "draft"),
    ("draft", "reviewed"),
    ("reviewed", "draft"),
    ("reviewed", "frozen"),
    ("frozen", "superseded"),
}

STATE_PACKAGE_STATUS = {
    "blank": "blank",
    "draft": "draft",
    "reviewed": "draft",
    "frozen": "frozen",
    "superseded": "frozen",
}

ENTITY_COLLECTIONS = {
    "regions": "region_id",
    "lines": "line_id",
    "glyph_candidates": "glyph_id",
    "ambiguity_groups": "ambiguity_group_id",
}

REVIEW_CHECKLIST_FIELDS = {
    "source_identity_verified",
    "source_pixel_coordinates_verified",
    "geometry_validated",
    "entity_ids_validated",
    "revision_events_validated",
    "ambiguities_preserved",
    "prohibited_fields_absent",
    "predecessor_chain_validated",
    "deterministic_revalidation_passed",
}

UNCERTAIN_GLYPH_STATES = {
    "possible_join",
    "possible_split",
    "overlap",
    "uncertain_boundary",
    "not_fully_visible",
}

VISIBILITY_UNCERTAINTY = {
    "clear": 0,
    "partial": 1,
    "obscured": 2,
    "damaged": 2,
    "uncertain": 3,
}


def _panel_id(package: dict[str, Any]) -> str:
    return str(package["source"]["photographic_panel_id"])


def _revision_number(package: dict[str, Any]) -> int:
    return int(package["revision"]["revision_number"])


def _entity_index(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for collection, id_key in ENTITY_COLLECTIONS.items():
        for entity in package.get(collection, []):
            entity_id = str(entity[id_key])
            if entity_id in result:
                raise AnnotationLifecycleError(f"duplicate entity ID {entity_id}")
            result[entity_id] = entity
    return result


def _events_by_entity(package: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for event in package.get("revision_events", []):
        result.setdefault(str(event["entity_id"]), []).append(event)
    return result


def _observational_payload(package: dict[str, Any]) -> dict[str, Any]:
    return {
        key: package.get(key, [])
        for key in ("regions", "lines", "glyph_candidates", "ambiguity_groups")
    }


def _source_identity(package: dict[str, Any]) -> tuple[Any, ...]:
    source = package["source"]
    return (
        source["photographic_panel_id"],
        source["institutional_id"],
        source["source_url"],
        source["source_sha256"],
        source["stored_path"],
        source["width_px"],
        source["height_px"],
    )


def _uncertainty_reduced(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    previous_visibility = VISIBILITY_UNCERTAINTY.get(str(previous.get("visibility")), 0)
    current_visibility = VISIBILITY_UNCERTAINTY.get(str(current.get("visibility")), 0)
    if current_visibility < previous_visibility:
        return True

    previous_segmentation = previous.get("segmentation_state")
    current_segmentation = current.get("segmentation_state")
    if (
        previous_segmentation in UNCERTAIN_GLYPH_STATES
        and current_segmentation not in UNCERTAIN_GLYPH_STATES
    ):
        return True

    if (
        previous.get("resolution_status") == "unresolved"
        and current.get("resolution_status") == "resolved"
    ):
        return True
    return False


def _validate_review(record: dict[str, Any], package: dict[str, Any]) -> None:
    review = record.get("technical_review")
    if not isinstance(review, dict):
        raise AnnotationLifecycleError("reviewed or frozen state requires technical review")
    if review.get("outcome") != "accepted":
        raise AnnotationLifecycleError("freeze gate requires an accepted technical review")
    reviewer_id = str(review.get("reviewer_id") or "")
    if not reviewer_id:
        raise AnnotationLifecycleError("technical review requires reviewer_id")
    if reviewer_id == package.get("annotator_id"):
        raise AnnotationLifecycleError("technical reviewer must differ from annotator")
    checklist = review.get("checklist")
    if not isinstance(checklist, dict):
        raise AnnotationLifecycleError("technical review checklist is missing")
    if set(checklist) != REVIEW_CHECKLIST_FIELDS:
        raise AnnotationLifecycleError("technical review checklist fields are incomplete")
    failed = sorted(key for key, value in checklist.items() if value is not True)
    if failed:
        raise AnnotationLifecycleError(f"technical review checklist failed: {failed}")


def validate_lifecycle_record(
    record: dict[str, Any], package: dict[str, Any]
) -> dict[str, Any]:
    """Validate one lifecycle record against the package it references."""

    package_summary = validate_package(package)
    state = str(record.get("state") or "")
    if state not in STATE_PACKAGE_STATUS:
        raise AnnotationLifecycleError(f"unknown lifecycle state {state!r}")
    if record.get("scientific_adjudication_used") is not False:
        raise AnnotationLifecycleError("scientific adjudication must remain separate")
    if record.get("package_id") != package.get("package_id"):
        raise AnnotationLifecycleError("lifecycle record package_id mismatch")
    package_digest = canonical_sha256(package)
    if record.get("package_sha256") != package_digest:
        raise AnnotationLifecycleError("lifecycle record package SHA-256 mismatch")
    expected_status = STATE_PACKAGE_STATUS[state]
    if package.get("package_status") != expected_status:
        raise AnnotationLifecycleError(
            f"state {state} requires package_status={expected_status}"
        )
    panel_id = _panel_id(package)
    record_id = str(record.get("record_id") or "")
    if panel_id not in record_id:
        raise AnnotationLifecycleError("lifecycle record belongs to another panel")

    if state in {"blank", "draft"}:
        if record.get("technical_review") is not None or record.get("freeze") is not None:
            raise AnnotationLifecycleError(f"{state} state cannot contain review or freeze")
    elif state == "reviewed":
        _validate_review(record, package)
        if record.get("freeze") is not None:
            raise AnnotationLifecycleError("reviewed state cannot contain freeze data")
    else:
        _validate_review(record, package)
        freeze = record.get("freeze")
        if not isinstance(freeze, dict):
            raise AnnotationLifecycleError("frozen state requires freeze data")
        if freeze.get("package_sha256") != package_digest:
            raise AnnotationLifecycleError("freeze package SHA-256 mismatch")
        if freeze.get("source_sha256") != package["source"]["source_sha256"]:
            raise AnnotationLifecycleError("freeze source SHA-256 mismatch")
        if freeze.get("immutable") is not True:
            raise AnnotationLifecycleError("freeze record must declare immutable=true")
        protocols = freeze.get("protocol_versions")
        if protocols != {
            "observation": "OBSERVATION-PROTOCOL-0001",
            "lifecycle": "ANNOTATION-LIFECYCLE-0001",
            "package_schema": "0.1.0",
        }:
            raise AnnotationLifecycleError("freeze protocol versions mismatch")

    return {
        "record_id": record_id,
        "state": state,
        "package_id": package_summary["package_id"],
        "package_sha256": package_digest,
    }


def _validate_new_revision(
    previous_package: dict[str, Any], current_package: dict[str, Any]
) -> None:
    if _source_identity(previous_package) != _source_identity(current_package):
        raise AnnotationLifecycleError("package source identity changed across revision")
    if _revision_number(current_package) != _revision_number(previous_package) + 1:
        raise AnnotationLifecycleError("package revision must increase by exactly one")
    if current_package["revision"].get("supersedes_package_id") != previous_package.get(
        "package_id"
    ):
        raise AnnotationLifecycleError("new revision must name its predecessor package")


def _validate_entity_changes(
    previous_package: dict[str, Any], current_package: dict[str, Any]
) -> None:
    previous_entities = _entity_index(previous_package)
    current_entities = _entity_index(current_package)
    events = _events_by_entity(current_package)

    missing = sorted(set(previous_entities) - set(current_entities))
    if missing:
        raise AnnotationLifecycleError(
            f"entities disappeared without retirement records: {missing}"
        )

    for entity_id, current in current_entities.items():
        previous = previous_entities.get(entity_id)
        entity_events = events.get(entity_id, [])
        if previous is None:
            matching = [event for event in entity_events if event.get("event_type") == "add"]
            if not matching:
                raise AnnotationLifecycleError(f"new entity {entity_id} lacks add event")
            continue

        previous_digest = canonical_sha256(previous)
        current_digest = canonical_sha256(current)
        if previous_digest == current_digest:
            continue

        matching = [
            event
            for event in entity_events
            if event.get("previous_entity_sha256") == previous_digest
            and event.get("resulting_entity_sha256") == current_digest
        ]
        if not matching:
            raise AnnotationLifecycleError(
                f"changed entity {entity_id} lacks matching revision event"
            )

        retired = (
            previous.get("observation_status") != "retired"
            and current.get("observation_status") == "retired"
        )
        if retired and not any(event.get("event_type") == "retire" for event in matching):
            raise AnnotationLifecycleError(f"retired entity {entity_id} lacks retire event")
        if _uncertainty_reduced(previous, current) and not any(
            event.get("event_type") == "uncertainty_update" for event in matching
        ):
            raise AnnotationLifecycleError(
                f"reduced uncertainty for {entity_id} lacks uncertainty_update event"
            )


def validate_transition(
    *,
    previous_record: dict[str, Any],
    current_record: dict[str, Any],
    previous_package: dict[str, Any],
    current_package: dict[str, Any],
) -> dict[str, Any]:
    """Validate an allowed lifecycle transition and its package revision rules."""

    previous = validate_lifecycle_record(previous_record, previous_package)
    current = validate_lifecycle_record(current_record, current_package)
    transition = (previous["state"], current["state"])
    if transition not in ALLOWED_TRANSITIONS:
        raise AnnotationLifecycleError(f"forbidden lifecycle transition {transition}")
    if current_record.get("previous_record_id") != previous_record.get("record_id"):
        raise AnnotationLifecycleError("lifecycle record predecessor mismatch")

    if transition in {("draft", "reviewed"), ("frozen", "superseded")}:
        if current_package != previous_package:
            raise AnnotationLifecycleError(
                f"transition {transition} must reference identical immutable package bytes"
            )
    else:
        _validate_new_revision(previous_package, current_package)
        _validate_entity_changes(previous_package, current_package)

    if transition == ("reviewed", "frozen"):
        if _observational_payload(previous_package) != _observational_payload(current_package):
            raise AnnotationLifecycleError(
                "reviewed to frozen transition cannot alter observational content"
            )

    return {
        "from": previous["state"],
        "to": current["state"],
        "previous_package_id": previous["package_id"],
        "current_package_id": current["package_id"],
    }


def validate_lifecycle_chain(
    *,
    records: Sequence[dict[str, Any]],
    packages: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Validate a complete ordered lifecycle chain and its freeze provenance."""

    if len(records) != len(packages) or not records:
        raise AnnotationLifecycleError("records and packages must be non-empty and aligned")
    if records[0].get("state") != "blank":
        raise AnnotationLifecycleError("lifecycle chain must begin in blank state")
    if records[0].get("previous_record_id") is not None:
        raise AnnotationLifecycleError("initial lifecycle record cannot have predecessor")

    record_ids: set[str] = set()
    for record, package in zip(records, packages):
        validate_lifecycle_record(record, package)
        record_id = str(record["record_id"])
        if record_id in record_ids:
            raise AnnotationLifecycleError(f"duplicate lifecycle record ID {record_id}")
        record_ids.add(record_id)

    for index in range(1, len(records)):
        validate_transition(
            previous_record=records[index - 1],
            current_record=records[index],
            previous_package=packages[index - 1],
            current_package=packages[index],
        )

    final_record = records[-1]
    final_package = packages[-1]
    if final_record.get("state") in {"frozen", "superseded"}:
        freeze = final_record["freeze"]
        expected_predecessors: list[str] = []
        for package in packages[:-1]:
            package_id = str(package["package_id"])
            if not expected_predecessors or expected_predecessors[-1] != package_id:
                expected_predecessors.append(package_id)
        if freeze.get("predecessor_package_ids") != expected_predecessors:
            raise AnnotationLifecycleError("freeze predecessor chain is incomplete")

        provenance_entities: set[str] = set()
        for package in packages:
            provenance_entities.update(
                str(event["entity_id"]) for event in package.get("revision_events", [])
            )
        final_entities = _entity_index(final_package)
        uncovered = sorted(set(final_entities) - provenance_entities)
        if uncovered:
            raise AnnotationLifecycleError(
                f"frozen entities lack provenance coverage: {uncovered}"
            )

    return {
        "record_count": len(records),
        "package_revision_count": len({package["package_id"] for package in packages}),
        "initial_state": str(records[0]["state"]),
        "final_state": str(final_record["state"]),
        "final_package_id": str(final_package["package_id"]),
        "final_package_sha256": canonical_sha256(final_package),
    }


def all_review_checks(value: bool = True) -> dict[str, bool]:
    """Return a complete deterministic technical-review checklist."""

    return {key: value for key in sorted(REVIEW_CHECKLIST_FIELDS)}


def predecessor_package_ids(packages: Iterable[dict[str, Any]]) -> list[str]:
    """Return package IDs without adjacent duplicates for freeze records."""

    result: list[str] = []
    for package in packages:
        package_id = str(package["package_id"])
        if not result or result[-1] != package_id:
            result.append(package_id)
    return result
