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
- Byte-level hashing of full-resolution image files remains pending before `SOURCE-FREEZE-0001` can be declared.

### Status
Validated; not frozen.
