# Project Timeline

## 2026-07-03 — Project inception

### Decision
Build an independent visual corpus directly from primary manuscript images.

### Rationale
Existing transliterations encode segmentation, spacing and glyph-identity choices that could contaminate structural analysis.

### Consequences
- External transliterations remain isolated.
- The observational corpus contains no semantic or linguistic claims.
- Every retained observation must be traceable to image coordinates and source hashes.
- Comparisons with external work occur only after a declared corpus freeze.

### Inputs
- Voynich Manuscript facsimile supplied by Breno.
- Initial direction discussed by Breno and Virendra.
- Interest in structural and spectral methods informed by work on the separate Riemann project.

### Status
Accepted.

## 2026-07-03 — Interpretation discipline

### Decision
Examples, analogies and borrowed mathematical vocabulary used in discussion are treated as approximations of intent, not literal model commitments.

### Rationale
The project is deliberately exploring structures that may not fit existing linguistic, semantic or mathematical labels. Premature literalization would convert explanation into hidden assumptions.

### Consequences
- Infer the intended abstraction behind an example before formalizing it.
- No example defines an ontology, operator, unit or hypothesis unless promoted through an explicit decision record.
- Formal commitments must be written as definitions, protocols, hypotheses or ADRs.

### Status
Accepted.

## 2026-07-03 — Canonical Yale source bootstrap

### Result
The official Yale IIIF manifest for Beinecke MS 408 was acquired and normalized successfully.

### Evidence
- Parent OID: `2002046`.
- Manifest SHA-256: `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23`.
- Normalized canvas/image records: `213`.
- Automated parser, acquisition and output validation completed successfully in GitHub Actions run `28686501175`.

### Consequences
- The institutional IIIF manifest replaces the HolyBooks PDF as the canonical digital source index.
- Institutional labels remain verbatim; physical folio and foldout relationships are not inferred silently.
- Byte-level verification and durable storage are required before `SOURCE-FREEZE-0001` can be declared.

### Status
Validated; not frozen.

## 2026-07-04 — Complete Yale image byte verification

### Result
All 213 canonical full-size Yale IIIF JPEG endpoints were streamed completely and hashed independently.

### Evidence
- Verified byte streams: `213 / 213`.
- Unique child OIDs: `213`.
- Unique image SHA-256 digests: `213`.
- Total bytes streamed: `560,960,374`.
- Stable content-inventory SHA-256: `b6898d67c062bd91e13a0b258c53195434deb7ba13c960554c57e24ab16cd975`.
- GitHub Actions run: `28690625639`.
- Detailed report: `reports/source-byte-verification.md`.

### Consequences
- The downloader, sharding strategy and strict freeze validator passed live institutional-source validation.
- The complete byte identity of the current Yale JPEG representation became known.
- The initial CI run discarded downloaded images after hashing and was verification-only.

### Status
Byte verification complete.

## 2026-07-04 — SOURCE-FREEZE-0001 declared

### Result
The 213 canonical Yale image objects were retained in a durable content-addressed external store and independently revalidated after transfer.

### Evidence
- External archive objects: `16`.
- Stored objects restored and rehashed: `213 / 213`.
- Missing, duplicate or mismatched objects: `0`.
- Total source-image bytes: `560,960,374`.
- Frozen record-set SHA-256: `23b37de04ce9bb7cc6ef3920612418ef78a0bbfa4fa6107c04a32740456ad0e0`.
- Stable frozen content-inventory SHA-256: `eadd4ee6ebe176b1de38cd48796966f819bffbe8d1e5ba0f8f05387fba1a5131`.
- Freeze record: `sources/primary/freezes/SOURCE-FREEZE-0001.json`.
- Merge commit: `ca5133568e90a5c6a2e15dc86422a095f8100042`.

### Consequences
- Primary-source byte identity is immutable and reconstructable from documented archives.
- Image binaries remain outside Git history.
- External transliterations remain excluded from the canonical source and observation layers.
- Physical folio-side and foldout-panel modeling remains a separate unresolved task.

### Status
Frozen.

## 2026-07-04 — Yale rights and reuse boundary documented

