"""Build a canonical page manifest without inferring reading order or geometry.

The manifest joins Yale asset metadata, frozen byte records and side tokens that
are explicitly present in institutional labels. A photographic asset may relate
to zero, one or several physical sides. No asset sequence is promoted to a
physical or reading-order claim.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


class PageManifestError(RuntimeError):
    """Raised when source tables cannot form a complete deterministic manifest."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PageManifestError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def unique_index(rows: Iterable[dict[str, Any]], key: str, source: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            raise PageManifestError(f"{source}: missing {key}")
        if value in result:
            raise PageManifestError(f"{source}: duplicate {key} {value}")
        result[value] = row
    return result


def load_rights_status(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not value.get("status"):
        raise PageManifestError(f"{path}: missing rights status")
    return str(value["status"])


def build_records(
    *,
    assets: list[dict[str, Any]],
    byte_records: list[dict[str, Any]],
    side_relations: list[dict[str, str]],
    composite_candidates: list[dict[str, str]],
    rights_record_path: str,
    rights_status: str,
) -> list[dict[str, Any]]:
    assets_by_oid = unique_index(assets, "child_oid", "asset inventory")
    bytes_by_oid = unique_index(byte_records, "child_oid", "byte inventory")
    composites_by_oid = unique_index(
        composite_candidates, "child_oid", "composite-candidate inventory"
    )

    asset_oids = set(assets_by_oid)
    byte_oids = set(bytes_by_oid)
    if asset_oids != byte_oids:
        missing = sorted(asset_oids - byte_oids)
        unexpected = sorted(byte_oids - asset_oids)
        raise PageManifestError(
            f"asset/byte key mismatch; missing={missing[:10]}, unexpected={unexpected[:10]}"
        )

    relations_by_oid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for relation in side_relations:
        child_oid = str(relation.get("child_oid") or "")
        if child_oid not in assets_by_oid:
            raise PageManifestError(f"relation refers to unknown child_oid {child_oid}")
        relations_by_oid[child_oid].append(relation)

    for relations in relations_by_oid.values():
        relations.sort(key=lambda row: int(row["relation_index"]))

    records: list[dict[str, Any]] = []
    for asset in sorted(assets, key=lambda row: int(row["sequence_index"])):
        child_oid = str(asset["child_oid"])
        byte_record = bytes_by_oid[child_oid]
        relations = relations_by_oid.get(child_oid, [])
        composite = composites_by_oid.get(child_oid)

        if byte_record.get("status") != "verified":
            raise PageManifestError(f"byte record for {child_oid} is not verified")
        digest = str(byte_record.get("sha256") or "")
        if len(digest) != 64:
            raise PageManifestError(f"byte record for {child_oid} has invalid SHA-256")
        if int(byte_record.get("byte_count") or 0) <= 0:
            raise PageManifestError(f"byte record for {child_oid} has invalid byte count")
        if not byte_record.get("stored_path"):
            raise PageManifestError(f"byte record for {child_oid} has no stored path")

        normalized_relations = [
            {
                "side_id": str(row["side_id"]),
                "relation_index": int(row["relation_index"]),
                "coverage": str(row["coverage"]),
                "basis": str(row["parse_status"]),
            }
            for row in relations
        ]
        parent_ids = [row["side_id"] for row in normalized_relations]
        is_support = not normalized_relations
        candidate_type = str(composite["candidate_type"]) if composite else None

        if is_support:
            record_type = "support_view"
            composition_status = "support_view"
            folio_id = None
        else:
            record_type = "manuscript_image"
            composition_status = "composite_candidate" if composite else "single_side_or_unspecified"
            folio_id = (
                normalized_relations[0]["side_id"]
                if len(normalized_relations) == 1
                and normalized_relations[0]["coverage"] == "full_or_unspecified"
                else None
            )

        records.append(
            {
                "schema_version": "0.2.0",
                "sequence_index": int(asset["sequence_index"]),
                "record_type": record_type,
                "institutional_id": child_oid,
                "canvas_id": str(asset["canvas_id"]),
                "institutional_label": str(asset.get("label") or ""),
                "photographic_panel_id": f"YDC-PANEL-{child_oid}",
                "folio_id": folio_id,
                "physical_parent_ids": parent_ids,
                "side_relations": normalized_relations,
                "composition_status": composition_status,
                "candidate_type": candidate_type,
                "reading_order": None,
                "source_url": str(byte_record.get("source_url") or asset.get("image_url") or ""),
                "source_sha256": digest,
                "byte_count": int(byte_record["byte_count"]),
                "width_px": int(asset["width_px"]),
                "height_px": int(asset["height_px"]),
                "stored_path": str(byte_record["stored_path"]),
                "rights_record": rights_record_path,
                "rights_status": rights_status,
                "retrieved_at": byte_record.get("acquired_at"),
                "notes": (
                    "Institutional label retained verbatim; physical parents are explicit label tokens; "
                    "reading order is not asserted."
                ),
            }
        )

    if len(records) != len(assets):
        raise PageManifestError("manifest record count differs from asset count")
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def write_csv_summary(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "sequence_index",
        "institutional_label",
        "record_type",
        "folio_id",
        "physical_parent_ids",
        "institutional_id",
        "canvas_id",
        "width_px",
        "height_px",
        "byte_count",
        "source_sha256",
        "source_url",
        "stored_path",
        "composition_status",
        "candidate_type",
        "reading_order",
        "rights_status",
        "retrieved_at",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **{key: record.get(key) for key in fields},
                    "physical_parent_ids": ";".join(record["physical_parent_ids"]),
                    "reading_order": "",
                }
            )


def build_page_manifest(
    *,
    assets_path: Path,
    byte_records_path: Path,
    relations_path: Path,
    composites_path: Path,
    rights_path: Path,
    jsonl_output: Path,
    csv_output: Path,
) -> dict[str, int]:
    records = build_records(
        assets=read_jsonl(assets_path),
        byte_records=read_jsonl(byte_records_path),
        side_relations=read_csv(relations_path),
        composite_candidates=read_csv(composites_path),
        rights_record_path=rights_path.as_posix(),
        rights_status=load_rights_status(rights_path),
    )
    write_jsonl(jsonl_output, records)
    write_csv_summary(csv_output, records)
    return {
        "asset_records": len(records),
        "manuscript_images": sum(row["record_type"] == "manuscript_image" for row in records),
        "support_views": sum(row["record_type"] == "support_view" for row in records),
        "composite_candidates": sum(
            row["composition_status"] == "composite_candidate" for row in records
        ),
        "single_folio_ids": sum(row["folio_id"] is not None for row in records),
    }
