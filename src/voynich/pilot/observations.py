"""Validate PILOT-0001 visual observations and build review checkpoints."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


class PilotObservationError(RuntimeError):
    """Raised when pilot observations are incomplete, mismatched or contaminated."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PilotObservationError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def canonical_records_sha256(records: Iterable[dict[str, Any]]) -> str:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def unique_index(
    rows: Iterable[dict[str, Any]], key: str, source: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            raise PilotObservationError(f"{source}: missing {key}")
        if value in result:
            raise PilotObservationError(f"{source}: duplicate {key} {value}")
        result[value] = row
    return result


def validate_primary_observations(
    *, candidates: list[dict[str, Any]], observations: list[dict[str, Any]]
) -> dict[str, Any]:
    candidates_by_id = unique_index(candidates, "candidate_id", "candidate set")
    observations_by_id = unique_index(observations, "candidate_id", "observation set")

    candidate_ids = set(candidates_by_id)
    observation_ids = set(observations_by_id)
    missing = sorted(candidate_ids - observation_ids)
    unexpected = sorted(observation_ids - candidate_ids)
    if missing or unexpected:
        raise PilotObservationError(
            f"candidate/observation mismatch; missing={missing}, unexpected={unexpected}"
        )

    for candidate_id in sorted(candidate_ids):
        candidate = candidates_by_id[candidate_id]
        observation = observations_by_id[candidate_id]
        if observation.get("review_pass") != "primary":
            raise PilotObservationError(f"{candidate_id}: expected primary review pass")
        if observation.get("pilot_id") != "PILOT-0001":
            raise PilotObservationError(f"{candidate_id}: wrong pilot_id")
        if observation.get("photographic_panel_id") != candidate.get("photographic_panel_id"):
            raise PilotObservationError(f"{candidate_id}: panel identifier mismatch")
        if observation.get("source_sha256") != candidate.get("source_sha256"):
            raise PilotObservationError(f"{candidate_id}: source SHA-256 mismatch")
        if observation.get("external_transliteration_consulted") is not False:
            raise PilotObservationError(f"{candidate_id}: contaminated review")
        if observation.get("semantic_section_assignment") is not None:
            raise PilotObservationError(f"{candidate_id}: semantic section assignment is forbidden")
        confidence = float(observation.get("confidence", -1))
        if not 0 <= confidence <= 1:
            raise PilotObservationError(f"{candidate_id}: invalid confidence")

    observer_counts = Counter(str(row["observer_id"]) for row in observations)
    return {
        "candidate_count": len(candidates),
        "observation_count": len(observations),
        "primary_pass_count": sum(row.get("review_pass") == "primary" for row in observations),
        "independent_second_pass_count": sum(
            row.get("review_pass") == "independent_second" for row in observations
        ),
        "adjudicated_pass_count": sum(
            row.get("review_pass") == "adjudicated" for row in observations
        ),
        "observer_count": len(observer_counts),
        "observer_ids": sorted(observer_counts),
        "observation_set_sha256": canonical_records_sha256(observations),
        "minimum_confidence": min(float(row["confidence"]) for row in observations),
        "maximum_confidence": max(float(row["confidence"]) for row in observations),
        "below_adjudication_threshold": sum(
            float(row["confidence"]) < 0.70 for row in observations
        ),
    }


def build_primary_checkpoint(
    *,
    candidates: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    candidate_set_sha256: str,
) -> dict[str, Any]:
    summary = validate_primary_observations(
        candidates=candidates,
        observations=observations,
    )
    return {
        "schema_version": "0.1.0",
        "checkpoint_id": "PILOT-PRIMARY-OBSERVATIONS-0001",
        "pilot_id": "PILOT-0001",
        "status": "primary-complete-independent-review-pending",
        "candidate_set_sha256": candidate_set_sha256,
        **summary,
        "visual_observation_schema": "schemas/pilot-visual-observation.schema.json",
        "selection_protocol": "docs/protocols/pilot-selection.md",
        "independent_review_required": True,
        "adjudication_required_after_disagreement": True,
        "final_selection_authorized": False,
        "external_transliterations_used": False,
        "semantic_sections_used": False,
    }


def write_primary_checkpoint(
    *,
    candidates_path: Path,
    observations_path: Path,
    candidate_freeze_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    candidate_freeze = json.loads(candidate_freeze_path.read_text(encoding="utf-8"))
    checkpoint = build_primary_checkpoint(
        candidates=read_jsonl(candidates_path),
        observations=read_jsonl(observations_path),
        candidate_set_sha256=str(candidate_freeze["candidate_set_sha256"]),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return checkpoint
