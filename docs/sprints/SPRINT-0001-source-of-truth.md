# Sprint 0001 — Source of Truth

## Goal

Create the first reproducible path from the institutional manuscript images to an immutable, machine-readable primary-source manifest.

This sprint does not perform transliteration, glyph classification, linguistic analysis or spectral interpretation.

## Deliverables

1. Official Yale/Beinecke source record for MS 408.
2. Acquisition script or documented manual fallback.
3. Immutable metadata snapshot for every accessible image asset.
4. SHA-256 checksum inventory.
5. Page/folio manifest with dimensions, source identifiers and foldout relationships.
6. Source audit describing missing, duplicated, recompressed or ambiguously identified images.
7. Selection criteria for a small pilot annotation set.

## Canonical output paths

```text
sources/primary/yale/collection.json
sources/primary/yale/assets.jsonl
sources/primary/checksums/sha256.txt
sources/primary/manifests/pages.csv
sources/primary/manifests/foldouts.csv
reports/source-audit.md
scripts/acquire_yale.py
scripts/build_page_manifest.py
```

## Acceptance criteria

- Re-running the acquisition process produces the same asset inventory or a documented upstream change.
- Every acquired file has a stable local name, source URL or source identifier, byte size and SHA-256 hash.
- Every analytical derivative can identify its exact parent asset.
- Institutional foliation is used instead of PDF page numbers.
- Foldouts and multi-panel images remain explicitly related.
- The HolyBooks PDF is retained only as a non-canonical access facsimile.
- No external transliteration is consulted or imported.

## Pilot selection rule

Do not select pilot folios by convenience alone. After the manifest is complete, choose a small set spanning materially different layouts, image quality and graphical density. Selection criteria must be recorded before annotation begins.

## Stop condition

The sprint ends when the primary source inventory is frozen as `SOURCE-FREEZE-0001` and independently reproducible.
