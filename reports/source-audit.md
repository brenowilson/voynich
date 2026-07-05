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

## Canonical page and side manifest

The canonical page layer contains **213 deterministic records**. Each record links one institutional image asset to:

- its neutral photographic panel ID;
- zero, one or several explicit physical-side parents;
- source dimensions, byte count and SHA-256;
- stored-object path and rights status;
- composition status and uncertainty state.

Nine records are support views. The remaining 204 are manuscript-image records. The model never treats PDF page numbering as evidence and never promotes image sequence to physical or reading order.

The machine-readable outputs are:

- `sources/primary/manifests/pages.jsonl`;
- `sources/primary/manifests/pages.csv`;
- `sources/primary/manifests/asset-side-relations.csv`;
- `schemas/page-manifest.schema.json`.

## Foldout evidence

The Yale physical description reports ten folding leaves in total:

- five double-folio leaves;
- three triple-folio leaves;
- one quadruple-folio leaf;
- one sextuple-folio leaf.

The institutional collation places them in quires IX, X, XI, XIV, XV, XVI and XVII. The project records this evidence in `sources/primary/yale/foldout-codicology.json`.

The canonical foldout layer contains:

- **7 quire-level foldout complexes**;
- **10 physical folding-leaf slots** matching the institutional totals;
- **40 photographic-panel relations**;
- all **21 label-derived composite or fragmented candidates**;
- **4 panels** assigned directly to the explicitly identified 85–86 sextuple leaf;
- no asserted reading order.

The outputs are:

- `sources/primary/manifests/foldout-complexes.jsonl`;
- `sources/primary/manifests/foldout-panel-relations.csv`;
- `sources/primary/manifests/foldouts.csv` for the earlier label-derived candidate layer;
- `schemas/foldout-complex.schema.json`.

## Foldout uncertainty boundary

A foldout complex is a codicological evidence container, not a reconstructed reading sequence.

For quire XIV, the institutional catalog explicitly identifies folios 85r–86v as one sextuple-folio folding leaf. The four corresponding Yale photographic panels are therefore linked to one physical-leaf slot. Their internal panel order remains unresolved.

For quires IX, XV and XVII, the catalog states that more than one folding leaf is present. The project creates the correct number and extent of physical-leaf slots but does not assign individual photographs to those slots when the institutional labels and collation do not uniquely determine the split.

For quires X, XI and XVI, the quire-level folding-leaf profile is known, but digital panels are not silently assigned to the physical leaf merely because they occur within the folio range.

The following are explicitly false in the canonical model:

- asset sequence equals reading order;
- pixel width equals physical leaf extent;
- a side token describes complete foldout geometry;
- overlapping photographed labels uniquely identify physical-leaf membership.

Unresolved assignments remain empty rather than being guessed.

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
- External transliterations, Currier classifications and third-party segmentations did not inform acquisition, folio modeling or source freezing.
- No semantic, linguistic or glyph-identity claim is encoded in the primary-source inventory.
- No unresolved foldout geometry is converted into a reading-order claim.

## Source-layer conclusion

The canonical source, page, side, panel and foldout-complex layers are now machine-readable, deterministic and testable. Remaining geometric questions are preserved as explicit unresolved states rather than treated as blockers or silently guessed.
