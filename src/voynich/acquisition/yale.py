"""Acquire and normalize Yale Digital Collections IIIF metadata.

The module preserves the institutional manifest verbatim and emits a small,
deterministic inventory. It does not infer foliation, reading order, glyphs or
linguistic units.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

DEFAULT_OID = "2002046"
DEFAULT_CATALOG_URL = f"https://collections.library.yale.edu/catalog/{DEFAULT_OID}"
DEFAULT_MANIFEST_URL = (
    f"https://collections.library.yale.edu/manifests/{DEFAULT_OID}.json"
)
USER_AGENT = "voynich-independent-corpus/0.0.1 (+https://github.com/brenowilson/voynich)"


class AcquisitionError(RuntimeError):
    """Raised when an institutional source cannot be acquired or validated."""


@dataclass(frozen=True)
class AssetRecord:
    sequence_index: int
    canvas_id: str
    label: str
    child_oid: str | None
    width_px: int | None
    height_px: int | None
    image_service_id: str | None
    image_info_url: str | None
    image_url: str | None
    catalog_child_url: str | None
    source_manifest_url: str


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout: float = 60.0, retries: int = 3) -> tuple[bytes, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, application/ld+json;q=0.9, */*;q=0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                return response.read(), headers
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise AcquisitionError(f"failed to fetch {url}: {last_error}") from last_error


def fetch_json(url: str, timeout: float = 60.0, retries: int = 3) -> tuple[Any, bytes, dict[str, str]]:
    raw, headers = fetch_bytes(url, timeout=timeout, retries=retries)
    try:
        return json.loads(raw), raw, headers
    except json.JSONDecodeError as exc:
        snippet = raw[:160].decode("utf-8", errors="replace")
        raise AcquisitionError(f"non-JSON response from {url}: {snippet!r}") from exc


def text_value(value: Any) -> str:
    """Extract a stable human-readable string from IIIF v2/v3 label forms."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " | ".join(filter(None, (text_value(item) for item in value)))
    if isinstance(value, dict):
        preferred = value.get("none") or value.get("en")
        if preferred is not None:
            return text_value(preferred)
        parts: list[str] = []
        for key in sorted(value):
            rendered = text_value(value[key])
            if rendered:
                parts.append(rendered)
        return " | ".join(parts)
    return str(value)


def service_id(service: Any) -> str | None:
    if isinstance(service, list):
        for item in service:
            result = service_id(item)
            if result:
                return result
        return None
    if isinstance(service, dict):
        value = service.get("id") or service.get("@id")
        return str(value).rstrip("/") if value else None
    return None


def child_oid_from_service(service: str | None) -> str | None:
    if not service:
        return None
    tail = service.rstrip("/").split("/")[-1]
    return tail if tail.isdigit() else None


def image_body_from_canvas(canvas: dict[str, Any]) -> dict[str, Any]:
    # IIIF Presentation 3
    try:
        body = canvas["items"][0]["items"][0]["body"]
        if isinstance(body, dict):
            return body
    except (KeyError, IndexError, TypeError):
        pass

    # IIIF Presentation 2
    images = canvas.get("images") or []
    if images and isinstance(images[0], dict):
        resource = images[0].get("resource")
        if isinstance(resource, dict):
            return resource
    return {}


def manifest_canvases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    items = manifest.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    sequences = manifest.get("sequences") or []
    if sequences and isinstance(sequences[0], dict):
        canvases = sequences[0].get("canvases") or []
        return [item for item in canvases if isinstance(item, dict)]
    raise AcquisitionError("manifest contains no IIIF v2 sequences or IIIF v3 items")


