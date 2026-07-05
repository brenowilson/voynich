import pytest

from voynich.pilot.observations import (
    PilotObservationError,
    build_primary_checkpoint,
    validate_primary_observations,
)


def candidate(index: int) -> dict:
    return {
        "candidate_id": f"PILOT-0001-CAND-{index:03d}",
        "photographic_panel_id": f"YDC-PANEL-{1000 + index}",
        "source_sha256": f"{index % 16:x}" * 64,
    }


def observation(index: int, **overrides) -> dict:
    row = {
        "candidate_id": f"PILOT-0001-CAND-{index:03d}",
        "photographic_panel_id": f"YDC-PANEL-{1000 + index}",
        "source_sha256": f"{index % 16:x}" * 64,
        "pilot_id": "PILOT-0001",
        "observer_id": "OBS-TEST-01",
        "review_pass": "primary",
        "external_transliteration_consulted": False,
        "semantic_section_assignment": None,
        "confidence": 0.9,
    }
    row.update(overrides)
    return row


def test_primary_checkpoint_requires_one_matching_observation_per_candidate() -> None:
    candidates = [candidate(1), candidate(2)]
    observations = [observation(1), observation(2)]

    checkpoint = build_primary_checkpoint(
        candidates=candidates,
        observations=observations,
        candidate_set_sha256="a" * 64,
    )

    assert checkpoint["candidate_count"] == 2
    assert checkpoint["observation_count"] == 2
    assert checkpoint["primary_pass_count"] == 2
    assert checkpoint["observer_ids"] == ["OBS-TEST-01"]
    assert checkpoint["independent_review_required"] is True
    assert checkpoint["final_selection_authorized"] is False


def test_rejects_missing_observation() -> None:
    with pytest.raises(PilotObservationError, match="candidate/observation mismatch"):
        validate_primary_observations(
            candidates=[candidate(1), candidate(2)],
            observations=[observation(1)],
        )


def test_rejects_duplicate_candidate_observation() -> None:
    with pytest.raises(PilotObservationError, match="duplicate candidate_id"):
        validate_primary_observations(
            candidates=[candidate(1)],
            observations=[observation(1), observation(1)],
        )


def test_rejects_source_mismatch() -> None:
    with pytest.raises(PilotObservationError, match="source SHA-256 mismatch"):
        validate_primary_observations(
            candidates=[candidate(1)],
            observations=[observation(1, source_sha256="f" * 64)],
        )


def test_rejects_contaminated_or_semantic_review() -> None:
    with pytest.raises(PilotObservationError, match="contaminated review"):
        validate_primary_observations(
            candidates=[candidate(1)],
            observations=[observation(1, external_transliteration_consulted=True)],
        )

    with pytest.raises(PilotObservationError, match="semantic section assignment"):
        validate_primary_observations(
            candidates=[candidate(1)],
            observations=[observation(1, semantic_section_assignment="conventional-section")],
        )
