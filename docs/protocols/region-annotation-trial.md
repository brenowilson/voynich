# REGION-ANNOTATION-TRIAL-0001

## Purpose

Exercise the source-anchored `blank → draft → technical review` path on a small deterministic set before any production annotation campaign or final PILOT-0001 selection.

The trial tests annotation mechanics, provenance and quality control. It does not claim that the selected panels are the final pilot, that the regions are scientifically adjudicated or that a frozen observational corpus exists.

## Trial selection

The input is the committed 25-package observation work queue.

For each of its five deterministic batches:

1. retain entries whose candidate metadata has `composition_status = single_side_or_unspecified`;
2. sort retained entries by canonical source sequence index and candidate ID;
3. choose the first entry.

The selection uses only frozen metadata and queue assignments. Primary visual-coding values, annotation outcomes, external transliterations, conventional sections and analytical results are forbidden.

## Trial scope

Exactly five packages are prepared, one per work-queue batch.

Only broad region candidates may be added in the first draft revision. Lines, glyph candidates, ambiguity groups, reading order and character identities remain outside this trial.

Permitted region roles are observational occupancy bins:

```text
text_bearing
graphic_bearing
mixed
unmarked_or_background
obscured_or_damaged
uncertain
```

These labels do not identify subject matter, language, manuscript section or meaning.

## Coordinate rules

- all polygons use immutable full-size Yale source-image pixels;
- origin is the upper-left source pixel;
- x increases rightward and y downward;
- displayed, resized or rotated coordinates are not committed;
- each polygon must lie inside the source dimensions;
- every region must have a neutral panel-local ID.

## Draft creation

A trial draft:

- starts from the committed `R000 blank` package;
- becomes revision `R001`;
- names the `R000` package as its predecessor;
- preserves panel ID, institutional ID, source URL, dimensions, stored path and source SHA-256;
- records annotator and timestamp;
- adds one `add` revision event for every region;
- contains no lines, glyphs or ambiguity groups;
- remains `package_status = draft`.

The committed `R000` package is never modified.

## Self-check

Before technical review, the annotator confirms:

1. every polygon is tied to visible boundaries rather than inferred meaning;
2. uncertain boundaries use lower confidence, uncertain visibility or the `uncertain` role;
3. no region exists merely to match an expected section or transcription;
4. source pixels, not display pixels, were recorded;
5. every region has a matching add event and resulting entity hash;
6. line and glyph segmentation has not begun.

## Technical review

Technical review checks package validity and provenance under `ANNOTATION-LIFECYCLE-0001`:

- source identity;
- geometry;
- IDs;
- event coverage;
- absence of prohibited fields;
- predecessor linkage;
- deterministic revalidation.

It does not determine whether the visual partition is scientifically optimal. Independent scientific adjudication remains a later gate.

## Stop conditions

The trial pauses rather than forcing a result when:

- a region boundary cannot be represented without semantic inference;
- the source image is insufficient to anchor coordinates;
- a panel requires foldout geometry not captured by the photographic panel;
- region-only annotation would implicitly assert line or reading order;
- validation reveals that the current schema cannot preserve the uncertainty.

A stop condition is a useful protocol result, not a failed annotation.

## Outputs

```text
corpus/pilots/PILOT-0001/region-annotation-trial/manifest.json
```

Later annotation iterations may add draft packages, lifecycle records and technical-review records under a separate data PR. Preparing the manifest and tooling does not authorize production freeze.

## Reproduction

```text
PYTHONPATH=src python scripts/build_region_annotation_trial.py
```

The generated manifest must match the committed manifest exactly regardless of input record order.
