# Yale Source Audit — Bootstrap

- Status: validated metadata acquisition; source freeze not yet declared
- Institutional object: Beinecke MS 408
- Yale parent OID: `2002046`
- Manifest SHA-256: `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23`
- Validation workflow run: `28686501175`
- Validation head: `cc1966b0ad7b9f4ab74604ed00cd7b9bb0b4f0f6`

## Inventory result

The official Yale IIIF manifest normalized successfully into **213 canvas/image records**. Each record has a canvas identifier, institutional label, child OID, pixel dimensions, IIIF image-service endpoint and direct image URL.

The inventory contains **210 unique institutional labels**. Repeated labels occur only where Yale exposes separate photographed parts of the same physical side:

- `70v (part)` — 2 assets;
- `72v (part)` — 2 assets;
- `102v (part)` — 2 assets.

These are not treated as duplicate files. Their child OIDs and image dimensions differ.

## Non-folio assets

The manifest also contains binding and support views:

- front and back covers;
- inside front cover;
- back flyleaf / inside back cover;
- head, tail, fore-edge and spine.

These remain in the primary inventory but must not be silently mixed with manuscript-side observations.

## Foldouts and composite photographs

Several canvases represent more than one folio side or only a photographed part. Examples include:

- `69v and 70r`;
- two separate `70v (part)` assets;
- `71v and 72r` and two `72v (part)` assets;
- the multi-image `85–86` foldout group;
- `88v and 89r`, `89v (part)` and `89v (part) and 90r`;
- `94v and 95r` plus `95v (part)`;
- `100v and 101r`, `101v (part) and 102r` and two `102v (part)` assets.

A canvas is therefore not equivalent to one folio side. The next manifest layer must model many-to-many relationships between assets, physical sides and photographed panels.

## Gaps in simple labels

A mechanical scan of labels matching only `number + r/v` does not find the following folio numbers in that simple form:

`12, 59–64, 70, 72, 74, 85, 86, 89, 91, 92, 97, 98, 101, 102, 109, 110`.

This is **not** interpreted as a list of acquisition failures. Some numbers are absent because the manuscript lacks those leaves; others are represented inside composite or part labels. The mapping must be resolved against institutional codicological metadata rather than guessed from sequence position.

## Image geometry

Ordinary photographed sides are generally around 2,600–3,000 pixels wide and 3,700–3,900 pixels high. Composite and foldout assets are substantially wider, with the largest normalized canvas in this snapshot measuring `7925 × 7268` pixels.

Geometry is retained exactly as provided by the IIIF manifest. No resizing, deskewing, cropping or perspective correction has been applied.

## Current limitations

1. The audit validates the IIIF manifest and machine-readable asset inventory, not yet the byte-level hash of every full-resolution image.
2. `folio_id` remains deliberately unresolved in `pages.csv`; institutional labels are preserved verbatim.
3. Foldout reconstruction and panel ordering have not been inferred.
4. Rights and reuse conditions must be captured before redistributing image bytes.
5. The HolyBooks PDF remains a non-canonical access facsimile and is excluded from pixel-level provenance.

## Next action

Build a physical-side/panel relation table from institutional labels and codicological evidence, then implement streamed image acquisition and SHA-256 verification without committing large image binaries to Git.
