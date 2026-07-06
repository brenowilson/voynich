# Observation Package Lifecycle

## Purpose

Define the deterministic transition from an immutable blank observation template to a draft and then to a frozen, hash-verifiable observation revision. This protocol governs state and provenance, not annotation content.

## States

### Blank `R000`

A blank package has no annotator, timestamp, observations or events. It is generated from the canonical source manifest or work queue and is never edited in place.

### Draft `R001` or later

A draft is created from blank `R000` or frozen `Rn`.

- blank `R000` produces draft `R001`;
- frozen `Rn` produces draft `R(n+1)`;
- the new package names its parent in `supersedes_package_id`;
- source identity is unchanged;
- an explicit annotator and timezone-aware creation time are required;
- inherited entities are preserved, but revision events reset for the new revision.

### Frozen `R001` or later

A draft can freeze only when it contains at least one entity and every entity has valid revision-event coverage.

Required freeze checks:

- events are chronological and fall between draft creation and freeze time;
- event actors match the package annotator;
- entity kinds match referenced entities;
- active entities end with an event whose resulting hash matches the entity;
- retired entities end with a retire event;
- package schema, geometry and cross-record validation pass.

The freeze record binds package and source hashes, revision ancestry, annotator, timestamps, entity counts and event counts.

## Immutability

Earlier frozen packages are never rewritten. A newer revision records supersession through its parent link and freeze record. The low-level `superseded` status is not used by this canonical lifecycle.

## Prohibited transitions

The lifecycle rejects:

- blank directly to frozen;
- starting a new draft from an existing draft;
- freezing without observations or complete event coverage;
- changes to panel ID, dimensions, URL, stored path or source SHA-256;
- automatic timestamps or annotator IDs;
- mutation of prior frozen revisions.

## Determinism

All timestamps and annotator IDs are supplied explicitly. Identical inputs produce identical draft, frozen package and freeze-record outputs.

## Commands

Start a draft:

```text
PYTHONPATH=src python scripts/start_observation_draft.py \
  --input <blank-or-frozen-package.json> \
  --annotator-id OBS-HUMAN-01 \
  --created-at 2026-07-06T22:30:00Z \
  --output <draft-package.json>
```

Freeze a completed draft:

```text
PYTHONPATH=src python scripts/freeze_observation_package.py \
  --input <draft-package.json> \
  --frozen-at 2026-07-06T23:30:00Z \
  --package-output <frozen-package.json> \
  --freeze-output <freeze-record.json>
```

## Interpretation boundary

Lifecycle tooling does not create or inspect transliterations, glyph identities, words, language, semantic labels, reading order, manuscript sections or analytical classifications.
