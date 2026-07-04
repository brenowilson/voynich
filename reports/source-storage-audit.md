# SOURCE-FREEZE-0001 Storage Audit

## Result

The durable source-store package was created from the 213 canonical Yale IIIF JPEG objects and placed in a private Google Drive folder under the alias:

```text
Voynich Source Store/SOURCE-FREEZE-0001/chunks-v1
```

The package contains 16 independently checksummed ZIP objects and one small freeze-evidence object. Image binaries are not present in Git history.

## Build evidence

- Source workflow run: `28719916670`
- Workflow head: `be6d43b0cc1011a6b676a2b4835872452fff8cbe`
- Expected assets: `213`
- Stored objects produced: `213`
- Uncompressed image bytes: `560,960,374`
- External ZIP objects: `16`
- External ZIP bytes: `559,130,377`
- Source manifest SHA-256: `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23`

## Post-upload verification

Every external ZIP object was downloaded from Google Drive after upload. Its SHA-256 was compared with the digest of the corresponding GitHub Actions artifact. All 16 matched.

The downloaded ZIP files were then unpacked. Every included compressed shard passed its internal SHA-256 check. The 16 shards reconstructed a content-addressed store containing exactly 213 files.

Every reconstructed image was reopened and checked against its JSONL record:

- stored path exists;
- byte count matches;
- SHA-256 matches;
- status is `verified`;
- source-manifest hash matches the canonical Yale manifest;
- no duplicate asset key is present.

Result: **213 verified objects, zero mismatches**.

## Public and private metadata boundary

The repository records archive names, sizes, SHA-256 values, storage class and folder alias. It does not contain provider credentials or access-control material. Authorized storage access is managed outside Git.

## Preservation status

The Google Drive package is the durable primary project copy. The replication protocol requires a second independently administered durable copy for long-term preservation. Expiring GitHub Actions artifacts are not counted as that replica.

## Conclusion

The byte-retention acceptance criterion for `SOURCE-FREEZE-0001` is satisfied: the exact 213-object source store is durably retained, reconstructable from documented archives and independently revalidated after transfer.
