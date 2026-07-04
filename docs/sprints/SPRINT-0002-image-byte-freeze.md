# Sprint 0002 — Image Byte Freeze

## Goal

Acquire every canonical Yale IIIF image byte stream in a reproducible way, compute a SHA-256 digest for each asset, retain the bytes outside Git commits and produce the evidence required for `SOURCE-FREEZE-0001`.

## Canonical byte representation

For this sprint, the canonical analyzable byte stream is the full-size JPEG URL declared by Yale's IIIF manifest for each canvas.

The original TIFF rendering, when available, is recorded as a higher-fidelity institutional alternative but is not silently substituted. JPEG and TIFF are distinct representations and receive distinct provenance records.

## Storage rule

Image binaries must not be committed to Git. The downloader writes to a content-addressed external directory:

```text
<store-root>/sha256/<first-two-hex>/<full-sha256>.<extension>
```

The repository stores only manifests, hashes, sizes, HTTP metadata and source URLs.

## Deliverables

- streamed downloader with resume support;
- content-addressed local store;
- one JSONL record per verified asset;
- SHA-256 checksum list;
- deterministic summary and failure report;
- sharded GitHub Actions validation;
- freeze builder that refuses incomplete or inconsistent inventories.

## Acceptance criteria

- every expected asset has exactly one successful JPEG byte record;
- recorded byte counts match the bytes actually hashed;
- repeated runs reuse verified objects and detect corruption;
- failures remain explicit and resumable;
- the freeze references the exact Yale manifest hash;
- binaries remain outside Git history;
- no foliation or semantic inference is introduced.

## Stop condition

`SOURCE-FREEZE-0001` may be declared only after all 213 expected assets are verified against the same canonical manifest snapshot and the freeze builder reports zero missing, duplicate or failed records.
