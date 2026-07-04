# Yale Image Byte Verification

- Status: verification complete; durable source freeze pending
- Representation: `iiif-full-jpeg`
- Source manifest SHA-256: `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23`
- Expected assets: 213
- Verified byte streams: 213
- Unique child OIDs: 213
- Unique image SHA-256 values: 213
- Total bytes streamed: 560,960,374
- Smallest asset: 688,476 bytes
- Median asset: 2,392,238 bytes
- Largest asset: 12,711,585 bytes
- Stable content inventory SHA-256: `b6898d67c062bd91e13a0b258c53195434deb7ba13c960554c57e24ab16cd975`
- Full record-set SHA-256: `3acf513fb2f65c459f46904da4ed60b3c1545fde769ee82e416f6330e52b9f8a`
- Canonical record file SHA-256: `b4c5b607a9b7084d64a1525218b3b79ccf80abb0b3ffd28585119b0597a5a39e`
- GitHub Actions run: `28690625639`
- Workflow head: `5158128a33a56cc945f020eea466c1c0aad9f527`
- Evidence artifact: `source-freeze-0001-verification` (`8077015204`)
- Artifact SHA-256: `e637cfd41161949e15d56bcdcafc57b74a1aa8150c557ecde851c55cfe41eb75`
- Artifact expiry: 2026-10-02

## Interpretation

Every canonical Yale IIIF JPEG endpoint in the 213-asset inventory returned a non-empty image byte stream. Every stream was hashed independently, and all 213 image digests are unique.

This is a complete **verification pass**, not `SOURCE-FREEZE-0001`. The CI runners discarded image bytes after hashing. A formal source freeze requires the same 213 objects to be retained in durable content-addressed storage and revalidated from that store.

## Reproduction

The sharded workflow is `.github/workflows/hash-yale-images-full.yml`. The downloader is `scripts/acquire_image_bytes.py`, and the strict freeze validator is `scripts/build_source_freeze.py`.
