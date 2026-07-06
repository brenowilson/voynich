"""Deterministic lifecycle transitions for observation packages.

Blank revision-zero packages are immutable templates. Annotation begins in a new
revision, and frozen revisions are never modified in place.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re
from typing import Any

from .model import canonical_sha256, validate_package


class ObservationLifecycleError(RuntimeError):
    """Raised when a package lifecycle transition is invalid."""


ANNOTATOR_PATTERN = re.compile(r"^OBS-[A-Z0-9-]+$")
ENTITY_COLLECTIONS = {
    "regions": ("region_id", "region"),
    "lines": ("line_id", "line"),
    "glyph_candidates": ("glyph_id", "glyph_candidate"),
    "ambiguity_groups": ("ambiguity_group_id", "ambiguity_group"),
}


def _parse_timestamp(value: str, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ObservationLifecycleError(f"{label} must be an explicit timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationLifecycleError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ObservationLifecycleError(f"{label} must include a timezone")
    return parsed


def _validate_annotator_id(annotator_id: str) -> None:
    if not isinstance(annotator_id, str) or not ANNOTATOR_PATTERN.fullmatch(annotator_id):
        raise ObservationLifecycleError(
            "annotator_id must match ^OBS-[A-Z0-9-]+$"
        )


def _source_identity(package: dict[str, Any]) -> dict[str, Any]:
    source = package["source"]
    coordinate_space = package["coordinate_space"]
    return {
        "photographic_panel_id": source["photographic_panel_id"],
        "institutional_id": source["institutional_id"],
        "source_url": source["source_url"],
        "source_sha256": source["source_sha256"],
        "stored_path": source["stored_path"],
        "width_px": source["width_px"],
        "height_px": source["height_px"],
        "coordinate_width_px": coordinate_space["width_px"],
        "coordinate_height_px": coordinate_space["height_px"],
        "coordinate_units": coordinate_space["units"],
    }


def start_draft(
    package: dict[str, Any], *, annotator_id: str, created_at: str
) -> dict[str, Any]:
    """Start a new draft revision from a blank or frozen package.

    The input package is not modified. A blank R000 becomes draft R001. A
    frozen Rn becomes draft R(n+1), preserving current entities but resetting
    revision-local events.
    """

    validate_package(package)
    status = package.get("package_status")
    if status not in {"blank", "frozen"}:
        raise ObservationLifecycleError(
            f"drafts can start only from blank or frozen packages, not {status!r}"
        )
    _validate_annotator_id(annotator_id)
    _parse_timestamp(created_at, "created_at")

    before_source = _source_identity(package)
    previous_package_id = str(package["package_id"])
    next_revision = int(package["revision"]["revision_number"]) + 1
    panel_id = str(package["source"]["photographic_panel_id"])

    draft = deepcopy(package)
    draft["package_id"] = f"OBS-PKG-{panel_id}-R{next_revision:03d}"
    draft["package_status"] = "draft"
    draft["annotator_id"] = annotator_id
    draft["revision"] = {
        "revision_number": next_revision,
        "supersedes_package_id": previous_package_id,
        "created_at": created_at,
    }
    draft["revision_events"] = []

    if _source_identity(draft) != before_source:
        raise ObservationLifecycleError("source identity changed during draft transition")
    validate_package(draft)
    return draft


def _index_entities(
    package: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    entities: dict[str, dict[str, Any]] = {}
    kinds: dict[str, str] = {}
    for collection, (id_key, kind) in ENTITY_COLLECTIONS.items():
        for entity in package.get(collection, []):
            entity_id = str(entity[id_key])
            if entity_id in entities:
                raise ObservationLifecycleError(f"duplicate entity ID {entity_id}")
            entities[entity_id] = entity
            kinds[entity_id] = kind
    return entities, kinds


def _validate_event_coverage(
    package: dict[str, Any], *, frozen_at: str
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    entities, kinds = _index_entities(package)
    if not entities:
        raise ObservationLifecycleError("a draft cannot be frozen without observations")

    created_dt = _parse_timestamp(package["revision"]["created_at"], "created_at")
    frozen_dt = _parse_timestamp(frozen_at, "frozen_at")
    if frozen_dt < created_dt:
        raise ObservationLifecycleError("frozen_at precedes the draft creation time")

    annotator_id = str(package["annotator_id"])
    events = package.get("revision_events", [])
    if not events:
        raise ObservationLifecycleError("a draft cannot be frozen without revision events")

    events_by_entity: dict[str, list[dict[str, Any]]] = {
        entity_id: [] for entity_id in entities
    }
    previous_time: datetime | None = None
    for event in events:
        event_id = str(event.get("event_id") or "")
        event_dt = _parse_timestamp(str(event.get("occurred_at") or ""), event_id)
        if event_dt < created_dt or event_dt > frozen_dt:
            raise ObservationLifecycleError(
                f"event {event_id} lies outside the draft-to-freeze interval"
            )
        if previous_time is not None and event_dt < previous_time:
            raise ObservationLifecycleError("revision events must be chronological")
        previous_time = event_dt

        if event.get("actor_id") != annotator_id:
            raise ObservationLifecycleError(
                f"event {event_id} actor differs from package annotator"
            )
        entity_id = str(event.get("entity_id") or "")
        if entity_id not in entities:
            raise ObservationLifecycleError(
                f"event {event_id} refers to an unknown entity"
            )
        if event.get("entity_kind") != kinds[entity_id]:
            raise ObservationLifecycleError(
                f"event {event_id} entity_kind does not match {entity_id}"
            )
        events_by_entity[entity_id].append(event)

    counts = {collection: len(package.get(collection, [])) for collection in ENTITY_COLLECTIONS}
    for entity_id, entity in entities.items():
        entity_events = events_by_entity[entity_id]
        if not entity_events:
            raise ObservationLifecycleError(
                f"entity {entity_id} has no revision-event coverage"
            )
        latest = entity_events[-1]
        status = entity.get("observation_status", "active")
        if status == "retired":
            if latest.get("event_type") != "retire":
                raise ObservationLifecycleError(
                    f"retired entity {entity_id} lacks a final retire event"
                )
            if latest.get("resulting_entity_sha256") is not None:
                raise ObservationLifecycleError(
                    f"retire event for {entity_id} must have a null resulting hash"
                )
        else:
            if latest.get("event_type") == "retire":
                raise ObservationLifecycleError(
                    f"active entity {entity_id} ends with a retire event"
                )
            expected = canonical_sha256(entity)
            if latest.get("resulting_entity_sha256") != expected:
                raise ObservationLifecycleError(
                    f"latest event hash does not match active entity {entity_id}"
                )

    return entities, counts


def freeze_draft(
    package: dict[str, Any], *, frozen_at: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Freeze a fully covered draft and create its immutable freeze record."""

    validate_package(package)
    if package.get("package_status") != "draft":
        raise ObservationLifecycleError("only draft packages can be frozen")

    before_source = _source_identity(package)
    _, counts = _validate_event_coverage(package, frozen_at=frozen_at)

    frozen = deepcopy(package)
    frozen["package_status"] = "frozen"
    if _source_identity(frozen) != before_source:
        raise ObservationLifecycleError("source identity changed during freeze")
    validate_package(frozen)

    panel_id = str(frozen["source"]["photographic_panel_id"])
    revision_number = int(frozen["revision"]["revision_number"])
    freeze_record = {
        "schema_version": "0.1.0",
        "freeze_id": f"OBS-FREEZE-{panel_id}-R{revision_number:03d}",
        "protocol_id": "OBSERVATION-PROTOCOL-0001",
        "status": "frozen",
        "package_id": str(frozen["package_id"]),
        "package_sha256": canonical_sha256(frozen),
        "photographic_panel_id": panel_id,
        "source_sha256": str(frozen["source"]["source_sha256"]),
        "revision_number": revision_number,
        "supersedes_package_id": frozen["revision"]["supersedes_package_id"],
        "annotator_id": str(frozen["annotator_id"]),
        "created_at": str(frozen["revision"]["created_at"]),
        "frozen_at": frozen_at,
        "entity_counts": counts,
        "revision_event_count": len(frozen["revision_events"]),
        "external_transliterations_used": False,
        "semantic_interpretation_used": False,
        "reading_order_asserted": False,
    }
    validate_freeze_record(frozen, freeze_record)
    return frozen, freeze_record


