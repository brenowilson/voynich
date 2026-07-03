# Asset-to-Side Relation Protocol

## Purpose

Represent the relation between a Yale image asset and folio-side identifiers explicitly written in the institutional label.

## Allowed derivation

The parser may extract tokens matching:

```text
<number><r|v>
<number><r|v> (part)
```

Examples include `1r`, `70v (part)` and the two explicit tokens in `69v and 70r`.

## Prohibited inference

The parser must not infer:

- a missing folio or side from neighboring sequence positions;
- reading order from the order of photographs;
- physical adjacency;
- a full side from a photographed part;
- equivalence between two assets carrying the same label;
- panel geometry or foldout reconstruction;
- manuscript structure from a conventional section name.

## Relation order

`relation_index` records only the left-to-right order in which side tokens occur in the institutional label. It is not a reading-order claim.

## Coverage

- `part`: the institutional label explicitly marks the token as a part;
- `full_or_unspecified`: no part marker follows that token. This does not prove that the photograph contains a complete physical side.

## Composite candidates

An asset is flagged as a label-derived composite candidate when the label:

- contains more than one explicit side token;
- contains an explicit `(part)` marker; or
- contains the word `foldout`.

A candidate flag is evidence for manual review, not a reconstructed codicological relation.

## Outputs

- `asset-side-relations.csv`: one row per explicit side token;
- `foldouts.csv`: composite and fragmented candidates derived from label evidence;
- `non-folio-assets.csv`: assets whose labels contain no folio-side token.
