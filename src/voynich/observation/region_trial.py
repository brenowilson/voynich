"""Deterministic preparation and validation for a region-only annotation trial."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from .lifecycle import validate_transition
from .model import canonical_sha256, validate_package
from .work_queue import canonical_records_sha256


class RegionAnnotationTrialError(RuntimeError):
    """Raised when the controlled region trial violates its preregistered rules."""


TRIAL_ID = "REGION-ANNOTATION-TRIAL-0001"
SELECTION_RULE = "lowest-source-sequence-single-side-per-work-queue-batch"
REGION_ROLES = {
    "text_bearing",
    "graphic_bearing",
    "mixed",
    "unmarked_or_background",
    "obscured_or_damaged",
    "uncertain",
}


def _unique_index(
    rows: Iterable[dict[str, Any]], key: str, label: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            raise RegionAnnotationTrialError(f"{label}: missing {key}")
        if value in result:
            raise RegionAnnotationTrialError(f"{label}: duplicate {key} {value}")
        result[value] = row
    return result


def select_trial_entries(
    *, work_queue: dict[str, Any], candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Select one metadata-eligible package from each deterministic queue batch."""

    if work_queue.get("status") != "ready":
        raise RegionAnnotationTrialError("work queue is not ready")
    for flag in (
        "interpretive_outputs_used",
        "external_transliterations_used",
        "final_pilot_selection_used",
    ):
        if work_queue.get(flag) is not False:
            raise RegionAnnotationTrialError(f"work queue violates {flag}")

    candidate_index = _unique_index(candidates, "candidate_id", "candidate set")
    queue_entries = work_queue.get("entries")
    if not isinstance(queue_entries, list):
        raise RegionAnnotationTrialError("work queue entries must be an array")

    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in queue_entries:
        candidate_id = str(entry.get("candidate_id") or "")
        candidate = candidate_index.get(candidate_id)
        if candidate is None:
            raise RegionAnnotationTrialError(
                f"work queue names unknown candidate {candidate_id}"
            )
        if entry.get("source_sha256") != candidate.get("source_sha256"):
            raise RegionAnnotationTrialError(
                f"candidate {candidate_id} source SHA-256 mismatch"
            )
        batch_id = str(entry.get("batch_id") or "")
        grouped.setdefault(batch_id, []).append({"entry": entry, "candidate": candidate})

    expected_batches = int(work_queue.get("batch_count") or 0)
    if expected_batches != 5 or len(grouped) != 5:
        raise RegionAnnotationTrialError("trial requires exactly five work-queue batches")

    selected: list[dict[str, Any]] = []
    for batch_id in sorted(grouped):
        eligible = [
            pair
            for pair in grouped[batch_id]
            if pair["candidate"].get("composition_status")
            == "single_side_or_unspecified"
        ]
        if not eligible:
            raise RegionAnnotationTrialError(
                f"batch {batch_id} has no eligible single-side package"
            )
        chosen = min(
            eligible,
            key=lambda pair: (
                int(pair["entry"]["sequence_index"]),
                str(pair["entry"]["candidate_id"]),
            ),
        )
        entry = chosen["entry"]
        candidate = chosen["candidate"]
        selected.append(
            {
                "batch_id": batch_id,
                "candidate_id": str(entry["candidate_id"]),
                "photographic_panel_id": str(entry["photographic_panel_id"]),
                "sequence_index": int(entry["sequence_index"]),
                "composition_status": str(candidate["composition_status"]),
                "source_sha256": str(entry["source_sha256"]),
                "blank_package_id": str(entry["package_id"]),
                "blank_package_path": str(entry["package_path"]),
                "blank_package_sha256": str(entry["package_sha256"]),
                "selection_reason": (
                    "Lowest canonical source-sequence entry in this batch with "
                    "composition_status=single_side_or_unspecified"
                ),
                "trial_annotation_status": "planned",
            }
        )

    if len({row["candidate_id"] for row in selected}) != 5:
        raise RegionAnnotationTrialError("trial candidate selection is not unique")
    if len({row["photographic_panel_id"] for row in selected}) != 5:
        raise RegionAnnotationTrialError("trial panel selection is not unique")
    return selected


