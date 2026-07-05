"""Create and import blinded PILOT-0001 independent-review forms."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


class IndependentReviewError(RuntimeError):
    """Raised when an independent-review form is incomplete or contaminated."""


FORM_FIELDS = [
    "candidate_id",
    "photographic_panel_id",
    "source_url",
    "source_sha256",
    "observer_id",
    "reviewed_at",
    "text_coverage",
    "graphic_coverage",
    "dominant_graphic_geometry",
    "line_organization",
    "visual_density",
    "color_presence",
    "source_quality",
    "crop_or_occlusion",
    "confidence",
    "semantic_section_assignment",
    "external_transliteration_consulted",
    "notes",
]

TEXT_COVERAGE = {"none", "low", "medium", "high", "dominant", "uncertain"}
GRAPHIC_COVERAGE = TEXT_COVERAGE
GRAPHIC_GEOMETRY = {
    "none",
    "organic_branched",
    "circular_radial",
    "container_network",
    "human_figure_cluster",
    "mixed",
    "other_observable",
    "uncertain",
}
LINE_ORGANIZATION = {"none", "clear", "ambiguous", "mixed", "uncertain"}
VISUAL_DENSITY = {"sparse", "moderate", "dense", "very_dense", "uncertain"}
COLOR_PRESENCE = {"none", "limited", "substantial", "uncertain"}
SOURCE_QUALITY = {"good", "limited", "problematic", "uncertain"}
CROP_OR_OCCLUSION = {"none", "present", "uncertain"}
PRIMARY_OBSERVER_IDS = {"OBS-AI-PRIMARY-01"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise IndependentReviewError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FORM_FIELDS:
            raise IndependentReviewError(
                f"unexpected form columns: {reader.fieldnames}; expected {FORM_FIELDS}"
            )
        return list(reader)


def candidate_index(candidates: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id or candidate_id in result:
            raise IndependentReviewError(f"missing or duplicate candidate_id: {candidate_id}")
        result[candidate_id] = candidate
    return result


def build_template_rows(candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for candidate in sorted(candidates, key=lambda row: str(row["candidate_id"])):
        rows.append(
            {
                "candidate_id": str(candidate["candidate_id"]),
                "photographic_panel_id": str(candidate["photographic_panel_id"]),
                "source_url": str(candidate["source_url"]),
                "source_sha256": str(candidate["source_sha256"]),
                "observer_id": "",
                "reviewed_at": "",
                "text_coverage": "",
                "graphic_coverage": "",
                "dominant_graphic_geometry": "",
                "line_organization": "",
                "visual_density": "",
                "color_presence": "",
                "source_quality": "",
                "crop_or_occlusion": "",
                "confidence": "",
                "semantic_section_assignment": "",
                "external_transliteration_consulted": "false",
                "notes": "",
            }
        )
    return rows


def write_template(path: Path, candidates: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FORM_FIELDS)
        writer.writeheader()
        writer.writerows(build_template_rows(candidates))


def validate_template_rows(
    *, candidates: list[dict[str, Any]], rows: list[dict[str, str]]
) -> None:
    expected = build_template_rows(candidates)
    if rows != expected:
        raise IndependentReviewError(
            "review template differs from the deterministic blinded candidate export"
        )


def require_enum(row: dict[str, str], field: str, allowed: set[str]) -> str:
    value = row[field].strip()
    if value not in allowed:
        raise IndependentReviewError(
            f"{row['candidate_id']}: invalid {field}={value!r}; allowed={sorted(allowed)}"
        )
    return value


def import_completed_rows(
    *, candidates: list[dict[str, Any]], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    candidates_by_id = candidate_index(candidates)
    if len(rows) != len(candidates_by_id):
        raise IndependentReviewError(
            f"expected {len(candidates_by_id)} completed rows, found {len(rows)}"
        )

    seen: set[str] = set()
    observations: list[dict[str, Any]] = []
    observer_ids: set[str] = set()

    for row in rows:
        candidate_id = row["candidate_id"].strip()
        if candidate_id in seen:
            raise IndependentReviewError(f"duplicate completed row: {candidate_id}")
        seen.add(candidate_id)
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            raise IndependentReviewError(f"unknown candidate: {candidate_id}")

        immutable = {
            "photographic_panel_id": str(candidate["photographic_panel_id"]),
            "source_url": str(candidate["source_url"]),
            "source_sha256": str(candidate["source_sha256"]),
        }
        for field, expected in immutable.items():
            if row[field].strip() != expected:
                raise IndependentReviewError(
                    f"{candidate_id}: immutable field {field} was altered"
                )

        observer_id = row["observer_id"].strip()
        if not observer_id.startswith("OBS-"):
            raise IndependentReviewError(f"{candidate_id}: invalid observer_id")
        if observer_id in PRIMARY_OBSERVER_IDS:
            raise IndependentReviewError(
                f"{candidate_id}: independent observer must differ from the primary observer"
            )
        observer_ids.add(observer_id)

        reviewed_at = row["reviewed_at"].strip()
        if "T" not in reviewed_at:
            raise IndependentReviewError(f"{candidate_id}: reviewed_at must be ISO 8601")
        if row["semantic_section_assignment"].strip():
            raise IndependentReviewError(
                f"{candidate_id}: semantic section assignment is forbidden"
            )
        if row["external_transliteration_consulted"].strip().lower() != "false":
            raise IndependentReviewError(f"{candidate_id}: contaminated review")

        try:
            confidence = float(row["confidence"])
        except ValueError as exc:
            raise IndependentReviewError(
                f"{candidate_id}: confidence must be numeric"
            ) from exc
        if not 0 <= confidence <= 1:
            raise IndependentReviewError(f"{candidate_id}: confidence outside 0..1")

        observations.append(
            {
                "schema_version": "0.1.0",
                "pilot_id": "PILOT-0001",
                "candidate_id": candidate_id,
                "photographic_panel_id": immutable["photographic_panel_id"],
                "source_sha256": immutable["source_sha256"],
                "observer_id": observer_id,
                "review_pass": "independent_second",
                "reviewed_at": reviewed_at,
                "text_coverage": require_enum(row, "text_coverage", TEXT_COVERAGE),
                "graphic_coverage": require_enum(
                    row, "graphic_coverage", GRAPHIC_COVERAGE
                ),
                "dominant_graphic_geometry": require_enum(
                    row, "dominant_graphic_geometry", GRAPHIC_GEOMETRY
                ),
                "line_organization": require_enum(
                    row, "line_organization", LINE_ORGANIZATION
                ),
                "visual_density": require_enum(
                    row, "visual_density", VISUAL_DENSITY
                ),
                "color_presence": require_enum(
                    row, "color_presence", COLOR_PRESENCE
                ),
                "source_quality": require_enum(
                    row, "source_quality", SOURCE_QUALITY
                ),
                "crop_or_occlusion": require_enum(
                    row, "crop_or_occlusion", CROP_OR_OCCLUSION
                ),
                "confidence": confidence,
                "semantic_section_assignment": None,
                "external_transliteration_consulted": False,
                "notes": row["notes"].strip() or None,
            }
        )

    if seen != set(candidates_by_id):
        raise IndependentReviewError("completed form does not cover the frozen candidate set")
    if len(observer_ids) != 1:
        raise IndependentReviewError(
            f"one completed form must contain one independent observer; found {observer_ids}"
        )

    observations.sort(key=lambda row: row["candidate_id"])
    return observations


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")
