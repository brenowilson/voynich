# PILOT-0001 Observation Work Queue

## Purpose

Prepare all 25 frozen PILOT-0001 candidates for source-anchored annotation without waiting for final pilot selection or an independent visual reviewer.

The work queue contains blank `OBSERVATION-PROTOCOL-0001` packages only. It does not contain region, line or glyph observations.

## Inputs

- `corpus/pilots/PILOT-0001/candidates.jsonl`;
- `corpus/pilots/PILOT-0001/candidate-freeze.json`;
- `sources/primary/manifests/pages.jsonl`;
- `schemas/observation-package.schema.json`.

The candidate freeze must be valid and unchanged. Candidate panel IDs, dimensions and source hashes must match the canonical page manifest.

## Queue construction

Candidates are sorted by canonical source sequence and candidate ID. They are assigned round-robin to five batches:

```text
position 1  -> batch 01
position 2  -> batch 02
...
position 5  -> batch 05
position 6  -> batch 01
```

This produces five batches of five packages while distributing early, middle and late source positions across the batches.

Batch numbers are work-allocation identifiers only. They do not encode manuscript sections, reading order or analytical classes.

## Package state

Every generated package is:

- revision `R000`;
- `package_status = blank`;
- anchored to one canonical panel and source SHA-256;
- empty of regions, lines, glyph candidates, ambiguity groups and revision events;
- free of external transliterations, semantic interpretation and reading-order claims.

A package becomes `draft` only when an annotator ID, creation timestamp and valid observations are added. It becomes `frozen` only after revision provenance is recorded and validation passes.

The committed blank package must never be overwritten by an annotated package. Annotation work creates a new revision in an observation-data location defined by the annotation sprint.

## Integrity rules

A valid queue requires:

- 25 unique candidates;
- 25 unique photographic panels;
- 25 unique blank packages;
- exact source-hash and dimension agreement with the page manifest;
- exact candidate-set digest agreement with `PILOT-CANDIDATES-FREEZE-0001`;
- five batches containing five packages each;
- deterministic package and manifest hashes;
- zero interpretive outputs, external transliterations or final-selection results.

## Why all 25 candidates are prepared

The unavailable independent reviewer blocks the final 12-panel selection, not technical readiness. Preparing all 25 packages:

- avoids choosing annotation targets from the primary visual coding alone;
- allows annotation tooling and quality-control procedures to be tested;
- preserves the ability to use any later independently selected subset;
- does not require that all 25 panels be fully annotated immediately.

## Outputs

```text
corpus/pilots/PILOT-0001/observation-work-queue/manifest.json
corpus/pilots/PILOT-0001/observation-work-queue/packages/*.json
```

The manifest records candidate, panel, package, source and batch identifiers together with SHA-256 digests.

## Reproduction

```text
PYTHONPATH=src python scripts/build_observation_work_queue.py
```

Regeneration must reproduce the committed manifest and all 25 package files semantically and byte-for-byte under the repository's normalized line-ending rules.
