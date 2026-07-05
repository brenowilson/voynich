import pytest

from voynich.pilot.independent_review import (
    IndependentReviewError,
    build_template_rows,
    import_completed_rows,
    validate_template_rows,
)


def candidate(index: int) -> dict:
    return {
        "candidate_id": f"PILOT-0001-CAND-{index:03d}",
        "photographic_panel_id": f"YDC-PANEL-{1000 + index}",
        "source_url": f"https://example.org/{1000 + index}.jpg",
        "source_sha256": f"{index % 16:x}" * 64,
    }


def completed(row: dict[str, str], **overrides) -> dict[str, str]:
    value = {
        **row,
        "observer_id": "OBS-HUMAN-02",
        "reviewed_at": "2026-07-05T04:00:00Z",
        "text_coverage": "medium",
        "graphic_coverage": "high",
        "dominant_graphic_geometry": "mixed",
        "line_organization": "clear",
        "visual_density": "dense",
        "color_presence": "limited",
        "source_quality": "good",
        "crop_or_occlusion": "none",
        "confidence": "0.9",
        "semantic_section_assignment": "",
        "external_transliteration_consulted": "false",
        "notes": "neutral visual note",
    }
    value.update(overrides)
    return value


def test_template_is_blinded_and_deterministic() -> None:
    candidates = [candidate(2), candidate(1)]
    rows = build_template_rows(candidates)

    assert [row["candidate_id"] for row in rows] == [
        "PILOT-0001-CAND-001",
        "PILOT-0001-CAND-002",
    ]
    assert all(row["observer_id"] == "" for row in rows)
    assert all(row["text_coverage"] == "" for row in rows)
    assert all(row["external_transliteration_consulted"] == "false" for row in rows)
    validate_template_rows(candidates=candidates, rows=rows)


def test_completed_form_imports_as_independent_second_pass() -> None:
    candidates = [candidate(1), candidate(2)]
    rows = [completed(row) for row in build_template_rows(candidates)]

    observations = import_completed_rows(candidates=candidates, rows=rows)

    assert len(observations) == 2
    assert all(row["review_pass"] == "independent_second" for row in observations)
    assert all(row["observer_id"] == "OBS-HUMAN-02" for row in observations)
    assert all(row["semantic_section_assignment"] is None for row in observations)
    assert not any(row["external_transliteration_consulted"] for row in observations)


def test_rejects_primary_observer_and_contamination() -> None:
    candidates = [candidate(1)]
    template = build_template_rows(candidates)[0]

    with pytest.raises(IndependentReviewError, match="must differ"):
        import_completed_rows(
            candidates=candidates,
            rows=[completed(template, observer_id="OBS-AI-PRIMARY-01")],
        )

    with pytest.raises(IndependentReviewError, match="contaminated"):
        import_completed_rows(
            candidates=candidates,
            rows=[completed(template, external_transliteration_consulted="true")],
        )


def test_rejects_changed_source_identity_or_invalid_category() -> None:
    candidates = [candidate(1)]
    template = build_template_rows(candidates)[0]

    with pytest.raises(IndependentReviewError, match="immutable field"):
        import_completed_rows(
            candidates=candidates,
            rows=[completed(template, source_sha256="f" * 64)],
        )

    with pytest.raises(IndependentReviewError, match="invalid text_coverage"):
        import_completed_rows(
            candidates=candidates,
            rows=[completed(template, text_coverage="semantic-label")],
        )
