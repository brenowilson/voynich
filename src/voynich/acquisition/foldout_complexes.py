"""Build quire-level foldout complexes from institutional evidence.

A foldout complex is an evidence-bounded set of digital panels associated with a
quire whose folding-leaf profile is stated by Yale. It is not a reconstructed
reading order and, where the catalog lists more than one folding leaf in a quire,
it does not silently assign each digital panel to a specific physical leaf.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


class FoldoutComplexError(RuntimeError):
    """Raised when codicological evidence and canonical page records disagree."""


EXTENTS = ("double", "triple", "quadruple", "sextuple")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FoldoutComplexError(f"{path}: expected a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise FoldoutComplexError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def side_number(side_id: str) -> int:
    if len(side_id) < 2 or side_id[-1] not in {"r", "v"}:
        raise FoldoutComplexError(f"invalid side identifier: {side_id}")
    try:
        return int(side_id[:-1])
    except ValueError as exc:
        raise FoldoutComplexError(f"invalid side identifier: {side_id}") from exc


def validate_codiaology_profile(config: dict[str, Any]) -> None:
    totals = config.get("folding_leaf_totals")
    complexes = config.get("complexes")
    if not isinstance(totals, dict) or not isinstance(complexes, list):
        raise FoldoutComplexError("codicology config requires totals and complexes")

    calculated = Counter({extent: 0 for extent in EXTENTS})
    ids: set[str] = set()
    quires: set[str] = set()
    ranges: list[tuple[int, int, str]] = []

    for complex_record in complexes:
        if not isinstance(complex_record, dict):
            raise FoldoutComplexError("complex record must be an object")
        complex_id = str(complex_record.get("complex_id") or "")
        quire_id = str(complex_record.get("quire_id") or "")
        if not complex_id or complex_id in ids:
            raise FoldoutComplexError(f"missing or duplicate complex_id: {complex_id}")
        if not quire_id or quire_id in quires:
            raise FoldoutComplexError(f"missing or duplicate quire_id: {quire_id}")
        ids.add(complex_id)
        quires.add(quire_id)

        lower = int(complex_record["folio_min"])
        upper = int(complex_record["folio_max"])
        if lower > upper:
            raise FoldoutComplexError(f"invalid folio range for {complex_id}")
        ranges.append((lower, upper, complex_id))

        profile = complex_record.get("folding_leaf_profile")
        if not isinstance(profile, dict):
            raise FoldoutComplexError(f"missing folding-leaf profile for {complex_id}")
        for extent in EXTENTS:
            count = int(profile.get(extent, 0))
            if count < 0:
                raise FoldoutComplexError(f"negative {extent} count for {complex_id}")
            calculated[extent] += count

        if complex_record.get("reading_order") is not None:
            raise FoldoutComplexError(f"reading order must remain null for {complex_id}")

    for index, (lower, upper, complex_id) in enumerate(sorted(ranges)):
        for other_lower, other_upper, other_id in sorted(ranges)[index + 1 :]:
            if other_lower > upper:
                break
            if lower <= other_upper and other_lower <= upper:
                raise FoldoutComplexError(
                    f"overlapping folio ranges: {complex_id} and {other_id}"
                )

    expected = Counter({extent: int(totals.get(extent, 0)) for extent in EXTENTS})
    if calculated != expected:
        raise FoldoutComplexError(
            f"quire profiles {dict(calculated)} do not match totals {dict(expected)}"
        )


def page_matches_range(page: dict[str, Any], lower: int, upper: int) -> bool:
    parents = page.get("physical_parent_ids")
    if not isinstance(parents, list):
        raise FoldoutComplexError("page record lacks physical_parent_ids array")
    return any(lower <= side_number(str(side_id)) <= upper for side_id in parents)


def normalize_profile(value: dict[str, Any]) -> dict[str, int]:
    return {extent: int(value.get(extent, 0)) for extent in EXTENTS}


def build_complexes(
    *, pages: list[dict[str, Any]], config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    validate_codiaology_profile(config)

    page_ids: set[str] = set()
    for page in pages:
        panel_id = str(page.get("photographic_panel_id") or "")
        if not panel_id or panel_id in page_ids:
            raise FoldoutComplexError(f"missing or duplicate photographic panel: {panel_id}")
        page_ids.add(panel_id)

    complexes: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    covered_candidate_panels: set[str] = set()

    for source in config["complexes"]:
        lower = int(source["folio_min"])
        upper = int(source["folio_max"])
        selected = [page for page in pages if page_matches_range(page, lower, upper)]
        selected.sort(key=lambda page: int(page["sequence_index"]))
        if not selected:
            raise FoldoutComplexError(f"no panels found for {source['complex_id']}")
        if any(page.get("record_type") != "manuscript_image" for page in selected):
            raise FoldoutComplexError(f"support view entered {source['complex_id']}")

        side_ids = sorted(
            {
                str(side_id)
                for page in selected
                for side_id in page.get("physical_parent_ids", [])
            },
            key=lambda value: (side_number(value), value[-1]),
        )
        panel_ids = [str(page["photographic_panel_id"]) for page in selected]
        institutional_ids = [str(page["institutional_id"]) for page in selected]
        candidate_panels = [
            str(page["photographic_panel_id"])
            for page in selected
            if page.get("composition_status") == "composite_candidate"
        ]
        covered_candidate_panels.update(candidate_panels)

        complex_record = {
            "schema_version": "0.1.0",
            "complex_id": str(source["complex_id"]),
            "quire_id": str(source["quire_id"]),
            "folio_range": {"minimum": lower, "maximum": upper},
            "folding_leaf_profile": normalize_profile(source["folding_leaf_profile"]),
            "panel_ids": panel_ids,
            "institutional_ids": institutional_ids,
            "side_ids": side_ids,
            "panel_count": len(panel_ids),
            "label_candidate_panel_count": len(candidate_panels),
            "assignment_status": str(source["assignment_status"]),
            "geometry_status": str(source["geometry_status"]),
            "reading_order": None,
            "evidence_source": str(config["source_url"]),
            "evidence_scope": str(config["evidence_scope"]),
            "evidence_note": str(source["evidence_note"]),
        }
        complexes.append(complex_record)

        for page in selected:
            relation_side_ids = [str(value) for value in page["physical_parent_ids"]]
            coverages = [
                str(relation["coverage"])
                for relation in page.get("side_relations", [])
            ]
            relations.append(
                {
                    "complex_id": complex_record["complex_id"],
                    "quire_id": complex_record["quire_id"],
                    "photographic_panel_id": str(page["photographic_panel_id"]),
                    "institutional_id": str(page["institutional_id"]),
                    "sequence_index": int(page["sequence_index"]),
                    "institutional_label": str(page["institutional_label"]),
                    "side_ids": ";".join(relation_side_ids),
                    "coverage_modes": ";".join(coverages),
                    "label_candidate": page.get("composition_status") == "composite_candidate",
                    "relation_basis": "institutional_quire_profile_and_explicit_side_tokens",
                    "physical_leaf_id": "",
                    "physical_leaf_assignment_status": str(source["assignment_status"]),
                    "geometry_status": str(source["geometry_status"]),
                    "reading_order": "",
                }
            )

    all_candidate_panels = {
        str(page["photographic_panel_id"])
        for page in pages
        if page.get("composition_status") == "composite_candidate"
    }
    missing_candidates = sorted(all_candidate_panels - covered_candidate_panels)
    if missing_candidates:
        raise FoldoutComplexError(
            f"label-derived candidate panels outside codicological complexes: {missing_candidates}"
        )

    panel_relation_counts = Counter(row["photographic_panel_id"] for row in relations)
    duplicated = sorted(panel for panel, count in panel_relation_counts.items() if count != 1)
    if duplicated:
        raise FoldoutComplexError(f"panels assigned to multiple complexes: {duplicated}")

    summary = {
        "complex_count": len(complexes),
        "panel_relation_count": len(relations),
        "label_candidate_panel_count": len(all_candidate_panels),
        "folding_leaf_count": sum(
            sum(record["folding_leaf_profile"].values()) for record in complexes
        ),
    }
    return complexes, relations, summary


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def write_relations_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "complex_id",
        "quire_id",
        "photographic_panel_id",
        "institutional_id",
        "sequence_index",
        "institutional_label",
        "side_ids",
        "coverage_modes",
        "label_candidate",
        "relation_basis",
        "physical_leaf_id",
        "physical_leaf_assignment_status",
        "geometry_status",
        "reading_order",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_foldout_complex_files(
    *,
    pages_path: Path,
    codicology_path: Path,
    complexes_output: Path,
    relations_output: Path,
) -> dict[str, int]:
    complexes, relations, summary = build_complexes(
        pages=read_jsonl(pages_path),
        config=read_json(codicology_path),
    )
    write_jsonl(complexes_output, complexes)
    write_relations_csv(relations_output, relations)
    return summary
