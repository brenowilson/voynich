from copy import deepcopy

import pytest

from voynich.observation.model import build_blank_package
from voynich.observation.region_trial import (
    RegionAnnotationTrialError,
    build_blank_draft_lifecycle_records,
    build_trial_manifest,
    start_region_draft,
    validate_region_trial_draft,
    validate_trial_manifest,
)


def candidate(index: int, *, eligible: bool = True) -> dict:
    return {
        "candidate_id": f"PILOT-0001-CAND-{index:03d}",
        "composition_status": (
            "single_side_or_unspecified" if eligible else "composite_candidate"
        ),
        "source_sha256": f"{index % 16:x}" * 64,
    }


def queue_entry(index: int, batch: int) -> dict:
    source_hash = f"{index % 16:x}" * 64
    return {
        "candidate_id": f"PILOT-0001-CAND-{index:03d}",
        "photographic_panel_id": f"YDC-PANEL-{4000 + index}",
        "sequence_index": index * 10,
        "source_sha256": source_hash,
        "package_id": f"OBS-PKG-YDC-PANEL-{4000 + index}-R000",
        "package_path": (
            "corpus/pilots/PILOT-0001/observation-work-queue/packages/"
            f"PILOT-0001-CAND-{index:03d}.json"
        ),
        "package_sha256": f"{(index + 1) % 16:x}" * 64,
        "batch_id": f"OBS-BATCH-PILOT-0001-{batch:02d}",
        "annotation_status": "blank",
    }


def work_queue() -> tuple[dict, list[dict]]:
    candidates = []
    entries = []
    for batch in range(1, 6):
        early = batch
        later = batch + 5
        candidates.append(candidate(early, eligible=True))
        candidates.append(candidate(later, eligible=True))
        entries.append(queue_entry(later, batch))
        entries.append(queue_entry(early, batch))
    return (
        {
            "queue_id": "OBS-WORK-QUEUE-PILOT-0001-0001",
            "status": "ready",
            "candidate_set_sha256": "a" * 64,
            "package_set_sha256": "b" * 64,
            "batch_count": 5,
            "interpretive_outputs_used": False,
            "external_transliterations_used": False,
            "final_pilot_selection_used": False,
            "entries": entries,
        },
        candidates,
    )


def panel() -> dict:
    digest = "ab22d0c20cc0c4e754236a32960c650c7275ac9a51e0dd33c91060694cb6ac05"
    return {
        "photographic_panel_id": "YDC-PANEL-1006094",
        "institutional_id": "1006094",
        "institutional_label": "10r",
        "source_url": "https://example.org/1006094.jpg",
        "source_sha256": digest,
        "stored_path": f"sha256/{digest[:2]}/{digest}.jpg",
        "width_px": 2691,
        "height_px": 3739,
        "acquisition_status": "verified",
    }


def region() -> dict:
    return {
        "region_id": "OBSREG-YDC-PANEL-1006094-0001",
        "role": "mixed",
        "polygon": [[100, 100], [900, 100], [900, 700], [100, 700]],
        "confidence": 0.72,
        "visibility": "clear",
        "observation_status": "active",
        "evidence_note": "Broad visibly bounded mark-bearing area.",
    }


def test_selection_is_metadata_only_and_stable_under_reordering() -> None:
    queue, candidates = work_queue()
    manifest = build_trial_manifest(work_queue=queue, candidates=candidates)

    reversed_queue = deepcopy(queue)
    reversed_queue["entries"] = list(reversed(reversed_queue["entries"]))
    reversed_manifest = build_trial_manifest(
        work_queue=reversed_queue,
        candidates=list(reversed(candidates)),
    )

    assert manifest == reversed_manifest
    assert manifest["selected_count"] == 5
    assert manifest["batch_count"] == 5
    assert [row["candidate_id"] for row in manifest["entries"]] == [
        "PILOT-0001-CAND-001",
        "PILOT-0001-CAND-002",
        "PILOT-0001-CAND-003",
        "PILOT-0001-CAND-004",
        "PILOT-0001-CAND-005",
    ]
    assert manifest["visual_outcomes_used"] is False
    assert manifest["production_freeze_authorized"] is False
    validate_trial_manifest(
        manifest=manifest,
        work_queue=queue,
        candidates=candidates,
    )


def test_selection_rejects_contaminated_queue_and_source_mismatch() -> None:
    queue, candidates = work_queue()
    queue["interpretive_outputs_used"] = True
    with pytest.raises(RegionAnnotationTrialError, match="interpretive_outputs_used"):
        build_trial_manifest(work_queue=queue, candidates=candidates)

    queue, candidates = work_queue()
    candidates[0]["source_sha256"] = "f" * 64
    with pytest.raises(RegionAnnotationTrialError, match="source SHA-256 mismatch"):
        build_trial_manifest(work_queue=queue, candidates=candidates)


def test_region_draft_preserves_source_and_lifecycle() -> None:
    blank = build_blank_package(panel())
    draft = start_region_draft(
        blank_package=blank,
        regions=[region()],
        annotator_id="OBS-TRIAL-ANNOTATOR-01",
        created_at="2026-07-07T18:00:00Z",
    )
    records = build_blank_draft_lifecycle_records(
        blank_package=blank,
        draft_package=draft,
        actor_id="OBS-LIFECYCLE-01",
        blank_recorded_at="2026-07-07T17:59:00Z",
        draft_recorded_at="2026-07-07T18:01:00Z",
    )
    summary = validate_region_trial_draft(
        blank_package=blank,
        draft_package=draft,
        lifecycle_records=records,
    )

    assert draft["package_id"] == "OBS-PKG-YDC-PANEL-1006094-R001"
    assert draft["revision"]["supersedes_package_id"] == blank["package_id"]
    assert draft["source"] == blank["source"]
    assert len(draft["revision_events"]) == 1
    assert summary["transition"] == "blank->draft"
    assert summary["region_count"] == 1
    assert summary["production_freeze_authorized"] is False


def test_region_trial_rejects_empty_or_interpretive_region_input() -> None:
    blank = build_blank_package(panel())
    with pytest.raises(RegionAnnotationTrialError, match="at least one region"):
        start_region_draft(
            blank_package=blank,
            regions=[],
            annotator_id="OBS-TRIAL-ANNOTATOR-01",
            created_at="2026-07-07T18:00:00Z",
        )

    bad = region()
    bad["role"] = "botanical_identification"
    with pytest.raises(RegionAnnotationTrialError, match="prohibited role"):
        start_region_draft(
            blank_package=blank,
            regions=[bad],
            annotator_id="OBS-TRIAL-ANNOTATOR-01",
            created_at="2026-07-07T18:00:00Z",
        )


def test_region_trial_remains_region_only_and_unfrozen() -> None:
    blank = build_blank_package(panel())
    draft = start_region_draft(
        blank_package=blank,
        regions=[region()],
        annotator_id="OBS-TRIAL-ANNOTATOR-01",
        created_at="2026-07-07T18:00:00Z",
    )
    records = build_blank_draft_lifecycle_records(
        blank_package=blank,
        draft_package=draft,
        actor_id="OBS-LIFECYCLE-01",
        blank_recorded_at="2026-07-07T17:59:00Z",
        draft_recorded_at="2026-07-07T18:01:00Z",
    )

    draft["lines"] = [{"line_id": "OBSLINE-YDC-PANEL-1006094-0001"}]
    with pytest.raises(RegionAnnotationTrialError, match="cannot contain lines or glyphs"):
        validate_region_trial_draft(
            blank_package=blank,
            draft_package=draft,
            lifecycle_records=records,
        )
