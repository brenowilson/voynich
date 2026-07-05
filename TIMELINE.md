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