def build_trial_manifest(
    *, work_queue: dict[str, Any], candidates: list[dict[str, Any]]
) -> dict[str, Any]:
    entries = select_trial_entries(work_queue=work_queue, candidates=candidates)
    return {
        "schema_version": "0.1.0",
        "trial_id": TRIAL_ID,
        "status": "prepared",
        "observation_protocol_id": "OBSERVATION-PROTOCOL-0001",
        "lifecycle_protocol_id": "ANNOTATION-LIFECYCLE-0001",
        "work_queue_id": str(work_queue["queue_id"]),
        "candidate_set_sha256": str(work_queue["candidate_set_sha256"]),
        "work_queue_package_set_sha256": str(work_queue["package_set_sha256"]),
        "selection_rule": SELECTION_RULE,
        "selected_count": len(entries),
        "batch_count": len({row["batch_id"] for row in entries}),
        "trial_set_sha256": canonical_records_sha256(entries),
        "visual_outcomes_used": False,
        "external_transliterations_used": False,
        "final_pilot_selection_used": False,
        "scientific_adjudication_used": False,
        "production_freeze_authorized": False,
        "entries": entries,
    }


def validate_trial_manifest(
    *,
    manifest: dict[str, Any],
    work_queue: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = build_trial_manifest(work_queue=work_queue, candidates=candidates)
    if manifest != expected:
        raise RegionAnnotationTrialError(
            "trial manifest differs from deterministic metadata-only selection"
        )
    return {
        "trial_id": str(manifest["trial_id"]),
        "selected_count": int(manifest["selected_count"]),
        "batch_count": int(manifest["batch_count"]),
        "trial_set_sha256": str(manifest["trial_set_sha256"]),
    }


def _validate_regions(regions: list[dict[str, Any]], panel_id: str) -> None:
    if not regions:
        raise RegionAnnotationTrialError("region trial draft requires at least one region")
    region_ids: set[str] = set()
    for region in regions:
        region_id = str(region.get("region_id") or "")
        if not region_id or panel_id not in region_id:
            raise RegionAnnotationTrialError(
                f"region {region_id!r} does not belong to {panel_id}"
            )
        if region_id in region_ids:
            raise RegionAnnotationTrialError(f"duplicate region ID {region_id}")
        region_ids.add(region_id)
        if region.get("role") not in REGION_ROLES:
            raise RegionAnnotationTrialError(
                f"region {region_id} has prohibited role {region.get('role')!r}"
            )


def start_region_draft(
    *,
    blank_package: dict[str, Any],
    regions: list[dict[str, Any]],
    annotator_id: str,
    created_at: str,
) -> dict[str, Any]:
    """Create a deterministic R001 region-only draft from an immutable R000 package."""

    blank_summary = validate_package(blank_package)
    if blank_summary["package_status"] != "blank":
        raise RegionAnnotationTrialError("trial draft must start from a blank package")
    if not annotator_id.startswith("OBS-"):
        raise RegionAnnotationTrialError("annotator_id must be a neutral OBS identifier")
    if "T" not in created_at:
        raise RegionAnnotationTrialError("created_at must be an ISO 8601 timestamp")

    panel_id = str(blank_package["source"]["photographic_panel_id"])
    ordered_regions = sorted(deepcopy(regions), key=lambda row: str(row.get("region_id")))
    _validate_regions(ordered_regions, panel_id)

    draft = deepcopy(blank_package)
    draft["package_id"] = f"OBS-PKG-{panel_id}-R001"
    draft["package_status"] = "draft"
    draft["annotator_id"] = annotator_id
    draft["revision"] = {
        "revision_number": 1,
        "supersedes_package_id": str(blank_package["package_id"]),
        "created_at": created_at,
    }
    draft["regions"] = ordered_regions
    draft["lines"] = []
    draft["glyph_candidates"] = []
    draft["ambiguity_groups"] = []
    draft["revision_events"] = []

    for index, region in enumerate(ordered_regions, start=1):
        draft["revision_events"].append(
            {
                "event_id": f"OBSEVENT-{panel_id}-{index:06d}",
                "event_type": "add",
                "entity_kind": "region",
                "entity_id": str(region["region_id"]),
                "actor_id": annotator_id,
                "occurred_at": created_at,
                "previous_entity_sha256": None,
                "resulting_entity_sha256": canonical_sha256(region),
                "reason": "Initial region-only controlled trial observation.",
                "uncertainty_change": "not_applicable",
            }
        )

    validate_package(draft)
    return draft


def build_blank_draft_lifecycle_records(
    *,
    blank_package: dict[str, Any],
    draft_package: dict[str, Any],
    actor_id: str,
    blank_recorded_at: str,
    draft_recorded_at: str,
) -> list[dict[str, Any]]:
    panel_id = str(blank_package["source"]["photographic_panel_id"])
    blank_record = {
        "schema_version": "0.1.0",
        "lifecycle_protocol_id": "ANNOTATION-LIFECYCLE-0001",
        "record_id": f"OBSLIFE-{panel_id}-000000",
        "state": "blank",
        "package_id": str(blank_package["package_id"]),
        "package_sha256": canonical_sha256(blank_package),
        "previous_record_id": None,
        "actor_id": actor_id,
        "occurred_at": blank_recorded_at,
        "technical_review": None,
        "freeze": None,
        "scientific_adjudication_used": False,
    }
    draft_record = {
        "schema_version": "0.1.0",
        "lifecycle_protocol_id": "ANNOTATION-LIFECYCLE-0001",
        "record_id": f"OBSLIFE-{panel_id}-000001",
        "state": "draft",
        "package_id": str(draft_package["package_id"]),
        "package_sha256": canonical_sha256(draft_package),
        "previous_record_id": blank_record["record_id"],
        "actor_id": actor_id,
        "occurred_at": draft_recorded_at,
        "technical_review": None,
        "freeze": None,
        "scientific_adjudication_used": False,
    }
    validate_transition(
        previous_record=blank_record,
        current_record=draft_record,
        previous_package=blank_package,
        current_package=draft_package,
    )
    return [blank_record, draft_record]


def validate_region_trial_draft(
    *,
    blank_package: dict[str, Any],
    draft_package: dict[str, Any],
    lifecycle_records: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(lifecycle_records) != 2:
        raise RegionAnnotationTrialError("trial requires blank and draft lifecycle records")
    if draft_package.get("lines") or draft_package.get("glyph_candidates"):
        raise RegionAnnotationTrialError("region-only trial cannot contain lines or glyphs")
    if draft_package.get("ambiguity_groups"):
        raise RegionAnnotationTrialError(
            "initial region-only trial does not authorize ambiguity groups"
        )
    if draft_package.get("package_status") != "draft":
        raise RegionAnnotationTrialError("trial package must remain draft")

    transition = validate_transition(
        previous_record=lifecycle_records[0],
        current_record=lifecycle_records[1],
        previous_package=blank_package,
        current_package=draft_package,
    )
    region_ids = {str(row["region_id"]) for row in draft_package.get("regions", [])}
    add_event_ids = {
        str(event["entity_id"])
        for event in draft_package.get("revision_events", [])
        if event.get("event_type") == "add" and event.get("entity_kind") == "region"
    }
    if region_ids != add_event_ids:
        raise RegionAnnotationTrialError("region add-event coverage is incomplete")

    return {
        "blank_package_id": str(blank_package["package_id"]),
        "draft_package_id": str(draft_package["package_id"]),
        "region_count": len(region_ids),
        "transition": f"{transition['from']}->{transition['to']}",
        "production_freeze_authorized": False,
    }
