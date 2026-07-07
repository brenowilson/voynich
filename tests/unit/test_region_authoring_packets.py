from copy import deepcopy

import pytest

from voynich.observation.authoring_packet import (
    RegionAuthoringPacketError,
    build_empty_region_input,
    build_packet_manifest,
    render_region_overlay,
    validate_completed_region_input,
)
from voynich.observation.model import ObservationValidationError, build_blank_package, canonical_sha256


def panel(index: int = 1) -> dict:
    oid = str(5000 + index)
    digest = f"{index % 16:x}" * 64
    return {
        "photographic_panel_id": f"YDC-PANEL-{oid}",
        "institutional_id": oid,
        "institutional_label": f"{index}r",
        "source_url": f"https://example.org/{oid}.jpg",
        "source_sha256": digest,
        "stored_path": f"sha256/{digest[:2]}/{digest}.jpg",
        "width_px": 2000 + index,
        "height_px": 3000 + index,
        "acquisition_status": "verified",
    }


def trial_entry(index: int = 1, batch: int = 1) -> tuple[dict, dict]:
    blank = build_blank_package(panel(index))
    candidate_id = f"PILOT-0001-CAND-{index:03d}"
    return (
        {
            "batch_id": f"OBS-BATCH-PILOT-0001-{batch:02d}",
            "candidate_id": candidate_id,
            "photographic_panel_id": blank["source"]["photographic_panel_id"],
            "sequence_index": index,
            "composition_status": "single_side_or_unspecified",
            "source_sha256": blank["source"]["source_sha256"],
            "blank_package_id": blank["package_id"],
            "blank_package_path": f"packages/{candidate_id}.json",
            "blank_package_sha256": canonical_sha256(blank),
            "selection_reason": "metadata-only test selection",
            "trial_annotation_status": "planned",
        },
        blank,
    )


def region(panel_id: str, width: int, height: int) -> dict:
    return {
        "region_id": f"OBSREG-{panel_id}-0001",
        "role": "mixed",
        "polygon": [[10, 10], [width - 10, 10], [width - 10, height - 10], [10, height - 10]],
        "confidence": 0.75,
        "visibility": "clear",
        "observation_status": "active",
        "evidence_note": "Broad visible mark-bearing region.",
    }


def test_empty_packet_is_source_anchored_and_outcome_free() -> None:
    entry, blank = trial_entry()
    packet = build_empty_region_input(trial_entry=entry, blank_package=blank)

    assert packet["source"]["width_px"] == blank["source"]["width_px"]
    assert packet["source"]["height_px"] == blank["source"]["height_px"]
    assert packet["source"]["source_sha256"] == blank["source"]["source_sha256"]
    assert packet["regions"] == []
    assert packet["annotator_id"] is None
    assert packet["production_freeze_authorized"] is False


def test_svg_uses_canonical_viewbox_and_external_image_reference() -> None:
    entry, blank = trial_entry()
    packet = build_empty_region_input(trial_entry=entry, blank_package=blank)
    svg = render_region_overlay(packet)

    width = blank["source"]["width_px"]
    height = blank["source"]["height_px"]
    assert f'viewBox="0 0 {width} {height}"' in svg
    assert blank["source"]["source_url"] in svg
    assert "data:image" not in svg
    assert '<g id="region-overlays">' in svg


def test_completed_packet_converts_to_valid_draft_and_lifecycle() -> None:
    entry, blank = trial_entry()
    packet = build_empty_region_input(trial_entry=entry, blank_package=blank)
    packet["annotator_id"] = "OBS-TRIAL-ANNOTATOR-01"
    packet["annotated_at"] = "2026-07-07T19:00:00Z"
    packet["regions"] = [
        region(
            blank["source"]["photographic_panel_id"],
            blank["source"]["width_px"],
            blank["source"]["height_px"],
        )
    ]

    draft, lifecycle = validate_completed_region_input(
        packet=packet,
        blank_package=blank,
    )

    assert draft["package_status"] == "draft"
    assert draft["package_id"].endswith("-R001")
    assert draft["source"] == blank["source"]
    assert len(draft["revision_events"]) == 1
    assert [record["state"] for record in lifecycle] == ["blank", "draft"]


def test_completed_packet_rejects_interpretive_and_out_of_bounds_input() -> None:
    entry, blank = trial_entry()
    packet = build_empty_region_input(trial_entry=entry, blank_package=blank)
    packet["annotator_id"] = "OBS-TRIAL-ANNOTATOR-01"
    packet["annotated_at"] = "2026-07-07T19:00:00Z"
    packet["semantic_label"] = "plant"
    with pytest.raises(RegionAuthoringPacketError, match="forbidden interpretive field"):
        validate_completed_region_input(packet=packet, blank_package=blank)

    packet = build_empty_region_input(trial_entry=entry, blank_package=blank)
    packet["annotator_id"] = "OBS-TRIAL-ANNOTATOR-01"
    packet["annotated_at"] = "2026-07-07T19:00:00Z"
    bad_region = region(
        blank["source"]["photographic_panel_id"],
        blank["source"]["width_px"],
        blank["source"]["height_px"],
    )
    bad_region["polygon"][0] = [blank["source"]["width_px"] + 1, 10]
    packet["regions"] = [bad_region]
    with pytest.raises((RegionAuthoringPacketError, ObservationValidationError)):
        validate_completed_region_input(packet=packet, blank_package=blank)


def test_packet_bundle_is_deterministic_and_contains_no_image_bytes() -> None:
    entries = []
    packages = {}
    for index in range(1, 6):
        entry, blank = trial_entry(index=index, batch=index)
        entries.append(entry)
        packages[entry["blank_package_path"]] = blank
    trial = {
        "trial_id": "REGION-ANNOTATION-TRIAL-0001",
        "status": "prepared",
        "entries": entries,
    }

    manifest, files = build_packet_manifest(
        trial_manifest=trial,
        blank_packages=packages,
    )
    reversed_manifest, reversed_files = build_packet_manifest(
        trial_manifest={**trial, "entries": list(reversed(entries))},
        blank_packages=packages,
    )

    assert manifest["packet_count"] == 5
    assert manifest["image_binaries_included"] is False
    assert len(files) == 10
    assert all("data:image" not in content for path, content in files.items() if path.endswith(".svg"))
    assert manifest != reversed_manifest
    assert set(files) == set(reversed_files)