def normalize_manifest(manifest: dict[str, Any], manifest_url: str) -> list[AssetRecord]:
    records: list[AssetRecord] = []
    for index, canvas in enumerate(manifest_canvases(manifest), start=1):
        body = image_body_from_canvas(canvas)
        svc = service_id(body.get("service"))
        child_oid = child_oid_from_service(svc)
        image_url = body.get("id") or body.get("@id")
        canvas_id = canvas.get("id") or canvas.get("@id") or f"canvas-{index}"
        width = canvas.get("width") or body.get("width")
        height = canvas.get("height") or body.get("height")
        records.append(
            AssetRecord(
                sequence_index=index,
                canvas_id=str(canvas_id),
                label=text_value(canvas.get("label")),
                child_oid=child_oid,
                width_px=int(width) if width is not None else None,
                height_px=int(height) if height is not None else None,
                image_service_id=svc,
                image_info_url=f"{svc}/info.json" if svc else None,
                image_url=str(image_url) if image_url else None,
                catalog_child_url=(
                    f"{DEFAULT_CATALOG_URL}?child_oid={child_oid}" if child_oid else None
                ),
                source_manifest_url=manifest_url,
            )
        )
    if not records:
        raise AcquisitionError("manifest normalized to zero assets")
    return records


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def write_pages_csv(path: Path, records: list[AssetRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "sequence_index",
        "institutional_label",
        "folio_id",
        "child_oid",
        "canvas_id",
        "width_px",
        "height_px",
        "image_service_id",
        "image_info_url",
        "image_url",
        "catalog_child_url",
        "folio_status",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "sequence_index": record.sequence_index,
                    "institutional_label": record.label,
                    "folio_id": "",
                    "child_oid": record.child_oid or "",
                    "canvas_id": record.canvas_id,
                    "width_px": record.width_px or "",
                    "height_px": record.height_px or "",
                    "image_service_id": record.image_service_id or "",
                    "image_info_url": record.image_info_url or "",
                    "image_url": record.image_url or "",
                    "catalog_child_url": record.catalog_child_url or "",
                    "folio_status": "unresolved",
                    "notes": "Institutional label retained verbatim; folio mapping not inferred.",
                }
            )


def acquire(manifest_url: str, output_root: Path) -> dict[str, Any]:
    manifest, raw_manifest, headers = fetch_json(manifest_url)
    if not isinstance(manifest, dict):
        raise AcquisitionError("IIIF manifest root is not a JSON object")
    records = normalize_manifest(manifest, manifest_url)

    yale_dir = output_root / "sources/primary/yale"
    checksums_dir = output_root / "sources/primary/checksums"
    manifests_dir = output_root / "sources/primary/manifests"

    yale_dir.mkdir(parents=True, exist_ok=True)
    checksums_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    raw_path = yale_dir / "manifest.json"
    raw_path.write_bytes(raw_manifest)
    manifest_sha = sha256_bytes(raw_manifest)

    inventory_rows = [asdict(record) for record in records]
    write_jsonl(yale_dir / "assets.jsonl", inventory_rows)
    write_pages_csv(manifests_dir / "pages.csv", records)

    collection = {
        "schema_version": "0.1.0",
        "institution": "Yale University Library / Beinecke Rare Book and Manuscript Library",
        "shelfmark": "Beinecke MS 408",
        "parent_oid": DEFAULT_OID,
        "catalog_url": DEFAULT_CATALOG_URL,
        "manifest_url": manifest_url,
        "manifest_sha256": manifest_sha,
        "manifest_content_type": headers.get("content-type"),
        "retrieved_at": utc_now(),
        "asset_count": len(records),
        "manifest_id": manifest.get("id") or manifest.get("@id"),
        "manifest_label": text_value(manifest.get("label")),
        "rights": manifest.get("rights") or manifest.get("license"),
        "provider": manifest.get("provider") or manifest.get("attribution"),
        "method": "IIIF Presentation manifest normalization; no foliation inference",
    }
    write_json(yale_dir / "collection.json", collection)

    checksum_lines = [f"{manifest_sha}  sources/primary/yale/manifest.json\n"]
    (checksums_dir / "sha256.txt").write_text("".join(checksum_lines), encoding="utf-8")
    return collection