def validate_freeze_record(
    package: dict[str, Any], freeze_record: dict[str, Any]
) -> dict[str, Any]:
    """Validate a freeze record against its frozen package."""

    validate_package(package)
    if package.get("package_status") != "frozen":
        raise ObservationLifecycleError("freeze records require a frozen package")

    panel_id = str(package["source"]["photographic_panel_id"])
    revision_number = int(package["revision"]["revision_number"])
    expected_freeze_id = f"OBS-FREEZE-{panel_id}-R{revision_number:03d}"
    expected = {
        "freeze_id": expected_freeze_id,
        "package_id": package["package_id"],
        "package_sha256": canonical_sha256(package),
        "photographic_panel_id": panel_id,
        "source_sha256": package["source"]["source_sha256"],
        "revision_number": revision_number,
        "supersedes_package_id": package["revision"]["supersedes_package_id"],
        "annotator_id": package["annotator_id"],
        "created_at": package["revision"]["created_at"],
        "revision_event_count": len(package["revision_events"]),
    }
    for key, value in expected.items():
        if freeze_record.get(key) != value:
            raise ObservationLifecycleError(f"freeze record mismatch for {key}")

    for key in (
        "external_transliterations_used",
        "semantic_interpretation_used",
        "reading_order_asserted",
    ):
        if freeze_record.get(key) is not False:
            raise ObservationLifecycleError(f"freeze record violates {key}")

    created_dt = _parse_timestamp(str(freeze_record.get("created_at") or ""), "created_at")
    frozen_dt = _parse_timestamp(str(freeze_record.get("frozen_at") or ""), "frozen_at")
    if frozen_dt < created_dt:
        raise ObservationLifecycleError("freeze record time precedes draft creation")

    counts = {collection: len(package.get(collection, [])) for collection in ENTITY_COLLECTIONS}
    if freeze_record.get("entity_counts") != counts:
        raise ObservationLifecycleError("freeze record entity counts do not match package")

    return {
        "freeze_id": expected_freeze_id,
        "package_id": str(package["package_id"]),
        "package_sha256": canonical_sha256(package),
        "entity_count": sum(counts.values()),
        "revision_event_count": len(package["revision_events"]),
    }
