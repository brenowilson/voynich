# PILOT-0001 Primary Visual Coding Audit

## Status

The primary blinded visual-coding pass is complete for all 25 frozen candidates.

This is a checkpoint, not the final observation freeze and not the final pilot selection. Independent review and disagreement adjudication remain required.

## Observer and source boundary

- Observer ID: `OBS-AI-PRIMARY-01`
- Review pass: `primary`
- Candidates reviewed: `25 / 25`
- Canonical source representation: retained Yale IIIF JPEG bytes from `SOURCE-FREEZE-0001`
- External transliterations consulted: `false`
- Conventional section assignments used: `false`
- Semantic section assignments recorded: `0`
- Glyph frequencies, tokenization or analytical results used: `0`

The review used the canonical photographic assets associated with the frozen candidate records. Institutional labels were retained only for source traceability. No label was treated as a linguistic, semantic or reading-order claim.

## Observation result

### Text coverage

- low: 3
- medium: 7
- high: 9
- dominant: 6

### Graphic coverage

- none: 1
- low: 3
- medium: 4
- high: 11
- dominant: 6

### Dominant observable graphic geometry

- organic or branched: 11
- circular or radial: 7
- mixed: 3
- human-like figure cluster: 2
- container or network: 1
- none: 1

These names are coarse visual coding categories. They are not identifications of subject matter or manuscript sections.

### Line organization

- clear: 14
- mixed: 8
- ambiguous: 3

### Visual density

- moderate: 8
- dense: 5
- very dense: 12

### Source quality and completeness

- good source quality: 16
- limited source quality: 9
- crop or occlusion present: 9
- crop or occlusion absent: 16

Confidence ranges from `0.88` to `0.96`. No primary observation falls below the protocol's `0.70` adjudication threshold.

## Integrity checks

Every observation:

- matches one frozen candidate ID;
- matches the candidate's photographic panel ID;
- matches the candidate's source-image SHA-256;
- has `review_pass = primary`;
- has `semantic_section_assignment = null`;
- has `external_transliteration_consulted = false`.

Primary observation-set SHA-256:

```text
c58d8efa52ea95ad0a6b99116250d32ef3ff4714642244ee9c4c18aec6f4f18d
```

## Independence limitation

There is currently one observer and no independent second-pass record. The primary coding therefore cannot authorize final selection by itself.

An independent reviewer must code:

- every panel that enters the final pilot;
- at least 25 percent of candidates not selected for the final pilot;
- any additional record chosen for uncertainty or protocol stress testing.

Categorical disagreements require adjudication. The independent reviewer must not receive the primary coding values before submitting their own observations.

## Current authorization state

- Primary coding complete: **yes**
- Independent review complete: **no**
- Adjudication complete: **no**
- Final pilot selection authorized: **no**

Machine-readable records:

- `corpus/pilots/PILOT-0001/visual-observations.jsonl`
- `corpus/pilots/PILOT-0001/primary-observation-checkpoint.json`
- `schemas/pilot-visual-observation.schema.json`
