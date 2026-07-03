"""Derive explicit asset-to-side relations from institutional labels.

This module parses only folio-side tokens written by the institution, such as
``70v (part)`` or ``85v and 86r (foldout)``. It does not infer missing leaves,
reading order, physical adjacency or manuscript structure from sequence position.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

FOLIO_TOKEN = re.compile(r"(?P<number>\d+)(?P<face>[rv])(?P<part>\s*\(part\))?")


@dataclass(frozen=True)
class AssetSideRelation:
    child_oid: str
    sequence_index: int
    institutional_label: str
    relation_index: int
    side_id: str
    folio_number: int
    face: str
    coverage: str
    parse_status: str
    rule_id: str


@dataclass(frozen=True)
class CompositeCandidate:
    candidate_id: str
    child_oid: str
    sequence_index: int
    institutional_label: str
    candidate_type: str
    side_ids: str
    relation_count: int
    basis: str
    status: str


def parse_explicit_side_tokens(
    *, child_oid: str, sequence_index: int, institutional_label: str
) -> list[AssetSideRelation]:
    """Return only side identifiers explicitly present in a Yale label."""
    relations: list[AssetSideRelation] = []
    for relation_index, match in enumerate(FOLIO_TOKEN.finditer(institutional_label), start=1):
        number = int(match.group("number"))
        face = match.group("face")
        coverage = "part" if match.group("part") else "full_or_unspecified"
        relations.append(
            AssetSideRelation(
                child_oid=child_oid,
                sequence_index=sequence_index,
                institutional_label=institutional_label,
                relation_index=relation_index,
                side_id=f"{number}{face}",
                folio_number=number,
                face=face,
                coverage=coverage,
                parse_status="explicit_label_token",
                rule_id="LABEL-FOLIO-TOKEN-V1",
            )
        )
    return relations


def classify_composite_candidate(
    *, child_oid: str, sequence_index: int, institutional_label: str, relations: list[AssetSideRelation]
) -> CompositeCandidate | None:
    """Flag assets whose labels explicitly indicate parts, multiple sides or foldouts."""
    lower = institutional_label.lower()
    has_part = any(relation.coverage == "part" for relation in relations)
    has_multiple = len(relations) > 1
    mentions_foldout = "foldout" in lower
    if not (has_part or has_multiple or mentions_foldout):
        return None

    if mentions_foldout:
        candidate_type = "explicit_foldout_label"
        basis = "institutional label contains 'foldout'"
    elif has_multiple and has_part:
        candidate_type = "multi_side_with_parts"
        basis = "institutional label contains multiple explicit sides and at least one part marker"
    elif has_multiple:
        candidate_type = "multi_side_asset"
        basis = "institutional label contains multiple explicit sides"
    else:
        candidate_type = "fragmented_side_asset"
        basis = "institutional label contains an explicit part marker"

    return CompositeCandidate(
        candidate_id=f"COMPOSITE-{child_oid}",
        child_oid=child_oid,
        sequence_index=sequence_index,
        institutional_label=institutional_label,
        candidate_type=candidate_type,
        side_ids=";".join(relation.side_id for relation in relations),
        relation_count=len(relations),
        basis=basis,
        status="label_derived_candidate",
    )


def read_assets_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_relation_tables(assets_path: Path, output_dir: Path) -> dict[str, int]:
    assets = read_assets_jsonl(assets_path)
    relations: list[AssetSideRelation] = []
    composites: list[CompositeCandidate] = []
    non_folio_assets: list[dict[str, Any]] = []

    for asset in assets:
        child_oid = str(asset.get("child_oid") or "")
        sequence_index = int(asset["sequence_index"])
        label = str(asset.get("label") or "")
        parsed = parse_explicit_side_tokens(
            child_oid=child_oid,
            sequence_index=sequence_index,
            institutional_label=label,
        )
        relations.extend(parsed)

        composite = classify_composite_candidate(
            child_oid=child_oid,
            sequence_index=sequence_index,
            institutional_label=label,
            relations=parsed,
        )
        if composite is not None:
            composites.append(composite)

        if not parsed:
            non_folio_assets.append(
                {
                    "child_oid": child_oid,
                    "sequence_index": sequence_index,
                    "institutional_label": label,
                    "classification": "support_or_unparsed_asset",
                    "status": "explicit_label_contains_no_folio_side_token",
                }
            )

    write_csv(
        output_dir / "asset-side-relations.csv",
        list(AssetSideRelation.__dataclass_fields__),
        (asdict(row) for row in relations),
    )
    write_csv(
        output_dir / "foldouts.csv",
        list(CompositeCandidate.__dataclass_fields__),
        (asdict(row) for row in composites),
    )
    write_csv(
        output_dir / "non-folio-assets.csv",
        ["child_oid", "sequence_index", "institutional_label", "classification", "status"],
        non_folio_assets,
    )

    return {
        "asset_count": len(assets),
        "relation_count": len(relations),
        "composite_candidate_count": len(composites),
        "non_folio_asset_count": len(non_folio_assets),
    }
