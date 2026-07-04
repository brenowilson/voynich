"""Stream institutional image bytes into content-addressed storage."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .yale import USER_AGENT

CHUNK_SIZE = 1024 * 1024


class ByteAcquisitionError(RuntimeError):
    """Raised when an image byte stream cannot be acquired or verified."""


@dataclass(frozen=True)
class ByteRecord:
    source_manifest_sha256: str
    sequence_index: int
    child_oid: str
    canvas_id: str
    institutional_label: str
    representation: str
    source_url: str
    resolved_url: str | None
    sha256: str | None
    byte_count: int
    media_type: str | None
    etag: str | None
    last_modified: str | None
    acquired_at: str
    status: str
    error: str | None
    stored_path: str | None


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def select_shard(rows: list[dict[str, Any]], shard_index: int, shard_count: int) -> list[dict[str, Any]]:
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if not 0 <= shard_index < shard_count:
        raise ValueError("shard_index must satisfy 0 <= shard_index < shard_count")
    return [row for row in rows if (int(row["sequence_index"]) - 1) % shard_count == shard_index]


def extension_for(media_type: str | None, source_url: str) -> str:
    media = (media_type or "").split(";", 1)[0].strip().lower()
    if media in {"image/jpeg", "image/jpg"}:
        return "jpg"
    if media in {"image/tiff", "image/tif"}:
        return "tif"
    suffix = Path(urllib.request.url2pathname(source_url.split("?", 1)[0])).suffix.lower().lstrip(".")
    return suffix if suffix in {"jpg", "jpeg", "tif", "tiff", "png", "webp"} else "bin"


def hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
            count += len(chunk)
    return digest.hexdigest(), count


def object_path(store_root: Path, digest: str, extension: str) -> Path:
    return store_root / "sha256" / digest[:2] / f"{digest}.{extension}"


def stream_to_temp(
    source_url: str,
    temp_path: Path,
    timeout: float,
) -> tuple[str, int, dict[str, str], str]:
    digest = hashlib.sha256()
    count = 0
    request = urllib.request.Request(
        source_url,
        headers={"User-Agent": USER_AGENT, "Accept": "image/*,*/*;q=0.1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response, temp_path.open("wb") as output:
        headers = {key.lower(): value for key, value in response.headers.items()}
        resolved_url = response.geturl()
        while chunk := response.read(CHUNK_SIZE):
            output.write(chunk)
            digest.update(chunk)
            count += len(chunk)
        output.flush()
        os.fsync(output.fileno())
    if count == 0:
        raise ByteAcquisitionError(f"zero-byte response from {source_url}")
    return digest.hexdigest(), count, headers, resolved_url


def acquire_one(
    asset: dict[str, Any],
    *,
    source_manifest_sha256: str,
    store_root: Path,
    representation: str = "iiif-full-jpeg",
    retain_bytes: bool = True,
    timeout: float = 180.0,
    retries: int = 3,
) -> ByteRecord:
    source_url = str(asset.get("image_url") or "")
    sequence_index = int(asset["sequence_index"])
    child_oid = str(asset.get("child_oid") or "")
    canvas_id = str(asset.get("canvas_id") or "")
    label = str(asset.get("label") or "")
    if not source_url:
        return ByteRecord(
            source_manifest_sha256=source_manifest_sha256,
            sequence_index=sequence_index,
            child_oid=child_oid,
            canvas_id=canvas_id,
            institutional_label=label,
            representation=representation,
            source_url="",
            resolved_url=None,
            sha256=None,
            byte_count=0,
            media_type=None,
            etag=None,
            last_modified=None,
            acquired_at=utc_now(),
            status="failed",
            error="missing image_url in asset inventory",
            stored_path=None,
        )

    store_root.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(retries):
        fd, temp_name = tempfile.mkstemp(prefix=f"{child_oid or sequence_index}-", suffix=".part", dir=store_root)
        os.close(fd)
        temp_path = Path(temp_name)
        try:
            digest, byte_count, headers, resolved_url = stream_to_temp(source_url, temp_path, timeout)
            media_type = headers.get("content-type")
            extension = extension_for(media_type, source_url)
            destination = object_path(store_root, digest, extension)
            stored_path: str | None = None
            if retain_bytes:
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    existing_digest, existing_size = hash_file(destination)
                    if existing_digest != digest or existing_size != byte_count:
                        raise ByteAcquisitionError(f"content-addressed object failed verification: {destination}")
                    temp_path.unlink()
                else:
                    shutil.move(str(temp_path), destination)
                stored_path = destination.relative_to(store_root).as_posix()
            else:
                temp_path.unlink()
            return ByteRecord(
                source_manifest_sha256=source_manifest_sha256,
                sequence_index=sequence_index,
                child_oid=child_oid,
                canvas_id=canvas_id,
                institutional_label=label,
                representation=representation,
                source_url=source_url,
                resolved_url=resolved_url,
                sha256=digest,
                byte_count=byte_count,
                media_type=media_type,
                etag=headers.get("etag"),
                last_modified=headers.get("last-modified"),
                acquired_at=utc_now(),
                status="verified",
                error=None,
                stored_path=stored_path,
            )
        except (urllib.error.URLError, TimeoutError, OSError, ByteAcquisitionError) as exc:
            last_error = exc
            temp_path.unlink(missing_ok=True)
            if attempt + 1 < retries:
                time.sleep(2**attempt)

    return ByteRecord(
        source_manifest_sha256=source_manifest_sha256,
        sequence_index=sequence_index,
        child_oid=child_oid,
        canvas_id=canvas_id,
        institutional_label=label,
        representation=representation,
        source_url=source_url,
        resolved_url=None,
        sha256=None,
        byte_count=0,
        media_type=None,
        etag=None,
        last_modified=None,
        acquired_at=utc_now(),
        status="failed",
        error=str(last_error),
        stored_path=None,
    )


def write_records(path: Path, records: Iterable[ByteRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def acquire_assets(
    *,
    assets_path: Path,
    output_path: Path,
    store_root: Path,
    source_manifest_sha256: str,
    shard_index: int = 0,
    shard_count: int = 1,
    retain_bytes: bool = True,
    limit: int | None = None,
) -> dict[str, int]:
    assets = select_shard(load_jsonl(assets_path), shard_index, shard_count)
    if limit is not None:
        assets = assets[:limit]
    records = [
        acquire_one(
            asset,
            source_manifest_sha256=source_manifest_sha256,
            store_root=store_root,
            retain_bytes=retain_bytes,
        )
        for asset in assets
    ]
    write_records(output_path, records)
    verified = sum(record.status == "verified" for record in records)
    failed = len(records) - verified
    return {"selected": len(records), "verified": verified, "failed": failed}