### Decision
Preserve the absence of an item-specific IIIF rights value and record Yale's institutional reuse policy without inventing a license.

### Consequences
- The repository does not assert a Creative Commons or other item-specific license.
- The durable source store remains private and access-controlled.
- Public reuse requires independent legal assessment, Yale provenance and the institutional credit line where applicable.
- Rights evidence is recorded in `sources/primary/yale/rights.json`.

### Status
Accepted.

## 2026-07-05 — Canonical page and foldout model completed

### Result
The institutional image inventory was converted into deterministic page, side, panel and foldout-complex layers while preserving unresolved physical geometry explicitly.

### Evidence
- Canonical page records: `213`.
- Support views separated from manuscript images: `9`.
- Label-derived composite or fragmented candidates: `21`.
- Quire-level foldout complexes: `7`.
- Physical folding-leaf slots: `10`.
- Panel-to-complex relations: `40`.
- Panels assigned to the institutionally explicit 85–86 sextuple leaf: `4`.
- Reading-order values asserted: `0`.
- Page-manifest schema version: `0.2.1`.
- Foldout-complex schema version: `0.1.0`.

### Consequences
- A photographic asset is no longer treated as equivalent to one physical folio side.
- The five double, three triple, one quadruple and one sextuple folding leaves reported by Yale are represented as explicit physical-leaf slots.
- Ambiguous panel-to-leaf assignments remain unresolved rather than guessed.
- The institutional IIIF manifest's absence of original filenames is recorded explicitly as `null`, with stable Yale identifiers and URLs retained instead.
- The source layer contains no inferred reading order, semantic section or transliteration-derived structure.

### Status
Completed and ready for pilot-set selection.

## 2026-07-05 — PILOT-CANDIDATES-FREEZE-0001 declared

### Result
A metadata-only candidate pool was selected and frozen before any visual outcome was coded.

### Evidence
- Frozen candidates: `25`.
- Ordinary non-foldout candidates: `14`.
- Composite or fragmented candidates: `10`.
- Additional ordinary foldout-complex representative: `1`.
- Source-sequence bins represented: `8 / 8`.
- Foldout complexes represented: `7 / 7`.
- Institutionally explicit 85–86 sextuple-leaf panels retained: `4 / 4`.
- Candidate-set SHA-256: `d460d6cc7c200f87e2b3182c1783079a6181bad01d0a83a8bd899b0cc7b8c113`.
- Visual outcomes used: `0`.
- External transliterations used: `0`.

### Consequences
- Candidate eligibility is immutable before blinded visual coding begins.
- Support views, unverified records and non-canonical PDF-derived pages are excluded.
- Conventional sections, semantic interpretations, Currier classes and glyph statistics did not influence the pool.
- Adding or removing a candidate now requires revoking the freeze and restarting visual coding.

### Status
Candidate pool frozen; blinded visual coding pending.

## 2026-07-05 — OBSERVATION-PROTOCOL-0001 defined

### Result
The project gained a source-anchored, interpretation-neutral model for regions, line candidates, glyph candidates, ambiguity groups and revision events.

### Evidence
- Canonical coordinates use immutable Yale source-image pixels.
- Region, line and glyph geometry is validated against source bounds and parent polygons.
- Ambiguous splits, joins, overlaps and incomplete visibility are explicit states.
- Neutral identifiers do not encode reading order or glyph identity.
- Revision events preserve actor, time, reason and entity hashes.
- JSON Schemas and deterministic validators reject transcription, transliteration, words, semantic labels, Currier classes, reading order and analytical labels.
- A blank package for `YDC-PANEL-1006094` regenerates deterministically from the canonical page manifest.
- Validation workflow run: `28750637731`.

### Consequences
- Phase 2 annotation infrastructure can advance while final pilot selection remains blocked on an unavailable independent reviewer.
- Whole-panel pilot visual coding remains separate from source-anchored region and glyph observation.
- Corrections require superseding revisions rather than silent mutation.

### Status
Protocol and validation infrastructure complete; production annotation packages not yet created.

