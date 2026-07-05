# PILOT-0001 Review Adjudication Plan

## Status

This branch prepares the next stage after the independent review package merged in commit `2e741d0ac6473c0b36cece4ca1a7f37ca74a5d03`.

No independent observations are present yet. No disagreement calculation, adjudication or final pilot selection is authorized.

## Planned sequence

1. Import a completed independent review form.
2. Validate candidate IDs, panel IDs and source SHA-256 values.
3. Freeze the independent observation set.
4. Compare the primary and independent categorical fields.
5. Record every disagreement without automatic resolution.
6. Adjudicate disagreements or retain them as explicit uncertainty.
7. Run the deterministic final selector only after the adjudication gate passes.

## Required safeguards

- The independent reviewer must differ from `OBS-AI-PRIMARY-01`.
- Primary coding values must remain unavailable to the independent reviewer before submission.
- External transliterations and semantic section assignments remain excluded.
- Final selection remains blocked until the independent and adjudication freezes exist.

## Branch preservation

The working branch is `feature/pilot-review-adjudication-tooling`. It begins at the merged independent-review package and exists separately from the preserved backup branch `backup/pilot-independent-review-package-20260705`.
