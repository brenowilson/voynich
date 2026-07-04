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
- The downloader, sharding strategy and strict freeze validator have passed live institutional-source validation.
- The complete byte identity of the current Yale JPEG representation is known.
- CI discarded the downloaded images after hashing, so the result is verification-only.
- `SOURCE-FREEZE-0001` remains blocked only by durable content-addressed retention and revalidation of the stored objects.

### Status
Byte verification complete; durable freeze pending.
