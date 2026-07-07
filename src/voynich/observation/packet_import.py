"""Import completed region authoring packets into validated draft bundles."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .authoring_packet import (
    RegionAuthoringPacketError,
    render_region_overlay,
    validate_completed_region_input,
)
from .model import canonical_sha256, validate_package
from .region_trial import validate_region_trial_draft
from .work_queue import canonical_records_sha256


class CompletedPacketImportError(RuntimeError):
    """Raised when a completed packet cannot be imported safely."""


def raw_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_import_bundle(
    *, packet: dict[str, Any], blank_package: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], str, dict[str, Any]]:
    """Convert a completed packet into a draft, lifecycle chain, overlay and manifest."""

    try:
        draft, lifecycle = validate_completed_region_input(
            packet=packet,
            blank_package=blank_package,
        )
    except Exception as exc:
        if isinstance(exc, CompletedPacketImportError):
            raise
        raise CompletedPacketImportError(str(exc)) from exc

    validate_package(draft)
    trial_summary = validate_region_trial_draft(
        blank_package=blank_package,
        draft_package=draft,
        lifecycle_records=lifecycle,
    )
    if draft.get("package_status") != "draft":
        raise CompletedPacketImportError("imported package must remain draft")
    if any(record.get("state") in {"reviewed", "frozen", "superseded"} for record in lifecycle):
        raise CompletedPacketImportError("import cannot create reviewed or frozen states")

    completed_overlay = render_region_overlay(packet)
    lifecycle_sha = canonical_records_sha256(lifecycle)
    manifest = {
        "schema_version": "0.1.0",
        "import_id": f"REGION-IMPORT-{packet['candidate_id']}-R001",
        "trial_id": "REGION-ANNOTATION-TRIAL-0001",
        "packet_id": str(packet["packet_id"]),
        "candidate_id": str(packet["candidate_id"]),
        "photographic_panel_id": str(packet["photographic_panel_id"]),
        "input_packet_sha256": canonical_sha256(packet),
        "blank_package_id": str(blank_package["package_id"]),
        "blank_package_sha256": canonical_sha256(blank_package),
        "draft_package_id": str(draft["package_id"]),
        "draft_package_sha256": canonical_sha256(draft),
        "lifecycle_record_count": len(lifecycle),
        "lifecycle_records_sha256": lifecycle_sha,
        "overlay_sha256": raw_sha256(completed_overlay),
        "region_count": int(trial_summary["region_count"]),
        "package_status": "draft",
        "technical_review_completed": False,
        "scientific_adjudication_used": False,
        "production_freeze_authorized": False,
        "image_binaries_written": False,
        "outputs": {
            "draft_package": "draft-package.json",
            "lifecycle_records": "lifecycle-records.jsonl",
            "inspection_overlay": "inspection-overlay.svg",
        },
    }
    return draft, lifecycle, completed_overlay, manifest


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _jsonl_text(rows: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for row in rows
    )


def write_import_bundle(
    *,
    packet_path: Path,
    blank_package_path: Path,
    output_root: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write a validated import bundle atomically."""

    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    blank = json.loads(blank_package_path.read_text(encoding="utf-8"))
    draft, lifecycle, overlay, manifest = build_import_bundle(
        packet=packet,
        blank_package=blank,
    )

    if output_root.exists() and any(output_root.iterdir()) and not overwrite:
        raise CompletedPacketImportError(
            f"output directory is not empty: {output_root}; use overwrite explicitly"
        )

    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.tmp-", dir=output_root.parent)
    )
    try:
        (temporary / "draft-package.json").write_text(
            _json_text(draft), encoding="utf-8"
        )
        (temporary / "lifecycle-records.jsonl").write_text(
            _jsonl_text(lifecycle), encoding="utf-8"
        )
        (temporary / "inspection-overlay.svg").write_text(
            overlay, encoding="utf-8"
        )
        (temporary / "import-manifest.json").write_text(
            _json_text(manifest), encoding="utf-8"
        )

        written_draft = json.loads(
            (temporary / "draft-package.json").read_text(encoding="utf-8")
        )
        written_lifecycle = [
            json.loads(line)
            for line in (temporary / "lifecycle-records.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        if canonical_sha256(written_draft) != manifest["draft_package_sha256"]:
            raise CompletedPacketImportError("written draft hash verification failed")
        if canonical_records_sha256(written_lifecycle) != manifest[
            "lifecycle_records_sha256"
        ]:
            raise CompletedPacketImportError("written lifecycle hash verification failed")
        if raw_sha256(
            (temporary / "inspection-overlay.svg").read_text(encoding="utf-8")
        ) != manifest["overlay_sha256"]:
            raise CompletedPacketImportError("written overlay hash verification failed")

        if output_root.exists():
            if overwrite:
                shutil.rmtree(output_root)
            elif any(output_root.iterdir()):
                raise CompletedPacketImportError("output directory changed during import")
            else:
                output_root.rmdir()
        os.replace(temporary, output_root)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return manifest
