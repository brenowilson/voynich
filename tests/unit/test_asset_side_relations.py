from voynich.acquisition.relations import (
    classify_composite_candidate,
    parse_explicit_side_tokens,
)


def parse(label: str):
    return parse_explicit_side_tokens(
        child_oid="1000000",
        sequence_index=1,
        institutional_label=label,
    )


def test_simple_side_is_preserved_without_extra_inference() -> None:
    relations = parse("1r")
    assert [relation.side_id for relation in relations] == ["1r"]
    assert relations[0].coverage == "full_or_unspecified"


def test_part_marker_is_preserved() -> None:
    relations = parse("70v (part)")
    assert [relation.side_id for relation in relations] == ["70v"]
    assert relations[0].coverage == "part"


def test_multiple_explicit_sides_are_extracted_in_label_order() -> None:
    relations = parse("69v and 70r")
    assert [relation.side_id for relation in relations] == ["69v", "70r"]
    assert [relation.relation_index for relation in relations] == [1, 2]


def test_complex_foldout_label_keeps_each_explicit_coverage() -> None:
    relations = parse("85r (part) 86v (part) (part of 85-86 foldout)")
    assert [(relation.side_id, relation.coverage) for relation in relations] == [
        ("85r", "part"),
        ("86v", "part"),
    ]


def test_support_view_has_no_folio_relation() -> None:
    assert parse("[Front cover]") == []


def test_composite_classification_uses_label_evidence_only() -> None:
    relations = parse("85v and 86r (foldout)")
    candidate = classify_composite_candidate(
        child_oid="1000000",
        sequence_index=1,
        institutional_label="85v and 86r (foldout)",
        relations=relations,
    )
    assert candidate is not None
    assert candidate.candidate_type == "explicit_foldout_label"
    assert candidate.side_ids == "85v;86r"
    assert candidate.status == "label_derived_candidate"
