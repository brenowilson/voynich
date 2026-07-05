# PILOT-0001 Selection Protocol

## Purpose

Select a small, deliberately varied set of Yale image assets for testing the observational annotation protocol before any full-corpus annotation begins.

The pilot is not a claim about manuscript sections, language, meaning, glyph identity or reading order. It is a stress test of the observation process.

## Prerequisites

The protocol may run only after:

- `SOURCE-FREEZE-0001` is frozen and hash-verifiable;
- the canonical page manifest is valid;
- foldout complexes and unresolved panel geometry are explicit;
- external transliterations remain isolated from selectors and annotators.

## Two-stage design

### Stage A — metadata-only candidate pool

A deterministic script creates `PILOT-0001-CANDIDATES` before visual outcomes are coded.

The script may use only canonical source metadata:

- institutional IDs and labels;
- image dimensions and SHA-256 values;
- manuscript-image versus support-view status;
- explicit composite or partial-label status;
- foldout-complex membership;
- source sequence index for broad coverage across the manuscript.

It may not use:

- external transliterations;
- Currier classes;
- conventional section assignments;
- glyph frequencies or tokenization;
- semantic interpretations;
- later annotation or spectral results.

The candidate pool contains four metadata strata:

1. every panel assigned to an institutionally explicit physical folding leaf;
2. up to two deterministic representatives of each label-derived composite-candidate type;
3. at least one representative of each foldout complex;
4. two ordinary, non-foldout, non-composite manuscript images from each of eight sequence bins.

Within a stratum, ties are broken by SHA-256 ranking using the fixed seed `PILOT-0001`. The final candidate IDs are assigned after sorting by source sequence.

### Stage B — blinded visual coding

Candidate images are reviewed directly from the canonical Yale representation. Reviewers receive no external transliteration, conventional section label or global corpus statistic.

The coding form records only coarse observable properties:

- relative text coverage;
- relative graphic coverage;
- dominant graphic geometry;
- line-organization clarity;
- visual density;
- color presence;
- crop, occlusion or source-quality limitations;
- confidence and free notes.

These variables describe the photographed surface. They do not assert what an illustration depicts or what text means.

## Review discipline

Each candidate receives:

- one primary visual coding pass;
- an independent second pass for all finally selected panels and at least 25 percent of the remaining candidate pool;
- adjudication when categorical fields disagree or confidence is below `0.70`.

A reviewer must record `external_transliteration_consulted = false`. Any contaminated review is excluded and repeated.

## Final pilot size

The target final set is **12 panels**. A range of 10–14 is permitted only when documented constraints make 12 scientifically inferior.

The final selector must satisfy, where the candidate pool contains eligible examples:

- at least three ordinary single-side panels;
- at least three composite, partial or foldout panels;
- at least one panel from the institutionally explicit 85–86 sextuple leaf;
- at least one panel with limited or problematic source quality, crop or occlusion;
- at least one clearly organized and one ambiguous or mixed line layout;
- representation across at least six of the eight source-sequence bins;
- no more than two panels sharing the same exact visual feature vector;
- no more than two panels selected solely from one foldout complex.

After satisfying constraints, remaining slots are chosen by deterministic maximin distance over the frozen visual-coding variables. Ties use the fixed seed `PILOT-0001-FINAL`.

## Freeze sequence

1. Generate and commit the metadata-only candidate pool.
2. Declare `PILOT-CANDIDATES-FREEZE-0001` with a SHA-256 digest.
3. Perform blinded visual coding.
4. Freeze the observation table and adjudication log.
5. Run the deterministic final selector.
6. Review exclusions and protocol failures.
7. Declare `PILOT-SELECTION-FREEZE-0001`.

No candidate may be added after visual coding begins unless the candidate freeze is revoked, the reason is documented and all visual coding is restarted.

## Exclusions

The following are excluded from the pilot candidate pool:

- covers, edges, spine, flyleaves and other support views;
- assets without verified stored bytes;
- assets lacking source SHA-256 or dimensions;
- records derived only from the non-canonical HolyBooks PDF;
- any asset whose selection would require inferred reading order.

Support views remain in the source inventory and may later receive a separate conservation-oriented protocol.

## Known limitations

- Sequence bins provide broad positional coverage but are not codicological or semantic sections.
- Image dimensions are sampling metadata, not physical leaf measurements.
- A Yale photographic panel may show a partial or composite physical surface.
- Coarse visual coding is deliberately lossy and exists only to diversify protocol testing.
- The pilot cannot establish corpus-wide frequency or structural claims.

## Outputs

- `corpus/pilots/PILOT-0001/candidates.csv`
- `corpus/pilots/PILOT-0001/candidates.jsonl`
- `corpus/pilots/PILOT-0001/candidate-freeze.json`
- `corpus/pilots/PILOT-0001/visual-observations.jsonl`
- `corpus/pilots/PILOT-0001/adjudication.csv`
- `corpus/pilots/PILOT-0001/selection.csv`
- `corpus/pilots/PILOT-0001/selection-freeze.json`

At the current stage, only the protocol and metadata-only candidate pool are authorized. Visual coding and final selection are subsequent review stages.
