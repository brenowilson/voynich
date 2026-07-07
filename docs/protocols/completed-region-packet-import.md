# Completed region packet import

## Purpose

Convert one completed source-pixel region authoring packet into a reproducible, validated draft bundle without marking the package reviewed or frozen.

## Inputs

- one completed packet created from `REGION-AUTHORING-PACKETS-0001`;
- the exact committed `R000` blank package named by that packet.

The importer validates immutable packet fields, source identity, source dimensions, package SHA-256, region geometry, neutral region roles and prohibited-field exclusions.

## Outputs

```text
draft-package.json
lifecycle-records.jsonl
inspection-overlay.svg
import-manifest.json
```

The manifest records SHA-256 identities for the input packet, blank package, draft package, lifecycle records and SVG overlay.

## Safety rules

- output is written through a temporary directory and moved into place only after validation;
- a nonempty destination is rejected unless `--overwrite` is explicitly supplied;
- overwrite replaces the complete bundle, not individual files;
- no source image binary is written;
- lifecycle states remain `blank` and `draft`;
- technical review, scientific adjudication and production freeze remain false.

## Command

```text
PYTHONPATH=src python scripts/import_completed_region_packet.py \
  --packet completed-packet.json \
  --blank-package corpus/pilots/PILOT-0001/observation-work-queue/packages/PILOT-0001-CAND-001.json \
  --output-root work/region-imports/PILOT-0001-CAND-001
```

Use `--overwrite` only when deliberately regenerating the entire output bundle from the same reviewed input file.

## Boundary

Successful import means that the data is structurally valid and traceable. It does not mean that region boundaries have passed technical review or independent scientific adjudication.
