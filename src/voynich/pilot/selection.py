"""Build the metadata-only candidate pool for PILOT-0001.

The builder uses canonical source metadata only. It does not inspect image content,
external transliterations, conventional section labels, glyph statistics or later
analytical results.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


class PilotSelectionError(RuntimeError):
    """Raised when canonical inputs cannot form a valid pilot candidate pool."""


PILOT_ID = "PILOT-0001"
SELECTION_SEED = "PILOT-0001"
SEQUENCE_BIN_COUNT = 8
ORDINARY_PER_BIN = 2
COMPOSITE_PER_TYPE = 2


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PilotSelectionError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_rank(namespace: str, panel_id: str) -> str:
    payload = f"{SELECTION_SEED}|{namespace}|{panel_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_records_sha256(records: Iterable[dict[str, Any]]) -> str:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def validate_pages(pages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_panel: dict[str, dict[str, Any]] = {}
    for page in pages:
        panel_id = str(page.get("photographic_panel_id") or "")
        if not panel_id:
            raise PilotSelectionError("page record lacks photographic_panel_id")
        if panel_id in by_panel:
            raise PilotSelectionError(f"duplicate photographic panel {panel_id}")
        if page.get("acquisition_status") != "verified":
            raise PilotSelectionError(f"unverified page record {panel_id}")
        digest = str(page.get("source_sha256") or "")
        if len(digest) != 64:
            raise PilotSelectionError(f"invalid source SHA-256 for {panel_id}")
        if int(page.get("width_px") or 0) <= 0 or int(page.get("height_px") or 0) <= 0:
            raise PilotSelectionError(f"invalid source dimensions for {panel_id}")
        if page.get("reading_order") is not None:
            raise PilotSelectionError(f"reading-order claim present for {panel_id}")
        by_panel[panel_id] = page
    return by_panel


def build_sequence_bins(
    manuscript_pages: list[dict[str, Any]], bin_count: int = SEQUENCE_BIN_COUNT
) -> dict[str, int]:
    if not manuscript_pages:
        raise PilotSelectionError("no manuscript-image records available")
    ordered = sorted(
        manuscript_pages,
        key=lambda row: (int(row["sequence_index"]), str(row["photographic_panel_id"])),
    )
    bins: dict[str, int] = {}
    total = len(ordered)
    for index, page in enumerate(ordered):
        bin_index = min(bin_count - 1, (index * bin_count) // total)
        bins[str(page["photographic_panel_id"])] = bin_index + 1
    return bins


def build_candidate_records(
    *,
    pages: list[dict[str, Any]],
    foldout_relations: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    pages_by_panel = validate_pages(pages)
    manuscript_pages = [
        page for page in pages if page.get("record_type") == "manuscript_image"
    ]
    sequence_bins = build_sequence_bins(manuscript_pages)

    foldout_rows_by_panel: dict[str, list[dict[str, str]]] = defaultdict(list)
    foldout_rows_by_complex: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in foldout_relations:
        panel_id = str(row.get("photographic_panel_id") or "")
        complex_id = str(row.get("complex_id") or "")
        if panel_id not in pages_by_panel:
            raise PilotSelectionError(f"foldout relation names unknown panel {panel_id}")
        if not complex_id:
            raise PilotSelectionError(f"foldout relation lacks complex_id for {panel_id}")
        foldout_rows_by_panel[panel_id].append(row)
        foldout_rows_by_complex[complex_id].append(row)

    selected: dict[str, dict[str, set[str]]] = {}

    def mark(panel_id: str, stratum: str, reason: str) -> None:
        if pages_by_panel[panel_id].get("record_type") != "manuscript_image":
            raise PilotSelectionError(f"support view selected: {panel_id}")
        entry = selected.setdefault(
            panel_id,
            {"selection_strata": set(), "selection_reasons": set()},
        )
        entry["selection_strata"].add(stratum)
        entry["selection_reasons"].add(reason)

    # Stratum 1: every panel whose physical folding-leaf assignment is explicit.
    for panel_id, rows in sorted(foldout_rows_by_panel.items()):
        explicit_leaf_ids = sorted(
            {str(row.get("physical_leaf_id") or "") for row in rows if row.get("physical_leaf_id")}
        )
        if explicit_leaf_ids:
            mark(
                panel_id,
                "institutionally_explicit_physical_leaf",
                "Panel is assigned by institutional evidence to physical leaf "
                + ",".join(explicit_leaf_ids),
            )

    # Stratum 2: up to two deterministic representatives per candidate type.
    composite_pages = [
        page
        for page in manuscript_pages
        if page.get("composition_status") == "composite_candidate"
        and page.get("candidate_type")
    ]
    composite_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in composite_pages:
        composite_by_type[str(page["candidate_type"])].append(page)
    for candidate_type in sorted(composite_by_type):
        ranked = sorted(
            composite_by_type[candidate_type],
            key=lambda row: (
                stable_rank(
                    f"composite-type:{candidate_type}",
                    str(row["photographic_panel_id"]),
                ),
                str(row["photographic_panel_id"]),
            ),
        )
        for page in ranked[:COMPOSITE_PER_TYPE]:
            mark(
                str(page["photographic_panel_id"]),
                f"composite_type:{candidate_type}",
                f"Deterministic representative of label-derived candidate type {candidate_type}",
            )

    # Stratum 3: guarantee at least one representative of every foldout complex.
    for complex_id in sorted(foldout_rows_by_complex):
        panel_ids = sorted(
            {str(row["photographic_panel_id"]) for row in foldout_rows_by_complex[complex_id]}
        )
        already_selected = [panel_id for panel_id in panel_ids if panel_id in selected]
        eligible = already_selected or panel_ids
        representative = min(
            eligible,
            key=lambda panel_id: (
                stable_rank(f"foldout-complex:{complex_id}", panel_id),
                panel_id,
            ),
        )
        mark(
            representative,
            f"foldout_complex:{complex_id}",
            f"Deterministic representative of foldout complex {complex_id}",
        )

    # Stratum 4: ordinary, non-foldout, non-composite coverage across sequence bins.
    ordinary_pages = [
        page
        for page in manuscript_pages
        if page.get("composition_status") == "single_side_or_unspecified"
        and str(page["photographic_panel_id"]) not in foldout_rows_by_panel
    ]
    ordinary_by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for page in ordinary_pages:
        ordinary_by_bin[sequence_bins[str(page["photographic_panel_id"])]].append(page)

    for bin_index in range(1, SEQUENCE_BIN_COUNT + 1):
        ranked = sorted(
            ordinary_by_bin.get(bin_index, []),
            key=lambda row: (
                stable_rank(
                    f"ordinary-sequence-bin:{bin_index}",
                    str(row["photographic_panel_id"]),
                ),
                str(row["photographic_panel_id"]),
            ),
        )
        for page in ranked[:ORDINARY_PER_BIN]:
            mark(
                str(page["photographic_panel_id"]),
                f"ordinary_sequence_bin:{bin_index}",
                f"Metadata-only ordinary-page representative of source-sequence bin {bin_index}",
            )

    ordered_panel_ids = sorted(
        selected,
        key=lambda panel_id: (
            int(pages_by_panel[panel_id]["sequence_index"]),
            panel_id,
        ),
    )

    records: list[dict[str, Any]] = []
    for index, panel_id in enumerate(ordered_panel_ids, start=1):
        page = pages_by_panel[panel_id]
        foldout_rows = foldout_rows_by_panel.get(panel_id, [])
        complex_ids = sorted({str(row["complex_id"]) for row in foldout_rows})
        physical_leaf_ids = sorted(
            {str(row.get("physical_leaf_id") or "") for row in foldout_rows if row.get("physical_leaf_id")}
        )
        records.append(
            {
                "schema_version": "0.1.0",
                "pilot_id": PILOT_ID,
                "candidate_id": f"PILOT-0001-CAND-{index:03d}",
                "photographic_panel_id": panel_id,
                "institutional_id": str(page["institutional_id"]),
                "institutional_label": str(page["institutional_label"]),
                "sequence_index": int(page["sequence_index"]),
                "source_sequence_bin": int(sequence_bins[panel_id]),
                "source_url": str(page["source_url"]),
                "source_sha256": str(page["source_sha256"]),
                "byte_count": int(page["byte_count"]),
                "width_px": int(page["width_px"]),
                "height_px": int(page["height_px"]),
                "stored_path": str(page["stored_path"]),
                "physical_parent_ids": [str(value) for value in page["physical_parent_ids"]],
                "composition_status": str(page["composition_status"]),
                "candidate_type": page.get("candidate_type"),
                "foldout_complex_ids": complex_ids,
                "physical_leaf_ids": physical_leaf_ids,
                "selection_strata": sorted(selected[panel_id]["selection_strata"]),
                "selection_reasons": sorted(selected[panel_id]["selection_reasons"]),
                "visual_review_status": "pending",
                "external_transliteration_consulted": False,
            }
        )

    if not records:
        raise PilotSelectionError("candidate selection produced no records")
    if any(record["visual_review_status"] != "pending" for record in records):
        raise PilotSelectionError("metadata stage may not contain visual outcomes")
    if any(record["external_transliteration_consulted"] for record in records):
        raise PilotSelectionError("candidate pool is contaminated by external transliteration")

    summary = {
        "candidate_count": len(records),
        "explicit_leaf_panel_count": sum(
            bool(record["physical_leaf_ids"]) for record in records
        ),
        "composite_candidate_count": sum(
            record["composition_status"] == "composite_candidate" for record in records
        ),
        "foldout_complexes_represented": len(
            {complex_id for record in records for complex_id in record["foldout_complex_ids"]}
        ),
        "sequence_bins_represented": len(
            {record["source_sequence_bin"] for record in records}
        ),
        "ordinary_candidate_count": sum(
            record["composition_status"] == "single_side_or_unspecified"
            and not record["foldout_complex_ids"]
            for record in records
        ),
    }
    return records, summary


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def write_csv_records(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "candidate_id",
        "photographic_panel_id",
        "institutional_id",
        "institutional_label",
        "sequence_index",
        "source_sequence_bin",
        "source_url",
        "source_sha256",
        "byte_count",
        "width_px",
        "height_px",
        "stored_path",
        "physical_parent_ids",
        "composition_status",
        "candidate_type",
        "foldout_complex_ids",
        "physical_leaf_ids",
        "selection_strata",
        "selection_reasons",
        "visual_review_status",
        "external_transliteration_consulted",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **{field: record.get(field) for field in fields},
                    "physical_parent_ids": ";".join(record["physical_parent_ids"]),
                    "foldout_complex_ids": ";".join(record["foldout_complex_ids"]),
                    "physical_leaf_ids": ";".join(record["physical_leaf_ids"]),
                    "selection_strata": ";".join(record["selection_strata"]),
                    "selection_reasons": " | ".join(record["selection_reasons"]),
                    "external_transliteration_consulted": "false",
                }
            )


def build_candidate_freeze(
    *,
    records: list[dict[str, Any]],
    pages_path: Path,
    foldout_relations_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "freeze_id": "PILOT-CANDIDATES-FREEZE-0001",
        "pilot_id": PILOT_ID,
        "status": "frozen",
        "candidate_count": len(records),
        "candidate_set_sha256": canonical_records_sha256(records),
        "source_page_manifest_path": "sources/primary/manifests/pages.jsonl",
        "source_page_manifest_sha256": file_sha256(pages_path),
        "foldout_relations_path": "sources/primary/manifests/foldout-panel-relations.csv",
        "foldout_relations_sha256": file_sha256(foldout_relations_path),
        "selection_protocol_path": "docs/protocols/pilot-selection.md",
        "selection_seed": SELECTION_SEED,
        "visual_outcomes_used": False,
        "external_transliterations_used": False,
    }


def build_candidate_files(
    *,
    pages_path: Path,
    foldout_relations_path: Path,
    jsonl_output: Path,
    csv_output: Path,
    freeze_output: Path,
) -> dict[str, Any]:
    records, summary = build_candidate_records(
        pages=read_jsonl(pages_path),
        foldout_relations=read_csv(foldout_relations_path),
    )
    write_jsonl(jsonl_output, records)
    write_csv_records(csv_output, records)
    freeze = build_candidate_freeze(
        records=records,
        pages_path=pages_path,
        foldout_relations_path=foldout_relations_path,
    )
    freeze_output.parent.mkdir(parents=True, exist_ok=True)
    freeze_output.write_text(
        json.dumps(freeze, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {**summary, "candidate_set_sha256": freeze["candidate_set_sha256"]}