## 2026-07-06 — PILOT-0001 observation work queue materialized

### Result
All 25 frozen pilot candidates were prepared as deterministic revision-zero blank observation packages without using final-selection results or interpretive metadata.

### Evidence
- Source-anchored blank packages: `25`.
- Unique candidate IDs: `25`.
- Unique photographic panel IDs: `25`.
- Deterministic batches: `5`.
- Packages per batch: `5`.
- Candidate-set SHA-256: `d460d6cc7c200f87e2b3182c1783079a6181bad01d0a83a8bd899b0cc7b8c113`.
- Package-set SHA-256: `e49d132116aa2b819a2918a6f0395d93a2c1e5096022d36b8e04891c46a05690`.
- Complete committed-output validation run: `28826281665`.
- Audit report: `reports/observation-work-queue.md`.

### Consequences
- Every frozen candidate is ready to enter the `blank → draft → frozen` annotation lifecycle.
- No candidate is promoted into the final 12-panel pilot by this materialization.
- Annotation tooling and quality-control work can proceed while independent pilot adjudication remains unavailable.
- External transliterations, semantic labels, glyph identities, token boundaries and reading-order claims remain absent.

### Status
Materialized and reproducible; source-anchored annotation has not yet begun.

## 2026-07-07 — ANNOTATION-LIFECYCLE-0001 validated

### Result
The project gained deterministic lifecycle and freeze gates for source-anchored observation packages.

### Evidence
- Allowed lifecycle states: `blank`, `draft`, `reviewed`, `frozen`, `superseded`.
- Invalid direct transitions are rejected.
- Technical reviewer and annotator must be distinct.
- Frozen package bytes cannot return to an editable state.
- Silent entity disappearance is rejected.
- Reduced uncertainty requires an explicit `uncertainty_update` event.
- Freeze records bind package SHA-256, source SHA-256, predecessor chain and protocol versions.
- Lifecycle and observation validation workflows passed in runs `28885898732` and `28885898723`.
- Audit report: `reports/annotation-lifecycle.md`.

### Consequences
- Package-integrity review can proceed without pretending to be independent scientific adjudication.
- Corrections to frozen packages require a new revision rather than in-place mutation.
- Final PILOT-0001 selection remains governed separately by issue #3.

### Status
Lifecycle protocol and tooling validated; no production annotation package has entered draft state.

## 2026-07-07 — REGION-ANNOTATION-TRIAL-0001 prepared

### Result
A metadata-only five-panel region trial was selected from the committed observation work queue without using visual-coding outcomes or final pilot selection.

### Evidence
- Selected trial packages: `5`.
- Work-queue batches represented: `5 / 5`.
- Selection rule: earliest `single_side_or_unspecified` candidate in each deterministic batch.
- Selected candidates: `PILOT-0001-CAND-001` through `PILOT-0001-CAND-005`.
- Trial-set SHA-256: `3685282f851d1d14b798716077041a2070d895570c589c57ef318664e11a9988`.
- Validation run: `28887175088`.

### Consequences
- Region-only draft mechanics can be tested on a controlled set without promoting panels into the final pilot.
- Lines, glyphs, scientific adjudication and production freeze remain unauthorized.

### Status
Trial prepared; no region observations have been recorded.

## 2026-07-07 — REGION-AUTHORING-PACKETS-0001 materialized

### Result
Five source-pixel JSON authoring templates and five SVG coordinate overlays were generated for the controlled region trial.

### Evidence
- Empty authoring templates: `5`.
- Source-pixel SVG overlays: `5`.
- Packet-set SHA-256: `9b0343ee18b2b5d35fb95ee4711bddb92893a26def51a607c3fdc766fc6cd50a`.
- Embedded Yale image binaries: `0`.
- Authoring-packet validation run: `28887992619`.

### Consequences
- Annotators can enter polygons in canonical source-pixel coordinates while the repository stores only URLs and vector data.
- Completed packets can be converted into valid `R001 draft` packages and lifecycle records.
- Technical acceptance, scientific adjudication and production freeze remain separate future gates.

### Status
Authoring packets ready; no observational outcome has been entered.
