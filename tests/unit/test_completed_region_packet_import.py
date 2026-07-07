import json
from pathlib import Path

import pytest

from voynich.observation.authoring_packet import build_empty_region_input
from voynich.observation.model import build_blank_package, canonical_sha256
from voynich.observation.packet_import import (
    CompletedPacketImportError,
    build_import_bundle,
    write_import_bundle,
)


def blank_and_entry():
    digest = "a" * 64
    blank = build_blank_package(
        {
            "photographic_panel_id": "YDC-PANEL-6001",
            "institutional_id": "6001",
            "institutional_label": "trial",
            "source_url": "https://example.org/6001.jpg",
            "source_sha256": digest,
            "stored_path": f"sha256/aa/{digest}.jpg",
            "width_px": 1200,
            "height_px": 1800,
            "acquisition_status": "verified",
        }
    )
    entry = {
        "candidate_id": "PILOT-0001-CAND-001",
        "trial_annotation_status": "planned",
        "blank_package_id": blank["package_id"],
        "blank_package_path": "blank.json",
        "blank_package_sha256": canonical_sha256(blank),
        "source_sha256": digest,
    }
    return blank, entry


def completed_packet():
    blank, entry = blank_and_entry()
    packet = build_empty_region_input(trial_entry=entry, blank_package=blank)
    packet["annotator_id"] = "OBS-TRIAL-ANNOTATOR-01"
    packet["annotated_at"] = "2026-07-07T20:00:00Z"
    packet["regions"] = [
        {
            "region_id": "OBSREG-YDC-PANEL-6001-0001",
            "role": "mixed",
            "polygon": [[100, 100], [1000, 100], [1000, 1500], [100, 1500]],
            "confidence": 0.8,
            "visibility": "clear",
            "observation_status": "active",
            "evidence_note": "Broad visible region.",
        }
    ]
    return packet, blank


def test_import_bundle_binds_all_output_hashes() -> None:
    packet, blank = completed_packet()
    draft, lifecycle, overlay, manifest = build_import_bundle(
        packet=packet,
        blank_package=blank,
    )

    assert draft["package_status"] == "draft"
    assert [row["state"] for row in lifecycle] == ["blank", "draft"]
    assert manifest["region_count"] == 1
    assert manifest["draft_package_sha256"] == canonical_sha256(draft)
    assert manifest["technical_review_completed"] is False
    assert manifest["production_freeze_authorized"] is False
    assert "data:image" not in overlay


def test_import_writes_atomically_and_refuses_accidental_overwrite(tmp_path: Path) -> None:
    packet, blank = completed_packet()
    packet_path = tmp_path / "packet.json"
    blank_path = tmp_path / "blank.json"
    output = tmp_path / "imported"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
    blank_path.write_text(json.dumps(blank), encoding="utf-8")

    first = write_import_bundle(
        packet_path=packet_path,
        blank_package_path=blank_path,
        output_root=output,
    )
    assert (output / "draft-package.json").exists()
    assert (output / "lifecycle-records.jsonl").exists()
    assert (output / "inspection-overlay.svg").exists()
    assert (output / "import-manifest.json").exists()

    with pytest.raises(CompletedPacketImportError, match="not empty"):
        write_import_bundle(
            packet_path=packet_path,
            blank_package_path=blank_path,
            output_root=output,
        )

    second = write_import_bundle(
        packet_path=packet_path,
        blank_package_path=blank_path,
        output_root=output,
        overwrite=True,
    )
    assert first == second


def test_import_rejects_modified_source_identity() -> None:
    packet, blank = completed_packet()
    packet["source"]["source_sha256"] = "f" * 64
    with pytest.raises(CompletedPacketImportError):
        build_import_bundle(packet=packet, blank_package=blank)


def test_import_rejects_prohibited_or_out_of_bounds_data() -> None:
    packet, blank = completed_packet()
    packet["reading_order"] = ["OBSREG-YDC-PANEL-6001-0001"]
    with pytest.raises(CompletedPacketImportError):
        build_import_bundle(packet=packet, blank_package=blank)

    packet, blank = completed_packet()
    packet["regions"][0]["polygon"][0] = [1300, 100]
    with pytest.raises(CompletedPacketImportError):
        build_import_bundle(packet=packet, blank_package=blank)
