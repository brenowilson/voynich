"""Build deterministic source-pixel authoring packets for region annotations."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .model import canonical_sha256, validate_package
from .region_trial import (
    RegionAnnotationTrialError,
    build_blank_draft_lifecycle_records,
    start_region_draft,
    validate_region_trial_draft,
)
from .work_queue import canonical_records_sha256


class RegionAuthoringPacketError(RuntimeError):
    """Raised when a region authoring packet is invalid or contaminated."""


FORBIDDEN_INPUT_KEYS = {
    "transcription",
    "transliteration",
    "glyph_class",
    "character_identity",
    "word",
    "token",
    "reading_order",
    "semantic_label",
    "semantic_section",
    "currier_class",
    "language",
}


def _walk_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in FORBIDDEN_INPUT_KEYS:
                raise RegionAuthoringPacketError(
                    f"forbidden interpretive field at {path}.{key}"
                )
            _walk_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}[{index}]")


def build_empty_region_input(
    *, trial_entry: dict[str, Any], blank_package: dict[str, Any]
) -> dict[str, Any]:
    """Create an empty authoring template anchored to one committed blank package."""

    summary = validate_package(blank_package)
    if summary["package_status"] != "blank":
        raise RegionAuthoringPacketError("authoring packet requires a blank package")
    if trial_entry.get("trial_annotation_status") != "planned":
        raise RegionAuthoringPacketError("trial entry is not in planned state")
    if trial_entry.get("blank_package_id") != blank_package.get("package_id"):
        raise RegionAuthoringPacketError("trial entry package ID mismatch")
    package_digest = canonical_sha256(blank_package)
    if trial_entry.get("blank_package_sha256") != package_digest:
        raise RegionAuthoringPacketError("trial entry package SHA-256 mismatch")
    source = blank_package["source"]
    if trial_entry.get("source_sha256") != source.get("source_sha256"):
        raise RegionAuthoringPacketError("trial entry source SHA-256 mismatch")

    candidate_id = str(trial_entry["candidate_id"])
    panel_id = str(source["photographic_panel_id"])
    return {
        "schema_version": "0.1.0",
        "packet_id": f"REGION-PACKET-{candidate_id}",
        "trial_id": "REGION-ANNOTATION-TRIAL-0001",
        "candidate_id": candidate_id,
        "photographic_panel_id": panel_id,
        "blank_package": {
            "package_id": str(blank_package["package_id"]),
            "package_path": str(trial_entry["blank_package_path"]),
            "package_sha256": package_digest,
        },
        "source": {
            "source_url": str(source["source_url"]),
            "source_sha256": str(source["source_sha256"]),
            "width_px": int(source["width_px"]),
            "height_px": int(source["height_px"]),
            "coordinate_origin": "top_left",
            "coordinate_units": "source_pixels",
        },
        "annotator_id": None,
        "annotated_at": None,
        "regions": [],
        "external_transliterations_used": False,
        "semantic_interpretation_used": False,
        "reading_order_asserted": False,
        "technical_review_completed": False,
        "scientific_adjudication_used": False,
        "production_freeze_authorized": False,
    }


def render_region_overlay(packet: dict[str, Any]) -> str:
    """Render an SVG overlay using canonical source dimensions and external image URL."""

    _walk_forbidden(packet)
    source = packet["source"]
    width = int(source["width_px"])
    height = int(source["height_px"])
    if width <= 0 or height <= 0:
        raise RegionAuthoringPacketError("overlay dimensions must be positive")
    href = html.escape(str(source["source_url"]), quote=True)
    packet_id = html.escape(str(packet["packet_id"]), quote=True)
    region_elements: list[str] = []
    for region in packet.get("regions", []):
        region_id = html.escape(str(region["region_id"]), quote=True)
        points = " ".join(f"{int(x)},{int(y)}" for x, y in region["polygon"])
        region_elements.append(
            f'    <polygon id="{region_id}" points="{points}" '
            'fill="none" stroke="currentColor" stroke-width="3" />'
        )
    region_markup = "\n".join(region_elements)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'id="{packet_id}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <image href="{href}" xlink:href="{href}" x="0" y="0" '
        f'width="{width}" height="{height}" preserveAspectRatio="none" />\n'
        '  <g id="region-overlays">\n'
        f'{region_markup}\n'
        '  </g>\n'
        '</svg>\n'
    )


def validate_completed_region_input(
    *, packet: dict[str, Any], blank_package: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate a completed packet and convert it into an R001 draft plus lifecycle records."""

    _walk_forbidden(packet)
    expected = build_empty_region_input(
        trial_entry={
            "candidate_id": packet["candidate_id"],
            "trial_annotation_status": "planned",
            "blank_package_id": packet["blank_package"]["package_id"],
            "blank_package_path": packet["blank_package"]["package_path"],
            "blank_package_sha256": packet["blank_package"]["package_sha256"],
            "source_sha256": packet["source"]["source_sha256"],
        },
        blank_package=blank_package,
    )
    immutable_fields = (
        "schema_version",
        "packet_id",
        "trial_id",
        "candidate_id",
        "photographic_panel_id",
        "blank_package",
        "source",
        "external_transliterations_used",
        "semantic_interpretation_used",
        "reading_order_asserted",
        "technical_review_completed",
        "scientific_adjudication_used",
        "production_freeze_authorized",
    )
    for field in immutable_fields:
        if packet.get(field) != expected.get(field):
            raise RegionAuthoringPacketError(f"packet immutable field changed: {field}")

    annotator_id = str(packet.get("annotator_id") or "")
    annotated_at = str(packet.get("annotated_at") or "")
    if not annotator_id.startswith("OBS-"):
        raise RegionAuthoringPacketError("completed packet requires neutral annotator_id")
    if "T" not in annotated_at:
        raise RegionAuthoringPacketError("completed packet requires ISO annotated_at")
    regions = packet.get("regions")
    if not isinstance(regions, list):
        raise RegionAuthoringPacketError("regions must be an array")

    try:
        draft = start_region_draft(
            blank_package=blank_package,
            regions=regions,
            annotator_id=annotator_id,
            created_at=annotated_at,
        )
        lifecycle = build_blank_draft_lifecycle_records(
            blank_package=blank_package,
            draft_package=draft,
            actor_id="OBS-LIFECYCLE-01",
            blank_recorded_at=annotated_at,
            draft_recorded_at=annotated_at,
        )
        validate_region_trial_draft(
            blank_package=blank_package,
            draft_package=draft,
            lifecycle_records=lifecycle,
        )
    except RegionAnnotationTrialError as exc:
        raise RegionAuthoringPacketError(str(exc)) from exc
    return draft, lifecycle


