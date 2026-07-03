# ADR-0001: Build an independent canonical corpus

- Status: Accepted
- Date: 2026-07-03

## Context
Existing transliterations embody decisions about glyph identity, ligatures, spaces and uncertain marks. Those decisions may bias structural and spectral results.

## Decision
Construct the canonical corpus directly from primary images. Existing transliterations are stored only as isolated external references and may be aligned after a corpus freeze.

## Consequences
The project bears the cost of independent annotation, but gains traceability and the ability to measure representation dependence instead of inheriting it invisibly.
