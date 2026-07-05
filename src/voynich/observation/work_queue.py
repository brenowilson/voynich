"""Build deterministic blank observation packages for a frozen candidate set."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .model import (
    ObservationValidationError,
    build_blank_package,
    canonical_sha256,
    read_jsonl,
    validate_package,
)


class ObservationWorkQueueError(RuntimeError):
    """Raised when a work queue cannot be built from frozen canonical inputs."""


def canonical_records_sha256(records: Iterable[dict[str, Any]]) -> str:
    payload = "\n".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def unique_index(
    rows: Iterable[dict[str, Any]], key: str, source: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            raise ObservationWorkQueueError(f"{source}: missing {key}")
        if value in result:
            raise ObservationWorkQueueError(f"{source}: duplicate {key} {value}")
        result[value] = row
    return result


def build_work_queue(
    *,
    candidates: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    candidate_freeze: dict[str, Any],
    package_root: str,
    batch_count: int = 5,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if batch_count <= 0:
        raise ObservationWorkQueueError("batch_count must be positive")

    candidate_digest = canonical_records_sha256(candidates)
    if candidate_digest != candidate_freeze.get("candidate_set_sha256"):
        raise ObservationWorkQueueError("candidate records do not match candidate freeze")
    if candidate_freeze.get("status") != "frozen":
        raise ObservationWorkQueueError("candidate set is not frozen")

    candidates_by_id = unique_index(candidates, "candidate_id", "candidate set")
    pages_by_panel = unique_index(pages, "photographic_panel_id", "page manifest")

    ordered_candidates = sorted(
        candidates,
        key=lambda row: (
            int(row["sequence_index"]),
            str(row["candidate_id"]),
        ),
    )
    packages: dict[str, dict[str, Any]] = {}
    entries: list[dict[str, Any]] = []

    for position, candidate in enumerate(ordered_candidates, start=1):
        candidate_id = str(candidate["candidate_id"])
        panel_id = str(candidate["photographic_panel_id"])
        page = pages_by_panel.get(panel_id)
        if page is None:
            raise ObservationWorkQueueError(
                f"candidate {candidate_id} names unknown panel {panel_id}"
            )
        if str(candidate["source_sha256"]) != str(page.get("source_sha256") or ""):
            raise ObservationWorkQueueError(
                f"candidate {candidate_id} source SHA-256 differs from page manifest"
            )
        if int(candidate["width_px"]) != int(page.get("width_px") or 0) or int(
            candidate["height_px"]
        ) != int(page.get("height_px") or 0):
            raise ObservationWorkQueueError(
                f"candidate {candidate_id} dimensions differ from page manifest"
            )

        package = build_blank_package(page)
        try:
            validate_package(package)
        except ObservationValidationError as exc:
            raise ObservationWorkQueueError(
                f"candidate {candidate_id} produced an invalid package: {exc}"
            ) from exc

        package_path = f"{package_root.rstrip('/')}/{candidate_id}.json"
        package_digest = canonical_sha256(package)
        batch_number = ((position - 1) % batch_count) + 1
        batch_id = f"OBS-BATCH-PILOT-0001-{batch_number:02d}"

        packages[package_path] = package
        entries.append(
            {
                "candidate_id": candidate_id,
                "photographic_panel_id": panel_id,
                "sequence_index": int(candidate["sequence_index"]),
                "source_sha256": str(candidate["source_sha256"]),
                "package_id": str(package["package_id"]),
                "package_path": package_path,
                "package_sha256": package_digest,
                "batch_id": batch_id,
                "annotation_status": "blank",
            }
        )

    if len(entries) != len(candidates_by_id):
        raise ObservationWorkQueueError("work queue does not cover every candidate")

    package_set_sha256 = canonical_records_sha256(entries)
    manifest = {
        "schema_version": "0.1.0",
        "queue_id": "OBS-WORK-QUEUE-PILOT-0001-0001",
        "protocol_id": "OBSERVATION-PROTOCOL-0001",
        "status": "ready",
        "candidate_freeze_id": str(candidate_freeze["freeze_id"]),
        "candidate_set_sha256": candidate_digest,
        "package_count": len(entries),
        "batch_count": batch_count,
        "batching_rule": "source-sequence-round-robin",
        "package_set_sha256": package_set_sha256,
        "interpretive_outputs_used": False,
        "external_transliterations_used": False,
        "final_pilot_selection_used": False,
        "entries": entries,
    }
    validate_work_queue(
        manifest=manifest,
        packages=packages,
        candidates=candidates,
        pages=pages,
        candidate_freeze=candidate_freeze,
    )
    return manifest, packages


def validate_work_queue(
    *,
    manifest: dict[str, Any],
    packages: dict[str, dict[str, Any]],
    candidates: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    candidate_freeze: dict[str, Any],
) -> dict[str, Any]:
    if manifest.get("interpretive_outputs_used") is not False:
        raise ObservationWorkQueueError("work queue used interpretive outputs")
    if manifest.get("external_transliterations_used") is not False:
        raise ObservationWorkQueueError("work queue used external transliterations")
    if manifest.get("final_pilot_selection_used") is not False:
        raise ObservationWorkQueueError("work queue used a final pilot selection")

    candidates_by_id = unique_index(candidates, "candidate_id", "candidate set")
    pages_by_panel = unique_index(pages, "photographic_panel_id", "page manifest")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ObservationWorkQueueError("manifest entries must be an array")
    entry_by_candidate = unique_index(entries, "candidate_id", "work queue")

    if set(entry_by_candidate) != set(candidates_by_id):
        missing = sorted(set(candidates_by_id) - set(entry_by_candidate))
        unexpected = sorted(set(entry_by_candidate) - set(candidates_by_id))
        raise ObservationWorkQueueError(
            f"candidate coverage mismatch; missing={missing}, unexpected={unexpected}"
        )

    package_ids: set[str] = set()
    panel_ids: set[str] = set()
    batch_ids: set[str] = set()
    for candidate_id, entry in entry_by_candidate.items():
        candidate = candidates_by_id[candidate_id]
        panel_id = str(entry.get("photographic_panel_id") or "")
        panel_ids.add(panel_id)
        if panel_id != candidate.get("photographic_panel_id"):
            raise ObservationWorkQueueError(f"{candidate_id}: panel mismatch")
        page = pages_by_panel.get(panel_id)
        if page is None:
            raise ObservationWorkQueueError(f"{candidate_id}: unknown panel")
        if entry.get("source_sha256") != candidate.get("source_sha256"):
            raise ObservationWorkQueueError(f"{candidate_id}: candidate hash mismatch")
        if entry.get("source_sha256") != page.get("source_sha256"):
            raise ObservationWorkQueueError(f"{candidate_id}: page hash mismatch")

        package_path = str(entry.get("package_path") or "")
        package = packages.get(package_path)
        if package is None:
            raise ObservationWorkQueueError(
                f"{candidate_id}: missing package file {package_path}"
            )
        validate_package(package)
        if package["source"]["photographic_panel_id"] != panel_id:
            raise ObservationWorkQueueError(f"{candidate_id}: package panel mismatch")
        if package["source"]["source_sha256"] != entry.get("source_sha256"):
            raise ObservationWorkQueueError(f"{candidate_id}: package source hash mismatch")
        if canonical_sha256(package) != entry.get("package_sha256"):
            raise ObservationWorkQueueError(f"{candidate_id}: package digest mismatch")
        if package.get("package_status") != "blank":
            raise ObservationWorkQueueError(f"{candidate_id}: package is not blank")

        package_id = str(package["package_id"])
        if package_id in package_ids:
            raise ObservationWorkQueueError(f"duplicate package ID {package_id}")
        package_ids.add(package_id)
        batch_ids.add(str(entry.get("batch_id") or ""))

    if len(panel_ids) != len(candidates):
        raise ObservationWorkQueueError("photographic panels are not unique")
    if manifest.get("package_count") != len(packages):
        raise ObservationWorkQueueError("manifest package count mismatch")
    if manifest.get("candidate_set_sha256") != candidate_freeze.get(
        "candidate_set_sha256"
    ):
        raise ObservationWorkQueueError("manifest candidate hash mismatch")
    if manifest.get("package_set_sha256") != canonical_records_sha256(entries):
        raise ObservationWorkQueueError("manifest package-set hash mismatch")
    if len(batch_ids) != int(manifest.get("batch_count") or 0):
        raise ObservationWorkQueueError("manifest batch count mismatch")

    batch_sizes: dict[str, int] = {}
    for entry in entries:
        batch_id = str(entry["batch_id"])
        batch_sizes[batch_id] = batch_sizes.get(batch_id, 0) + 1

    return {
        "queue_id": str(manifest.get("queue_id") or ""),
        "candidate_count": len(candidates),
        "package_count": len(packages),
        "batch_count": len(batch_ids),
        "batch_sizes": dict(sorted(batch_sizes.items())),
        "package_set_sha256": str(manifest.get("package_set_sha256") or ""),
    }


def write_work_queue(
    *,
    candidates_path: Path,
    pages_path: Path,
    candidate_freeze_path: Path,
    output_root: Path,
    batch_count: int = 5,
) -> dict[str, Any]:
    candidates = read_jsonl(candidates_path)
    pages = read_jsonl(pages_path)
    candidate_freeze = json.loads(candidate_freeze_path.read_text(encoding="utf-8"))
    package_root = f"{output_root.as_posix().rstrip('/')}/packages"
    manifest, packages = build_work_queue(
        candidates=candidates,
        pages=pages,
        candidate_freeze=candidate_freeze,
        package_root=package_root,
        batch_count=batch_count,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    for package_path, package in packages.items():
        path = Path(package_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(package, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
