# PILOT-0001

## Current state

`PILOT-CANDIDATES-FREEZE-0001` is a frozen metadata-only pool of 25 Yale photographic panels.

This directory does **not** yet contain the final pilot selection. Every candidate remains at `visual_review_status = pending`.

## Frozen candidate composition

- 25 unique photographic panels;
- 14 ordinary, non-foldout, non-composite panels;
- 10 label-derived composite or fragmented panels;
- 1 additional ordinary panel representing a foldout complex;
- all 8 broad source-sequence bins represented;
- all 7 codicological foldout complexes represented;
- all 4 panels assigned to the institutionally explicit 85–86 sextuple leaf retained;
- 0 visual outcomes used;
- 0 external transliterations used.

Candidate-set SHA-256:

```text
d460d6cc7c200f87e2b3182c1783079a6181bad01d0a83a8bd899b0cc7b8c113
```

## Files

- `candidates.jsonl` — canonical machine-readable candidate records;
- `candidates.csv` — review-oriented tabular view;
- `candidate-freeze.json` — input hashes, seed and frozen candidate-set digest.

## Next stage

Each candidate must receive blinded visual coding under `docs/protocols/pilot-selection.md` and `schemas/pilot-visual-observation.schema.json`.

Reviewers must not receive external transliterations, Currier classes, conventional section labels, semantic assignments, glyph frequencies or analytical results. The visual observation table is frozen before the deterministic final selector chooses the target 12-panel pilot.

Adding or removing candidates after visual coding begins requires revoking this freeze and restarting all visual coding.
