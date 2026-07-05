from copy import deepcopy

import pytest

from voynich.observation.work_queue import (
    ObservationWorkQueueError,
    build_work_queue,
    canonical_records_sha256,
    validate_work_queue,
)


def page(index: int) -> dict:
    oid = str(3000 + index)
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
        "sequence_index": index,
        "acquisition_status": "verified",
    }


def candidate(index: int) -> dict:
    source = page(index)
    return {
        "candidate_id": f"PILOT-0001-CAND-{index:03d}",
        "photographic_panel_id": source["photographic_panel_id"],
        "sequence_index": index,
        "source_sha256": source["source_sha256"],
        "width_px": source["width_px"],
        "height_px": source["height_px"],
    }


def frozen(candidates: list[dict]) -> dict:
    ordered = sorted(candidates, key=lambda row: row["sequence_index"])
    return {
        "freeze_id": "PILOT-CANDIDATES-FREEZE-0001",
        "status": "frozen",
        "candidate_set_sha256": canonical_records_sha256(ordered),
    }


def test_queue_is_stable_under_input_reordering() -> None:
    candidates = [candidate(index) for index in range(1, 11)]
    pages = [page(index) for index in range(1, 11)]
    freeze = frozen(candidates)

    manifest, packages = build_work_queue(
        candidates=candidates,
        pages=pages,
        candidate_freeze=freeze,
        batch_count=5,
    )
    reversed_manifest, reversed_packages = build_work_queue(
        candidates=list(reversed(candidates)),
        pages=list(reversed(pages)),
        candidate_freeze=freeze,
        batch_count=5,
    )

    assert manifest == reversed_manifest
    assert packages == reversed_packages
    assert manifest["package_count"] == 10
    assert len({entry["batch_id"] for entry in manifest["entries"]}) == 5
    assert [entry["batch_id"] for entry in manifest["entries"][:5]] == [
        "OBS-BATCH-PILOT-0001-01",
        "OBS-BATCH-PILOT-0001-02",
        "OBS-BATCH-PILOT-0001-03",
        "OBS-BATCH-PILOT-0001-04",
        "OBS-BATCH-PILOT-0001-05",
    ]
    assert all(package["package_status"] == "blank" for package in packages.values())


def test_queue_rejects_candidate_source_mismatch() -> None:
    candidates = [candidate(1)]
    pages = [page(1)]
    freeze = frozen(candidates)
    candidates[0]["source_sha256"] = "f" * 64
    freeze = frozen(candidates)

    with pytest.raises(ObservationWorkQueueError, match="differs from page manifest"):
        build_work_queue(
            candidates=candidates,
            pages=pages,
            candidate_freeze=freeze,
            batch_count=1,
        )


def test_queue_rejects_unfrozen_or_changed_candidate_set() -> None:
    candidates = [candidate(1), candidate(2)]
    pages = [page(1), page(2)]
    freeze = frozen(candidates)

    changed = deepcopy(candidates)
    changed[0]["sequence_index"] = 99
    with pytest.raises(ObservationWorkQueueError, match="do not match candidate freeze"):
        build_work_queue(
            candidates=changed,
            pages=pages,
            candidate_freeze=freeze,
            batch_count=1,
        )

    freeze["status"] = "draft"
    with pytest.raises(ObservationWorkQueueError, match="not frozen"):
        build_work_queue(
            candidates=candidates,
            pages=pages,
            candidate_freeze=freeze,
            batch_count=1,
        )


def test_validation_rejects_missing_package_and_interpretive_flag() -> None:
    candidates = [candidate(1), candidate(2)]
    pages = [page(1), page(2)]
    freeze = frozen(candidates)
    manifest, packages = build_work_queue(
        candidates=candidates,
        pages=pages,
        candidate_freeze=freeze,
        batch_count=1,
    )

    missing = dict(packages)
    missing.pop(next(iter(missing)))
    with pytest.raises(ObservationWorkQueueError, match="missing package"):
        validate_work_queue(
            manifest=manifest,
            packages=missing,
            candidates=candidates,
            pages=pages,
            candidate_freeze=freeze,
        )

    contaminated = deepcopy(manifest)
    contaminated["interpretive_outputs_used"] = True
    with pytest.raises(ObservationWorkQueueError, match="interpretive_outputs_used"):
        validate_work_queue(
            manifest=contaminated,
            packages=packages,
            candidates=candidates,
            pages=pages,
            candidate_freeze=freeze,
        )
