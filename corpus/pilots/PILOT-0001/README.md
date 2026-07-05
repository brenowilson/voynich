# PILOT-0001

## Current state

`PILOT-CANDIDATES-FREEZE-0001` is a frozen metadata-only pool of 25 Yale photographic panels.

One primary blinded visual-coding pass is complete for all 25 candidates. The independent second pass has not yet been submitted, disagreement adjudication has not occurred, and the final pilot selection remains unauthorized.

## Frozen candidate composition

- 25 unique photographic panels;
- 14 ordinary, non-foldout, non-composite panels;
- 10 label-derived composite or fragmented panels;
- 1 additional ordinary panel representing a foldout complex;
- all 8 broad source-sequence bins represented;
- all 7 codicological foldout complexes represented;
- all 4 panels assigned to the institutionally explicit 85–86 sextuple leaf retained;
- 0 visual outcomes used to determine candidate eligibility;
- 0 external transliterations used.

Candidate-set SHA-256:

```text
d460d6cc7c200f87e2b3182c1783079a6181bad01d0a83a8bd899b0cc7b8c113
```

## Primary visual coding

- primary observations: `25 / 25`;
- observer ID: `OBS-AI-PRIMARY-01`;
- confidence range: `0.88–0.96`;
- observations below the `0.70` adjudication threshold: `0`;
- external transliterations consulted: `0`;
- semantic section assignments: `0`;
- final selection authorized: `false`.

Primary observation-set SHA-256:

```text
c58d8efa52ea95ad0a6b99116250d32ef3ff4714642244ee9c4c18aec6f4f18d
```

## Independent review package

The independent reviewer receives only:

- `independent-review-template.csv`;
- the canonical Yale image URL and source SHA-256 in each row;
- `docs/protocols/pilot-independent-review.md`;
- `schemas/pilot-visual-observation.schema.json`.

The reviewer must not inspect `visual-observations.jsonl`, summaries of the primary coding, external transliterations, conventional sections, semantic interpretations, glyph statistics or a proposed final selection before completing the second pass.

The preferred independent pass covers all 25 candidates. The importer rejects modified source identities, the primary observer ID, semantic assignments, external-transliteration consultation, incomplete forms and invalid categorical values.

## Files

- `candidates.jsonl` — canonical machine-readable candidate records;
- `candidates.csv` — review-oriented candidate table;
- `candidate-freeze.json` — input hashes, seed and frozen candidate-set digest;
- `visual-observations.jsonl` — primary blinded visual observations;
- `primary-observation-checkpoint.json` — machine-readable primary-pass checkpoint;
- `independent-review-template.csv` — blank deterministic form for the independent reviewer.

## Completion gate

Final selection remains blocked until:

1. the independent form is completed without access to the primary values;
2. the imported independent observations pass schema and provenance validation;
3. the independent observation set is frozen;
4. categorical disagreements are enumerated;
5. required adjudications are completed or retained explicitly as unresolved uncertainty;
6. the deterministic final selector is executed;
7. `PILOT-SELECTION-FREEZE-0001` is declared.

Adding or removing candidates requires revoking the candidate freeze and restarting all visual coding.
