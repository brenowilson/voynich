# Yale Source Audit — SOURCE-FREEZE-0001

## Status

Canonical source acquisition is complete and frozen.

- Institutional object: Beinecke MS 408
- Yale parent OID: `2002046`
- Canonical representation: full-size Yale IIIF JPEG
- Yale manifest SHA-256: `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23`
- Expected and verified assets: `213`
- Stored objects revalidated: `213`
- Total source-image bytes: `560,960,374`
- Stored-object record-set SHA-256: `23b37de04ce9bb7cc6ef3920612418ef78a0bbfa4fa6107c04a32740456ad0e0`
- Stable content-inventory SHA-256: `eadd4ee6ebe176b1de38cd48796966f819bffbe8d1e5ba0f8f05387fba1a5131`
- Freeze record: `sources/primary/freezes/SOURCE-FREEZE-0001.json`

## Provenance chain

The source chain is:

```text
Yale Digital Collections parent object 2002046
→ immutable IIIF manifest snapshot
→ 213 canvas and image-service records
→ 213 streamed full-size JPEG byte records
→ content-addressed objects
→ 16 checksummed external archive chunks
→ post-upload restoration and full rehash
→ SOURCE-FREEZE-0001
```

Every analytical source image is traceable to a Yale canvas identifier, child OID, image URL, institutional label, pixel dimensions, byte count, SHA-256 digest and content-addressed stored path.

Image binaries are not committed to Git. The repository retains the manifests, checksums, byte records, storage inventory, acquisition code and audit evidence. The durable private store is described in `sources/primary/storage/SOURCE-FREEZE-0001-storage.json`.

## Inventory result

The official Yale IIIF manifest normalizes to **213 canvas/image records** and **210 unique institutional labels**. Repeated labels occur where Yale exposes separate photographed parts of the same physical side:

- `70v (part)` — 2 assets;
- `72v (part)` — 2 assets;
- `102v (part)` — 2 assets.

These are distinct institutional assets with different child OIDs and image geometry. They are not treated as duplicate files.

All 213 image byte streams are non-empty and have distinct SHA-256 values.

## Non-folio assets

The canonical inventory includes nine binding or support views, including covers, inside covers, back flyleaf, head, tail, fore-edge and spine. They remain part of the primary-source freeze but are explicitly separated from manuscript-side observations.

## Foldouts and composite photographs

A Yale canvas is not necessarily equivalent to a single physical folio side. Composite and partial labels include:

- `69v and 70r`;
- two separate `70v (part)` assets;
- `71v and 72r` and two `72v (part)` assets;
- the multi-image `85–86` foldout group;
- `88v and 89r`, `89v (part)` and `89v (part) and 90r`;
- `94v and 95r` plus `95v (part)`;
- `100v and 101r`, `101v (part) and 102r` and two `102v (part)` assets.

The current relation tables extract only folio-side tokens explicitly present in Yale labels. They do not infer reading order, adjacency, missing leaves or foldout geometry. The definitive physical-side and panel model remains tracked by issue #2.

## Image geometry and byte identity

Ordinary photographed sides are generally around 2,600–3,000 pixels wide and 3,700–3,900 pixels high. Composite and foldout assets are substantially wider; the largest normalized canvas in this snapshot is `7925 × 7268` pixels.

No canonical source image has been resized, deskewed, cropped, rotated or perspective-corrected. Every byte record names the exact downloaded representation and its digest.

## Durable-store validation

The content-addressed source store was packaged into 16 independently checksummed ZIP objects. After upload to the external store, every ZIP was downloaded again and compared with its originating artifact digest. All matched.

The downloaded archives were unpacked into a clean store. All inner shard checksums passed, exactly 213 stored objects were reconstructed, and every object was reopened and checked against its byte record. Result: **213 verified stored objects and zero mismatches**.

Restoration and replication requirements are defined in `docs/protocols/source-store-replication.md`. Temporary GitHub Actions artifacts are not considered durable storage.

## Rights and reuse

The canonical IIIF manifest does not supply an item-specific `rights` or license value. This absence is preserved rather than replaced by an invented license.

Yale states in its institutional reuse policy that photographs and digitized copies of public-domain images are openly available for reuse. Yale also states that users remain responsible for legal assessment and necessary permissions and provides the preferred credit line `Courtesy of the Yale University Library`.

The project therefore records a policy-based assessment, not an item-specific license grant. Source bytes remain in a private external store and are not distributed through Git. The complete assessment and institutional policy sources are recorded in `sources/primary/yale/rights.json`.

## Canonical exclusions

- The supplied HolyBooks PDF is retained only as a non-canonical access facsimile.
- PDF page numbering is not a source identifier.
- External transliterations, Currier classifications and third-party segmentations did not inform acquisition or source freezing.
- No semantic, linguistic or glyph-identity claim is encoded in the primary-source inventory.

## Remaining source-layer work

The acquisition objective is complete. The remaining source-layer task is issue #2: construct and validate the canonical many-to-many model linking institutional assets, physical folio sides and photographed foldout panels without guessing reading order.
