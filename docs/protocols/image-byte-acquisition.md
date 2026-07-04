# Image Byte Acquisition Protocol

## Scope

This protocol acquires institutional image byte streams and records provenance. It does not normalize, crop, rotate, segment or interpret images.

## Canonical representation

The canonical analytical source for `SOURCE-FREEZE-0001` is each canvas's full-size JPEG URL from Yale's IIIF manifest.

A TIFF rendering is a separate representation. When available, its URL may be recorded and acquired under a different representation identifier. It must never overwrite or masquerade as the JPEG object.

## Streaming

Downloads are processed in fixed-size chunks. The SHA-256 digest and byte count are updated while streaming. A completed object is moved atomically into content-addressed storage only after the stream ends successfully.

## Content-addressed storage

Objects are stored outside Git as:

```text
<store-root>/sha256/<digest[0:2]>/<digest>.<extension>
```

A local index may point from `child_oid` and representation to the content-addressed object.

## Resume and corruption handling

- A verified existing object is reused only after its digest and size are checked.
- Temporary partial files have a `.part` suffix and are never treated as complete.
- A mismatch is retained as an explicit failure; the expected record is not rewritten to fit the corrupted object.
- Network failures may be retried with bounded exponential backoff.

## Required record fields

- source manifest SHA-256;
- child OID and canvas ID;
- institutional label;
- representation identifier;
- source URL;
- final resolved URL;
- SHA-256;
- byte count;
- media type;
- ETag and Last-Modified when supplied;
- acquisition timestamp;
- status and error details;
- content-addressed relative path when bytes are retained.

## Freeze rule

A source freeze is invalid if any expected asset is absent, duplicated, failed, tied to a different source-manifest hash or represented by a zero-byte object.
