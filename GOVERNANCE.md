# Governance

## Canonical layers
1. Primary source: immutable image and metadata records.
2. Observation: geometry, segmentation, instances and uncertainty.
3. Derived structure: graphs, operators, statistics and spectra.
4. Hypotheses: interpretations that may be replaced without rewriting observations.
5. External comparison: isolated alignments to third-party work.

## Decision rule
A statement becomes a project commitment only when encoded in a versioned definition, protocol, schema, hypothesis record or Architecture Decision Record.

## Repository boundary
All Voynich work is performed in `brenowilson/voynich`. No changes belonging to this project may be made in the separate `Riemann` repository.

## Corpus freezes
A freeze names an immutable set of observations and schemas. External comparisons must identify the freeze they used.

## Issue and pull request lifecycle

Issues represent unfinished objectives, blocked work or explicitly retained decisions. Pull requests represent a concrete reviewable change set.

- Every non-trivial pull request must reference at least one issue using `Refs #N`, `Relates to #N` or a closing keyword when closure is justified.
- `Closes #N` or `Fixes #N` may be used only when the pull request satisfies every acceptance criterion of that issue.
- A merged pull request does not automatically imply that the associated issue is complete.
- An issue remains open while acceptance criteria are unmet, even when one or more supporting pull requests have merged.
- A pull request should not remain open after its change set has been merged, superseded, abandoned or cancelled.
- Superseded or cancelled pull requests are closed with a comment naming the replacement or reason.
- Blocked issues receive a status comment identifying dependencies and the condition that will unblock them.
- Active issues receive periodic checkpoints summarizing completed work, remaining work and the next expected pull request.
- Before opening a pull request, confirm that its branch has a single coherent purpose and that the target issue is still open and correctly scoped.
- After merge, review every referenced issue and either close it with evidence or add a checkpoint explaining why it remains open.

## Negative results
Failed hypotheses and null findings are retained in `experiments/negative-results/` when scientifically informative.
