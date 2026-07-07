# ADR-0002: Technical review is not scientific adjudication

## Status

Accepted.

## Context

The project currently lacks an independent scientific reviewer. That absence must not block package-integrity work, but it must also not be disguised by calling technical validation independent review.

## Decision

Technical review and scientific adjudication are separate gates.

Technical review checks source identity, coordinates, geometry, identifiers, revision events, uncertainty preservation, predecessor chains and deterministic validation. It may be performed before an independent scientific reviewer is available.

Scientific adjudication evaluates observational choices, protocol adequacy, sampling and disagreements. It requires a genuinely independent reviewer and remains outside `ANNOTATION-LIFECYCLE-0001`.

## Consequences

- A package may become technically reviewed and frozen without claiming scientific consensus.
- Lifecycle records must keep `scientific_adjudication_used = false` until a later explicit protocol authorizes otherwise.
- Technical review cannot close issue #3 or authorize the final 12-panel pilot.
- Reports must name the review type rather than using the ambiguous word “review” alone.
