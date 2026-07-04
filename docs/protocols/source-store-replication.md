# Source Store Restoration and Replication Protocol

## Purpose

Preserve the exact 213 Yale IIIF JPEG byte streams used by `SOURCE-FREEZE-0001` without committing image binaries to Git.

## Canonical external package

The durable package consists of 16 ZIP objects named `drive-source-chunk-0.zip` through `drive-source-chunk-15.zip`.

Each ZIP contains one compressed content-addressed store shard, its SHA-256 checksum, and one JSONL byte-record file. Together the shards reconstruct:

```text
sha256/<first-two-hex>/<full-sha256>.jpg
```

Archive names, byte counts and SHA-256 values are recorded in `sources/primary/storage/SOURCE-FREEZE-0001-storage.json`. Credentials and private access controls are never committed.

## Restoration procedure

1. Obtain all 16 ZIP objects from the authorized external store.
2. Verify each ZIP against the repository storage inventory.
3. Extract every ZIP into a separate temporary directory.
4. Verify every included compressed shard using its checksum file.
5. Extract all shards into the same store root.
6. Collect all 16 JSONL record files.
7. Run `scripts/build_source_freeze.py` with the canonical Yale asset inventory, the 16 record files, the Yale manifest SHA-256 and the restored store root.

A valid restoration reports 213 expected assets, 213 verified records, 213 stored objects verified and status `frozen`.

## Invalid-store conditions

The store is invalid when an outer ZIP is missing or has a different SHA-256, an inner checksum fails, a stored image is missing or differs from its byte record, a record names a different source-manifest hash, or duplicate or unexpected asset keys are present.

## Replication policy

The Google Drive folder is the current durable primary copy. Yale remains the authoritative upstream source, but its public endpoints are not a backup controlled by this project.

A second independently administered durable copy must be created for long-term preservation. Acceptable replicas include an institutional research drive, encrypted object storage or an offline archival disk. A replica is accepted only after all 16 outer checksums and the full 213-object restoration validation pass.

The storage inventory is reviewed after provider migration, after any object replacement, before a new corpus freeze derived from this source, and at least annually while the project remains active.

GitHub Actions artifacts are temporary reproducibility evidence. They expire and do not count as a durable replica.
