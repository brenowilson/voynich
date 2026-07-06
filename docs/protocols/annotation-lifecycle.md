# ANNOTATION-LIFECYCLE-0001 — Package States and Freeze Gates

## Purpose

Define how a source-anchored observation package moves from an untouched template to an immutable observational record without importing interpretation, final pilot selection or external transliterations.

This lifecycle governs technical package integrity. It does not substitute for later independent scientific adjudication.

## States

### `blank`

A deterministic revision-zero package generated from the canonical page manifest.

Requirements:

- revision number `0`;
- no annotator;
- no creation timestamp;
- no observations or revision events;
- no predecessor.

### `draft`

An actively edited observational revision.

Requirements:

- named annotator;
- creation timestamp;
- schema and geometry validation pass;
- every change from a predecessor is represented by revision events;
- uncertainty remains explicit.

A draft may be replaced by a later draft revision. It must never overwrite a frozen package.

### `reviewed`

A draft that has passed technical review for source identity, geometry, provenance and protocol compliance.

Technical review asks whether the package is valid and traceable. It does not decide whether the observations are scientifically correct, exhaustive or semantically meaningful.

Requirements:

- all draft requirements;
- reviewer ID distinct from the annotator ID;
- review timestamp;
- review checklist completed;
- no unresolved validation errors;
- all acknowledged unresolved ambiguities remain represented.

### `frozen`

An immutable reviewed package accepted as an observational corpus revision.

Requirements:

- all reviewed requirements;
- package SHA-256 recorded in a freeze record;
- predecessor chain complete;
- every active entity covered by provenance;
- no silent disappearance of entities or uncertainty;
- source panel ID, dimensions and source SHA-256 match the canonical manifest;
- package copied to a freeze location rather than edited in place.

### `superseded`

A formerly frozen package replaced by a later frozen revision.

The original bytes, hash and provenance remain retained. Supersession does not delete or rewrite the earlier package.

## Allowed transitions

```text
blank -> draft
draft -> draft
draft -> reviewed
reviewed -> draft
reviewed -> frozen
frozen -> superseded
```

The following transitions are forbidden:

```text
blank -> reviewed
blank -> frozen
draft -> frozen
frozen -> draft
frozen -> reviewed
superseded -> any editable state
```

A correction to a frozen package starts a new draft revision that names the frozen package as its predecessor. The frozen package itself is not modified.

## Revision rules

- revision numbers increase by exactly one along a package chain;
- `R000` is reserved for the blank package;
- each nonzero revision names exactly one predecessor package;
- the predecessor must refer to the same photographic panel and source SHA-256;
- a revision cannot supersede itself;
- package IDs encode panel and revision only, not reading order or interpretation.

## Uncertainty preservation

Uncertainty may increase, decrease or remain unchanged, but it cannot disappear silently.

A decrease in uncertainty requires:

- an explicit `uncertainty_update` revision event;
- previous and resulting entity hashes;
- a reason tied to visible evidence or corrected geometry;
- preservation of the predecessor revision.

Deletion by omission is prohibited. Retirement requires a retirement event and a later revision.

## Technical review checklist

A reviewer confirms:

1. source panel ID and SHA-256 match the canonical manifest;
2. coordinates use immutable source-image pixels;
3. parent-child geometry validates;
4. entity IDs are unique and panel-local;
5. revision events match resulting entity hashes;
6. ambiguous splits, joins and overlaps remain explicit;
7. prohibited interpretive fields are absent;
8. no reading order, transliteration or glyph identity was introduced;
9. predecessor and revision numbers are consistent;
10. the package can be regenerated or independently revalidated.

## Separation of review roles

- **Self-check:** performed by the annotator before requesting technical review.
- **Technical review:** checks package validity, geometry and provenance. It may be performed before an independent scientific reviewer is available.
- **Scientific adjudication:** later assessment of observational choices, protocol adequacy and sampling decisions by an independent reviewer.

Only the third role is blocked by the current absence of an independent reviewer. The first two may proceed now.

## Freeze gate

A package may enter `frozen` only when all of the following are true:

- lifecycle transition is allowed;
- package and event schemas pass;
- geometric validation passes;
- technical-review record passes;
- predecessor chain validates;
- freeze record contains package hash, source hash, reviewer, timestamp and protocol versions;
- committed bytes match the recorded package hash.

## Rollback and failure

A failed review returns the package to `draft` through a new revision or a recorded review outcome. The rejected reviewed artifact is retained as evidence when it has already been committed.

No workflow converts a failed package into `blank`; blank state is reserved for deterministic untouched templates.

## Relationship to PILOT-0001

The lifecycle applies to all 25 prepared candidate packages. Entering draft, reviewed or frozen state does not promote a panel into the final 12-panel pilot. Final pilot adjudication remains governed separately by issue #3.