def build_packet_manifest(
    *, trial_manifest: dict[str, Any], blank_packages: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build packet JSON/SVG files and a deterministic packet-set manifest."""

    if trial_manifest.get("status") != "prepared":
        raise RegionAuthoringPacketError("region trial is not prepared")
    entries: list[dict[str, Any]] = []
    files: dict[str, str] = {}
    for trial_entry in trial_manifest["entries"]:
        package_path = str(trial_entry["blank_package_path"])
        blank = blank_packages.get(package_path)
        if blank is None:
            raise RegionAuthoringPacketError(f"missing blank package {package_path}")
        packet = build_empty_region_input(
            trial_entry=trial_entry,
            blank_package=blank,
        )
        candidate_id = str(trial_entry["candidate_id"])
        json_path = f"packets/{candidate_id}.json"
        svg_path = f"overlays/{candidate_id}.svg"
        json_text = json.dumps(
            packet, ensure_ascii=False, sort_keys=True, indent=2
        ) + "\n"
        svg_text = render_region_overlay(packet)
        files[json_path] = json_text
        files[svg_path] = svg_text
        entries.append(
            {
                "candidate_id": candidate_id,
                "photographic_panel_id": str(trial_entry["photographic_panel_id"]),
                "packet_path": json_path,
                "packet_sha256": canonical_sha256(packet),
                "overlay_path": svg_path,
                "overlay_sha256": canonical_sha256(svg_text),
                "source_sha256": str(trial_entry["source_sha256"]),
                "width_px": int(blank["source"]["width_px"]),
                "height_px": int(blank["source"]["height_px"]),
                "annotation_status": "empty_template",
            }
        )

    manifest = {
        "schema_version": "0.1.0",
        "packet_set_id": "REGION-AUTHORING-PACKETS-0001",
        "trial_id": str(trial_manifest["trial_id"]),
        "status": "ready_for_authoring",
        "packet_count": len(entries),
        "image_binaries_included": False,
        "external_transliterations_used": False,
        "scientific_adjudication_used": False,
        "production_freeze_authorized": False,
        "packet_set_sha256": canonical_records_sha256(entries),
        "entries": entries,
    }
    return manifest, files


def write_packet_bundle(
    *,
    trial_manifest_path: Path,
    output_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    trial_manifest = json.loads(trial_manifest_path.read_text(encoding="utf-8"))
    blank_packages: dict[str, dict[str, Any]] = {}
    for entry in trial_manifest["entries"]:
        relative = str(entry["blank_package_path"])
        blank_packages[relative] = json.loads(
            (repository_root / relative).read_text(encoding="utf-8")
        )
    manifest, files = build_packet_manifest(
        trial_manifest=trial_manifest,
        blank_packages=blank_packages,
    )
    for relative, content in files.items():
        path = output_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
