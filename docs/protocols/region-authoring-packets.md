# REGION-AUTHORING-PACKETS-0001

## Purpose

Provide a reproducible authoring surface for the five panels in `REGION-ANNOTATION-TRIAL-0001` without copying Yale image bytes into Git.

Each packet binds an empty region-input document and an SVG coordinate overlay to one immutable `R000` package.

## Packet contents

Each packet records:

- trial and candidate IDs;
- photographic panel ID;
- source URL, source SHA-256, width and height;
- blank package ID, path and SHA-256;
- coordinate origin and units;
- empty annotator and timestamp fields;
- an empty regions array;
- explicit false flags for interpretation, transliteration, reading order, technical completion, scientific adjudication and production freeze.

The accompanying SVG:

- has width and height equal to the canonical source image;
- uses `viewBox="0 0 width height"`;
- references the official institutional image URL;
- embeds no raster bytes;
- contains an initially empty `region-overlays` group.

## Authoring rules

The annotator fills only:

- `annotator_id`;
- `annotated_at`;
- `regions`.

All source, package and control fields are immutable.

Every region uses the fields already defined by `OBSERVATION-PROTOCOL-0001`:

- neutral region ID;
- observational role;
- source-pixel polygon;
- confidence;
- visibility;
- active status;
- neutral evidence note.

No field may contain a transcription, character identity, word boundary, language, semantic label, Currier class or reading-order assertion.

## Coordinate integrity

The SVG is a coordinate reference, not a transformed canonical image. Polygon points committed to JSON must be read in the SVG viewBox coordinate system, which exactly matches immutable Yale source pixels.

Resized browser display is acceptable because SVG interaction maps back to the viewBox. Coordinates copied from screenshots, the HolyBooks facsimile or other transformed images are not acceptable.

## Conversion

A completed packet is converted into:

- one `R001 draft` observation package;
- one blank lifecycle record;
- one draft lifecycle record;
- one SVG overlay containing the region polygons.

Conversion validates source identity, immutable packet fields, polygon bounds, region roles, revision events and the `blank → draft` lifecycle transition.

## Review boundary

Generated drafts remain unreviewed. The packet tools do not mark technical review complete and do not create freeze records.

A later technical-review iteration may inspect the draft JSON and SVG overlay. Independent scientific adjudication remains separate.

## Rights boundary

The repository stores URLs and vector coordinates only. It does not embed or redistribute Yale image binaries.
