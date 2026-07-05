# PILOT-0001 Independent Review Procedure

## Purpose

Collect a genuinely independent visual-coding pass for the frozen 25-panel candidate pool before disagreement adjudication and final pilot selection.

The independent reviewer must not see the primary coding values in `visual-observations.jsonl` before submitting their own form.

## Reviewer inputs

The reviewer receives only:

- `corpus/pilots/PILOT-0001/independent-review-template.csv`;
- the canonical Yale image URL listed for each candidate;
- the field definitions in `schemas/pilot-visual-observation.schema.json`;
- this procedure.

The reviewer must not receive:

- the primary visual-observation table;
- summaries of primary coding values;
- external transliterations;
- Currier classes;
- conventional manuscript section assignments;
- semantic interpretations;
- glyph frequencies, tokenization or analytical results;
- a proposed final 12-panel selection.

## Scope

The preferred independent pass covers all 25 candidates. This exceeds the minimum protocol requirement and prevents the final selector from determining which panels receive independent review.

Every row must be completed from direct inspection of the canonical Yale image representation.

## Required fields

The reviewer fills:

- `observer_id` using a stable neutral identifier such as `OBS-HUMAN-02`;
- `reviewed_at` as an ISO 8601 timestamp;
- all visual coding fields;
- `confidence` between 0 and 1;
- optional neutral observational notes.

The following fields are immutable and must not be edited:

- `candidate_id`;
- `photographic_panel_id`;
- `source_url`;
- `source_sha256`;
- `semantic_section_assignment`, which must remain empty and becomes `null` on import;
- `external_transliteration_consulted`, which must remain `false`.

## Permitted values

### Coverage

`text_coverage` and `graphic_coverage`:

```text
none | low | medium | high | dominant | uncertain
```

### Dominant observable graphic geometry

```text
none
organic_branched
circular_radial
container_network
human_figure_cluster
mixed
other_observable
uncertain
```

These are descriptive visual bins, not subject identifications.

### Line organization

```text
none | clear | ambiguous | mixed | uncertain
```

### Visual density

```text
sparse | moderate | dense | very_dense | uncertain
```

### Color presence

```text
none | limited | substantial | uncertain
```

### Source quality

```text
good | limited | problematic | uncertain
```

### Crop or occlusion

```text
none | present | uncertain
```

## Independence declaration

Submission asserts that:

- primary coding values were not inspected before completion;
- no external transliteration was consulted;
- no semantic or conventional section assignment was used;
- each judgment was made from the canonical image and the field definitions alone.

A contaminated pass is rejected and must be repeated by a reviewer who has not seen the primary values.

## Import and adjudication

The completed CSV is imported as `review_pass = independent_second` and validated against the visual-observation schema.

The project then generates a disagreement table. Categorical disagreement does not automatically imply error; it identifies a record requiring adjudication or an uncertainty flag.

Adjudicators receive both completed passes only after the independent form is frozen.

## Completion gate

Final pilot selection remains unauthorized until:

- the independent form passes validation;
- the independent observation set is frozen;
- disagreements are enumerated;
- required adjudications are complete or explicitly retained as unresolved uncertainty.
