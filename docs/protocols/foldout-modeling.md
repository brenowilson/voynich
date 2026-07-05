# Foldout Modeling Protocol

## Purpose

Represent Yale's digital photographs, physical folio sides and folding leaves without converting image order or visual appearance into unsupported codicological claims.

## Evidence layers

The model separates three evidence classes:

1. **Institutional asset evidence** — Yale canvas IDs, child OIDs, labels, dimensions and source URLs.
2. **Explicit label relations** — folio-side tokens written in Yale labels, including `part`, multi-side and `foldout` markers.
3. **Institutional codicology** — the physical description and quire-level folding-leaf profile in the Beinecke MS 408 catalog.

No lower layer may silently strengthen a claim from a higher layer.

## Entities

### Photographic panel

A `YDC-PANEL-*` identifier denotes one Yale image asset. It does not imply that the image is one complete physical page.

### Physical side

A side identifier such as `70v` is retained only when it appears explicitly in an institutional label. Coverage is recorded as `part` or `full_or_unspecified`.

### Foldout complex

A foldout complex groups photographic panels and physical-side tokens within a quire for which Yale states a folding-leaf profile. It is an evidence container, not a reading sequence.

### Physical folding-leaf slot

A slot represents one folding leaf required by the institutional profile. Its extent is `double`, `triple`, `quadruple` or `sextuple`.

A panel is assigned to a slot only when the institutional evidence uniquely supports that assignment. Otherwise the slot exists while panel membership remains unresolved.

## Canonical rules

- Asset sequence is never reading order.
- Pixel width is never used as proof of physical leaf extent.
- A label token is never treated as a complete geometric reconstruction.
- Composite photographs may have several physical-side parents.
- Repeated partial labels remain separate photographic assets.
- Empty physical-leaf assignments are valid and scientifically preferable to guesses.
- Reading order is always `null` or empty in the source layer.

## Current explicit assignment

The institutional catalog identifies folios `85r–86v` as one sextuple-folio folding leaf. The four Yale panels labeled as parts or faces of the 85–86 foldout are assigned to one sextuple leaf slot.

No internal ordering among those four photographs is asserted.

## Current unresolved assignments

Quires IX, XV and XVII contain more than one folding leaf. Their required leaf slots are represented, but overlapping side labels do not uniquely determine which photograph belongs to which physical leaf.

Quires X, XI and XVI have a known quire-level foldout profile. Panels in the associated folio range are related to the complex, but are not individually assigned to the folding leaf solely because they fall within that range.

## Validation requirements

A valid build must satisfy all of the following:

- 213 canonical page records;
- 7 foldout complexes;
- 10 physical folding-leaf slots;
- profile totals of 5 double, 3 triple, 1 quadruple and 1 sextuple leaves;
- 40 panel-to-complex relations;
- all 21 label-derived composite candidates covered;
- exactly 4 panels assigned to the explicitly identified 85–86 sextuple leaf;
- no reading-order value;
- no panel assigned to more than one complex;
- all records valid against their JSON Schemas.

## Outputs

- `sources/primary/yale/foldout-codicology.json`
- `sources/primary/manifests/foldout-complexes.jsonl`
- `sources/primary/manifests/foldout-panel-relations.csv`
- `schemas/foldout-complex.schema.json`
