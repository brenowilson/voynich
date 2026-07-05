# OBSERVATION-PROTOCOL-0001 — Source-Anchored Observation Primitives

## Purpose

Define the smallest machine-readable observation units needed to describe visible structure in the frozen Yale images without asserting language, meaning, glyph identity, word boundaries or reading order.

This protocol is valid for any panel in the canonical page manifest. It is independent of the final `PILOT-0001` selection and may be implemented while issue #3 remains blocked on an unavailable independent reviewer.

## Governing rule

> Record what is visibly bounded and where it occurs before deciding what it is.

An observation is not a transcription. A candidate region, line or glyph is a geometric hypothesis tied to source pixels and explicit uncertainty.

## Source anchoring

Every observation package must identify:

- one canonical `photographic_panel_id`;
- the Yale institutional child OID;
- the exact source-image SHA-256;
- source URL, stored path, width and height;
- the observation protocol and schema versions.

Coordinates use the immutable full-size Yale JPEG representation named by the source hash.

## Coordinate space

- origin: upper-left source pixel;
- x-axis: increases to the right;
- y-axis: increases downward;
- units: integer source-image pixels;
- no deskew, crop, rotation, rescale or perspective correction is silently applied;
- a displayed or transformed view may be used for annotation only when its reversible transform back to source pixels is recorded.

All canonical geometry is stored in source pixels. Display coordinates are never canonical.

## Entity hierarchy

### Observation package

A package contains all observation entities for one source panel and one revision. Packages are immutable after freeze. A correction creates a new revision that names the package it supersedes.

### Region candidate

A region candidate is a polygon enclosing a visibly coherent area. Permitted observational roles are:

- `text_bearing`;
- `graphic_bearing`;
- `mixed`;
- `unmarked_or_background`;
- `obscured_or_damaged`;
- `uncertain`.

These roles describe visible occupancy only. They do not identify a manuscript section or subject.

### Line candidate

A line candidate is a polygon inside a parent region that appears to organize multiple marks along a locally coherent direction. It may include an optional baseline polyline and an observed orientation angle.

A line candidate does not imply reading order. Line IDs are identifiers, not sequence numbers.

### Glyph candidate

A glyph candidate is a polygon around one locally bounded mark or mark-complex. It has no canonical character identity.

Permitted segmentation states are:

- `isolated_candidate` — locally bounded without a presently recorded split or join concern;
- `possible_join` — may combine marks that should remain separate;
- `possible_split` — may be one mark divided by visibility, contact or annotation choice;
- `overlap` — boundaries visibly intersect another candidate;
- `uncertain_boundary` — boundary placement is materially uncertain;
- `not_fully_visible` — crop, occlusion, damage or imaging prevents complete observation.

A glyph candidate may belong directly to a region when no defensible line parent exists.

### Ambiguity group

An ambiguity group preserves competing or coupled segmentation hypotheses. Permitted relations are:

- `mutually_exclusive`;
- `possible_join`;
- `possible_split`;
- `overlap`;
- `shared_uncertainty`.

Members remain separate observations. The group does not force a winner.

### Revision event

A revision event records the addition, modification, retirement or uncertainty change of an entity. Events preserve:

- stable event and entity IDs;
- actor and timestamp;
- previous and resulting entity hashes when applicable;
- reason and evidence note;
- whether uncertainty increased, decreased or remained unchanged.

Retirement removes an entity only from the current revision. Prior packages and events remain part of the provenance chain.

## Stable neutral identifiers

- package: `OBS-PKG-<panel>-R<revision>`;
- region: `OBSREG-<panel>-<number>`;
- line: `OBSLINE-<panel>-<number>`;
- glyph candidate: `OBSGLYPH-<panel>-<number>`;
- ambiguity group: `OBSAMB-<panel>-<number>`;
- revision event: `OBSEVENT-<panel>-<number>`.

The numeric suffix is an identifier only. It must not encode reading order, linguistic order or importance.

## Geometry rules

- polygons contain at least three source-pixel points;
- polylines contain at least two source-pixel points;
- every coordinate lies within the source image bounds;
- every line polygon lies within its parent region polygon;
- every glyph polygon lies within its parent line polygon, or within its parent region when no line parent is asserted;
- parent IDs must exist in the same package revision;
- a glyph cannot name a line whose parent region differs from the glyph's region;
- zero-area bounding envelopes are invalid.

The validator checks point containment and bounding envelopes. It does not pretend to solve damaged or visually ambiguous topology; such cases must use uncertainty states and notes.

## Confidence and visibility

Every region, line and glyph candidate records:

- `confidence` in the closed interval `[0, 1]`;
- `visibility`: `clear`, `partial`, `obscured`, `damaged`, or `uncertain`;
- an optional neutral evidence note.

Confidence measures confidence in the recorded observation boundary and role, not confidence in a linguistic interpretation.

## Explicitly prohibited fields and inferences

Canonical observation records must not contain:

- transcription or transliteration;
- glyph class, character identity or phonetic value;
- word, token, morpheme or sentence boundaries;
- language or semantic labels;
- Currier class or conventional manuscript section;
- reading order or sequence claims;
- spectral, graph or frequency-derived labels;
- external-transliteration identifiers.

The validator rejects these concepts by key name anywhere in the package.

## Annotation workflow

1. Verify panel ID, dimensions and source SHA-256.
2. Create a blank package revision `R000`.
3. Draw broad region candidates.
4. Add line candidates only where local organization is visually defensible.
5. Add glyph candidates without assigning identities.
6. Create ambiguity groups instead of forcing uncertain splits or joins.
7. Run schema and geometric validation.
8. Record revision events and freeze the package.
9. Correct errors only through a superseding revision.

## Separation from visual pilot coding

The coarse `PILOT-0001` visual-coding table describes whole-panel diversity. It is not imported into this observation model and does not determine region, line or glyph boundaries.

The unavailable independent reviewer blocks the final pilot freeze, but does not block definition, testing or implementation of these source-anchored primitives.

## Canonical outputs

- `schemas/observation-package.schema.json`;
- `schemas/observation-event.schema.json`;
- `src/voynich/observation/model.py`;
- `scripts/build_blank_observation_package.py`;
- `corpus/templates/observation-package.example.json`.
