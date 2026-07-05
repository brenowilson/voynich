"""Compare independent pilot observations and build adjudicated visual features.

The module preserves the primary and independent observations as immutable inputs.
It emits explicit field-level disputes and never silently chooses one observer over
another. Low-confidence records conservatively require review of every categorical
field.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


class PilotAdjudicationError(RuntimeError):
    """Raised when observation sets or adjudication decisions are invalid."""


ADJUDICATION_THRESHOLD = 0.70
CATEGORICAL_FIELDS = (
    "text_coverage",
    "graphic_coverage",
    "dominant_graphic_geometry",
    "line_organization",
    "visual_density",
    "color_presence",
    "source_quality",
    "crop_or_occlusion",
)

ALLOWED_VALUES: dict[str, set[str]] = {
    "text_coverage": {"none", "low", "medium", "high", "dominant", "uncertain"},
    "graphic_coverage": {"none", "low", "medium", "high", "dominant", "uncertain"},
    "dominant_graphic_geometry": {
        "none",
        "organic_branched",
        "circular_radial",
        "container_network",
        "human_figure_cluster",
        "mixed",
        "other_observable",
        "uncertain",
    },
    "line_organization": {"none", "clear", "ambiguous", "mixed", "uncertain"},
    "visual_density": {"sparse", "moderate", "dense", "very_dense", "uncertain"},
    "color_presence": {"none", "limited", "substantial", "uncertain"},
    "source_quality": {"good", "limited", "problematic", "uncertain"},
    "crop_or_occlusion": {"none", "present", "uncertain"},
}

DISPUTE_FIELDS = [
    "dispute_id",
    "candidate_id",
    "photographic_panel_id",
    "source_sha256",
    "field_name",
    "trigger",
    "primary_value",
    "independent_value",
    "primary_observer_id",
    "independent_observer_id",
    "primary_confidence",
    "independent_confidence",
    "resolution_status",
    "adjudicated_value",
    "adjudicator_id",
    "adjudicated_at",
    "adjudication_confidence",
    "notes",
]

IMMUTABLE_DISPUTE_FIELDS = tuple(DISPUTE_FIELDS[:12])


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PilotAdjudicationError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != DISPUTE_FIELDS:
            raise PilotAdjudicationError(
                f"unexpected dispute columns: {reader.fieldnames}; expected {DISPUTE_FIELDS}"
            )
        return list(reader)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def write_disputes_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DISPUTE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_records_sha256(rows: Iterable[dict[str, Any]]) -> str:
    lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def unique_index(
    rows: Iterable[dict[str, Any]], key: str, source: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            raise PilotAdjudicationError(f"{source}: missing {key}")
        if value in result:
            raise PilotAdjudicationError(f"{source}: duplicate {key} {value}")
        result[value] = row
    return result


def _validate_observation(
    *,
    candidate: dict[str, Any],
    observation: dict[str, Any],
    candidate_id: str,
    expected_pass: str,
) -> None:
    if observation.get("review_pass") != expected_pass:
        raise PilotAdjudicationError(
            f"{candidate_id}: expected review_pass={expected_pass}"
        )
    if observation.get("pilot_id") != "PILOT-0001":
        raise PilotAdjudicationError(f"{candidate_id}: wrong pilot_id")
    if observation.get("photographic_panel_id") != candidate.get(
        "photographic_panel_id"
    ):
        raise PilotAdjudicationError(f"{candidate_id}: panel identifier mismatch")
    if observation.get("source_sha256") != candidate.get("source_sha256"):
        raise PilotAdjudicationError(f"{candidate_id}: source SHA-256 mismatch")
    if observation.get("external_transliteration_consulted") is not False:
        raise PilotAdjudicationError(f"{candidate_id}: contaminated observation")
    if observation.get("semantic_section_assignment") is not None:
        raise PilotAdjudicationError(
            f"{candidate_id}: semantic section assignment is forbidden"
        )
    try:
        confidence = float(observation["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PilotAdjudicationError(f"{candidate_id}: invalid confidence") from exc
    if not 0 <= confidence <= 1:
        raise PilotAdjudicationError(f"{candidate_id}: confidence outside 0..1")
    for field in CATEGORICAL_FIELDS:
        value = str(observation.get(field) or "")
        if value not in ALLOWED_VALUES[field]:
            raise PilotAdjudicationError(
                f"{candidate_id}: invalid {field}={value!r}"
            )


def validate_observation_sets(
    *,
    candidates: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    independent: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    candidates_by_id = unique_index(candidates, "candidate_id", "candidate set")
    primary_by_id = unique_index(primary, "candidate_id", "primary observations")
    independent_by_id = unique_index(
        independent, "candidate_id", "independent observations"
    )

    expected = set(candidates_by_id)
    if set(primary_by_id) != expected:
        raise PilotAdjudicationError("primary observation set does not match candidates")
    if set(independent_by_id) != expected:
        raise PilotAdjudicationError(
            "independent observation set does not match candidates"
        )

    for candidate_id in sorted(expected):
        candidate = candidates_by_id[candidate_id]
        primary_row = primary_by_id[candidate_id]
        independent_row = independent_by_id[candidate_id]
        _validate_observation(
            candidate=candidate,
            observation=primary_row,
            candidate_id=candidate_id,
            expected_pass="primary",
        )
        _validate_observation(
            candidate=candidate,
            observation=independent_row,
            candidate_id=candidate_id,
            expected_pass="independent_second",
        )
        if primary_row.get("observer_id") == independent_row.get("observer_id"):
            raise PilotAdjudicationError(
                f"{candidate_id}: primary and independent observer must differ"
            )

    return candidates_by_id, primary_by_id, independent_by_id


def build_dispute_rows(
    *,
    candidates: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    independent: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    candidates_by_id, primary_by_id, independent_by_id = validate_observation_sets(
        candidates=candidates,
        primary=primary,
        independent=independent,
    )

    disputes: list[dict[str, Any]] = []
    direct_disagreement_rows = 0
    low_confidence_rows = 0
    candidates_requiring_review: set[str] = set()

    for candidate_id in sorted(candidates_by_id):
        candidate = candidates_by_id[candidate_id]
        primary_row = primary_by_id[candidate_id]
        independent_row = independent_by_id[candidate_id]
        primary_confidence = float(primary_row["confidence"])
        independent_confidence = float(independent_row["confidence"])
        low_confidence = (
            primary_confidence < ADJUDICATION_THRESHOLD
            or independent_confidence < ADJUDICATION_THRESHOLD
        )

        for field in CATEGORICAL_FIELDS:
            primary_value = str(primary_row[field])
            independent_value = str(independent_row[field])
            disagrees = primary_value != independent_value
            if not disagrees and not low_confidence:
                continue

            triggers: list[str] = []
            if disagrees:
                triggers.append("categorical_disagreement")
                direct_disagreement_rows += 1
            if low_confidence:
                triggers.append("low_confidence")
                low_confidence_rows += 1
            candidates_requiring_review.add(candidate_id)
            disputes.append(
                {
                    "dispute_id": "",
                    "candidate_id": candidate_id,
                    "photographic_panel_id": str(candidate["photographic_panel_id"]),
                    "source_sha256": str(candidate["source_sha256"]),
                    "field_name": field,
                    "trigger": ";".join(triggers),
                    "primary_value": primary_value,
                    "independent_value": independent_value,
                    "primary_observer_id": str(primary_row["observer_id"]),
                    "independent_observer_id": str(independent_row["observer_id"]),
                    "primary_confidence": f"{primary_confidence:.6f}",
                    "independent_confidence": f"{independent_confidence:.6f}",
                    "resolution_status": "pending",
                    "adjudicated_value": "",
                    "adjudicator_id": "",
                    "adjudicated_at": "",
                    "adjudication_confidence": "",
                    "notes": "",
                }
            )

    for index, row in enumerate(disputes, start=1):
        row["dispute_id"] = f"PILOT-0001-DIS-{index:03d}"

    summary = {
        "candidate_count": len(candidates_by_id),
        "dispute_row_count": len(disputes),
        "candidates_requiring_adjudication": len(candidates_requiring_review),
        "fully_agreeing_candidate_count": len(candidates_by_id)
        - len(candidates_requiring_review),
        "direct_disagreement_row_count": direct_disagreement_rows,
        "low_confidence_triggered_row_count": low_confidence_rows,
    }
    return disputes, summary


def _validate_completed_decisions(
    *,
    expected_disputes: list[dict[str, Any]],
    completed_decisions: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    expected_by_id = unique_index(
        expected_disputes, "dispute_id", "expected disputes"
    )
    completed_by_id = unique_index(
        completed_decisions, "dispute_id", "completed decisions"
    )
    if set(completed_by_id) != set(expected_by_id):
        raise PilotAdjudicationError(
            "completed adjudication set does not match expected disputes"
        )

    for dispute_id in sorted(expected_by_id):
        expected = expected_by_id[dispute_id]
        completed = completed_by_id[dispute_id]
        for field in IMMUTABLE_DISPUTE_FIELDS:
            if str(completed.get(field, "")) != str(expected.get(field, "")):
                raise PilotAdjudicationError(
                    f"{dispute_id}: immutable dispute field {field} was altered"
                )

        status = completed.get("resolution_status", "").strip()
        if status not in {"resolved", "retain_uncertainty"}:
            raise PilotAdjudicationError(
                f"{dispute_id}: invalid resolution_status={status!r}"
            )
        field_name = str(expected["field_name"])
        adjudicated_value = completed.get("adjudicated_value", "").strip()
        if status == "retain_uncertainty":
            if adjudicated_value != "uncertain":
                raise PilotAdjudicationError(
                    f"{dispute_id}: retained uncertainty must use value 'uncertain'"
                )
        elif adjudicated_value not in ALLOWED_VALUES[field_name]:
            raise PilotAdjudicationError(
                f"{dispute_id}: invalid adjudicated value {adjudicated_value!r}"
            )

        adjudicator_id = completed.get("adjudicator_id", "").strip()
        if not adjudicator_id.startswith("OBS-"):
            raise PilotAdjudicationError(f"{dispute_id}: invalid adjudicator_id")
        if adjudicator_id in {
            str(expected["primary_observer_id"]),
            str(expected["independent_observer_id"]),
        }:
            raise PilotAdjudicationError(
                f"{dispute_id}: adjudicator must differ from both observers"
            )
        if "T" not in completed.get("adjudicated_at", ""):
            raise PilotAdjudicationError(
                f"{dispute_id}: adjudicated_at must be ISO 8601"
            )
        try:
            confidence = float(completed.get("adjudication_confidence", ""))
        except ValueError as exc:
            raise PilotAdjudicationError(
                f"{dispute_id}: adjudication_confidence must be numeric"
            ) from exc
        if not 0 <= confidence <= 1:
            raise PilotAdjudicationError(
                f"{dispute_id}: adjudication_confidence outside 0..1"
            )

    return completed_by_id


def build_final_feature_records(
    *,
    candidates: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    independent: list[dict[str, Any]],
    completed_decisions: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    candidates_by_id, primary_by_id, independent_by_id = validate_observation_sets(
        candidates=candidates,
        primary=primary,
        independent=independent,
    )
    expected_disputes, dispute_summary = build_dispute_rows(
        candidates=candidates,
        primary=primary,
        independent=independent,
    )
    completed_by_id = _validate_completed_decisions(
        expected_disputes=expected_disputes,
        completed_decisions=completed_decisions,
    )

    disputes_by_candidate_field = {
        (str(row["candidate_id"]), str(row["field_name"])): row
        for row in expected_disputes
    }
    completed_by_candidate_field = {
        (str(row["candidate_id"]), str(row["field_name"])): row
        for row in completed_by_id.values()
    }

    records: list[dict[str, Any]] = []
    retained_uncertainty_count = 0
    adjudicated_field_count = 0

    for candidate_id in sorted(candidates_by_id):
        candidate = candidates_by_id[candidate_id]
        primary_row = primary_by_id[candidate_id]
        independent_row = independent_by_id[candidate_id]
        final_values: dict[str, str] = {}
        field_resolution: dict[str, str] = {}
        dispute_ids: list[str] = []
        adjudicator_ids: set[str] = set()
        adjudication_confidences: list[float] = []

        for field in CATEGORICAL_FIELDS:
            key = (candidate_id, field)
            if key not in disputes_by_candidate_field:
                if primary_row[field] != independent_row[field]:
                    raise PilotAdjudicationError(
                        f"{candidate_id}: unregistered disagreement for {field}"
                    )
                final_values[field] = str(primary_row[field])
                field_resolution[field] = "observer_agreement"
                continue

            expected = disputes_by_candidate_field[key]
            completed = completed_by_candidate_field[key]
            value = str(completed["adjudicated_value"])
            final_values[field] = value
            field_resolution[field] = str(completed["resolution_status"])
            dispute_ids.append(str(expected["dispute_id"]))
            adjudicator_ids.add(str(completed["adjudicator_id"]))
            adjudication_confidences.append(
                float(completed["adjudication_confidence"])
            )
            adjudicated_field_count += 1
            if completed["resolution_status"] == "retain_uncertainty":
                retained_uncertainty_count += 1

        final_confidence = (
            min(adjudication_confidences)
            if adjudication_confidences
            else min(float(primary_row["confidence"]), float(independent_row["confidence"]))
        )
        records.append(
            {
                "schema_version": "0.1.0",
                "pilot_id": "PILOT-0001",
                "candidate_id": candidate_id,
                "photographic_panel_id": str(candidate["photographic_panel_id"]),
                "source_sha256": str(candidate["source_sha256"]),
                **final_values,
                "primary_observer_id": str(primary_row["observer_id"]),
                "independent_observer_id": str(independent_row["observer_id"]),
                "primary_confidence": float(primary_row["confidence"]),
                "independent_confidence": float(independent_row["confidence"]),
                "final_confidence": final_confidence,
                "adjudication_required": bool(dispute_ids),
                "dispute_ids": sorted(dispute_ids),
                "adjudicator_ids": sorted(adjudicator_ids),
                "field_resolution": field_resolution,
                "external_transliterations_used": False,
                "semantic_sections_used": False,
            }
        )

    summary = {
        **dispute_summary,
        "final_feature_record_count": len(records),
        "adjudicated_field_count": adjudicated_field_count,
        "retained_uncertainty_field_count": retained_uncertainty_count,
    }
    return records, summary


def build_observation_freeze(
    *,
    records: list[dict[str, Any]],
    candidates_path: Path,
    primary_path: Path,
    independent_path: Path,
    decisions_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "freeze_id": "PILOT-OBSERVATIONS-FREEZE-0001",
        "pilot_id": "PILOT-0001",
        "status": "frozen",
        "record_count": len(records),
        "final_feature_set_sha256": canonical_records_sha256(records),
        "candidate_set_path": "corpus/pilots/PILOT-0001/candidates.jsonl",
        "candidate_set_file_sha256": file_sha256(candidates_path),
        "primary_observations_path": "corpus/pilots/PILOT-0001/visual-observations.jsonl",
        "primary_observations_file_sha256": file_sha256(primary_path),
        "independent_observations_path": "corpus/pilots/PILOT-0001/independent-observations.jsonl",
        "independent_observations_file_sha256": file_sha256(independent_path),
        "adjudication_decisions_path": "corpus/pilots/PILOT-0001/adjudication.csv",
        "adjudication_decisions_file_sha256": file_sha256(decisions_path),
        "external_transliterations_used": False,
        "semantic_sections_used": False,
        "final_selection_authorized": True,
    }
