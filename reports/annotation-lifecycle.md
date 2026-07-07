# Annotation lifecycle validation

## Scope

This report records the implementation boundary for `ANNOTATION-LIFECYCLE-0001`.

The lifecycle tooling validates package-state transitions, predecessor chains, technical-review gates, source identity, revision increments, explicit uncertainty changes and immutable freeze records.

## Implemented transitions

```text
blank -> draft
draft -> draft
draft -> reviewed
reviewed -> draft
reviewed -> frozen
frozen -> superseded
```

A lifecycle `reviewed` record references unchanged draft package bytes. A `frozen` record references a new frozen package revision whose observational payload is identical to the reviewed draft. A `superseded` record references the original frozen bytes and does not rewrite them.

## Technical review boundary

Technical review verifies package integrity and provenance. It requires a reviewer distinct from the annotator and a complete passing checklist.

It does not claim independent scientific adjudication, validate semantic interpretation or authorize final PILOT-0001 selection.

## Freeze gate

The validator requires:

- accepted technical review;
- complete predecessor package chain;
- immutable freeze declaration;
- package and source SHA-256 agreement;
- fixed protocol versions;
- provenance coverage for all entities in the frozen package;
- no observational changes between reviewed and frozen states.

## Uncertainty and deletion

Entities cannot disappear between package revisions. Changed entities require revision events that bind previous and resulting entity hashes. A reduction in visibility or segmentation uncertainty requires an explicit `uncertainty_update` event.

## Current limitation

No production annotation package has entered draft, reviewed or frozen state. The implementation is validated with deterministic synthetic package chains and is ready for a controlled technical annotation trial.
