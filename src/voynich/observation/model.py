"""Build and validate interpretation-neutral observation packages."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Sequence


class ObservationValidationError(RuntimeError):
    """Raised when an observation package violates the canonical protocol."""


FORBIDDEN_KEYS = {
    "transcription",
    "transliteration",
    "glyph_class",
    "character_identity",
    "phonetic_value",
    "word",
    "word_id",
    "word_boundary",
    "token",
    "token_id",
    "token_boundary",
    "morpheme",
    "sentence",
    "language",
    "semantic_label",
    "semantic_section",
    "currier_class",
    "conventional_section",
    "reading_order",
    "spectral_label",
    "frequency_class",
    "external_transliteration_id",
}

ENTITY_COLLECTIONS = {
    "regions": "region_id",
    "lines": "line_id",
    "glyph_candidates": "glyph_id",
    "ambiguity_groups": "ambiguity_group_id",
}

Point = tuple[int, int]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ObservationValidationError(
                    f"{path}:{line_number}: expected a JSON object"
                )
            rows.append(value)
    return rows


def load_panel_record(pages_path: Path, panel_id: str) -> dict[str, Any]:
    matches = [
        row
        for row in read_jsonl(pages_path)
        if str(row.get("photographic_panel_id") or "") == panel_id
    ]
    if len(matches) != 1:
        raise ObservationValidationError(
            f"expected one canonical page record for {panel_id}, found {len(matches)}"
        )
    panel = matches[0]
    if panel.get("acquisition_status") != "verified":
        raise ObservationValidationError(f"source panel is not verified: {panel_id}")
    if len(str(panel.get("source_sha256") or "")) != 64:
        raise ObservationValidationError(f"source panel has invalid SHA-256: {panel_id}")
    return panel


def build_blank_package(panel: dict[str, Any]) -> dict[str, Any]:
    panel_id = str(panel["photographic_panel_id"])
    width = int(panel["width_px"])
    height = int(panel["height_px"])
    package = {
        "schema_version": "0.1.0",
        "protocol_id": "OBSERVATION-PROTOCOL-0001",
        "package_id": f"OBS-PKG-{panel_id}-R000",
        "package_status": "blank",
        "source": {
            "photographic_panel_id": panel_id,
            "institutional_id": str(panel["institutional_id"]),
            "institutional_label": str(panel["institutional_label"]),
            "source_url": str(panel["source_url"]),
            "source_sha256": str(panel["source_sha256"]),
            "stored_path": str(panel["stored_path"]),
            "width_px": width,
            "height_px": height,
        },
        "coordinate_space": {
            "origin": "top_left",
            "x_axis": "right",
            "y_axis": "down",
            "units": "source_pixels",
            "width_px": width,
            "height_px": height,
            "display_transforms": [],
        },
        "revision": {
            "revision_number": 0,
            "supersedes_package_id": None,
            "created_at": None,
        },
        "annotator_id": None,
        "regions": [],
        "lines": [],
        "glyph_candidates": [],
        "ambiguity_groups": [],
        "revision_events": [],
        "external_transliterations_used": False,
        "semantic_interpretation_used": False,
        "reading_order_asserted": False,
    }
    validate_package(package)
    return package


def write_blank_package(
    *, pages_path: Path, panel_id: str, output_path: Path
) -> dict[str, Any]:
    package = build_blank_package(load_panel_record(pages_path, panel_id))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(package, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return package


def _walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in FORBIDDEN_KEYS:
                raise ObservationValidationError(
                    f"forbidden interpretive field at {path}.{key}"
                )
            _walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, f"{path}[{index}]")


def _points(value: Sequence[Sequence[int]], label: str) -> list[Point]:
    points: list[Point] = []
    for index, raw in enumerate(value):
        if len(raw) != 2:
            raise ObservationValidationError(f"{label}[{index}] is not an x/y point")
        x, y = raw
        if isinstance(x, bool) or isinstance(y, bool):
            raise ObservationValidationError(f"{label}[{index}] uses boolean coordinates")
        if not isinstance(x, int) or not isinstance(y, int):
            raise ObservationValidationError(
                f"{label}[{index}] must use integer source pixels"
            )
        points.append((x, y))
    return points


def _validate_bounds(points: Sequence[Point], width: int, height: int, label: str) -> None:
    if not points:
        raise ObservationValidationError(f"{label} has no points")
    for x, y in points:
        if not 0 <= x < width or not 0 <= y < height:
            raise ObservationValidationError(
                f"{label} point {(x, y)} lies outside {width}x{height} source pixels"
            )


def _bounding_box(points: Sequence[Point]) -> tuple[int, int, int, int]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _validate_nonzero_envelope(points: Sequence[Point], label: str) -> None:
    min_x, min_y, max_x, max_y = _bounding_box(points)
    if min_x == max_x or min_y == max_y:
        raise ObservationValidationError(f"{label} has a zero-area bounding envelope")


def _point_on_segment(point: Point, start: Point, end: Point) -> bool:
    px, py = point
    ax, ay = start
    bx, by = end
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if cross != 0:
        return False
    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)


def _point_in_polygon(point: Point, polygon: Sequence[Point]) -> bool:
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if _point_on_segment(point, start, end):
            return True

    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersects = (yi > y) != (yj > y) and x < (
            (xj - xi) * (y - yi) / (yj - yi) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _validate_containment(
    child: Sequence[Point], parent: Sequence[Point], label: str
) -> None:
    parent_box = _bounding_box(parent)
    child_box = _bounding_box(child)
    if not (
        parent_box[0] <= child_box[0]
        and parent_box[1] <= child_box[1]
        and child_box[2] <= parent_box[2]
        and child_box[3] <= parent_box[3]
    ):
        raise ObservationValidationError(f"{label} exceeds its parent bounding envelope")
    outside = [point for point in child if not _point_in_polygon(point, parent)]
    if outside:
        raise ObservationValidationError(
            f"{label} contains points outside its parent polygon: {outside[:3]}"
        )


def _entity_panel_id(entity_id: str) -> str | None:
    match = re.search(r"YDC-PANEL-[0-9]+", entity_id)
    return match.group(0) if match else None


def _index_entities(package: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    entities: dict[str, Any] = {}
    kinds: dict[str, str] = {}
    for collection, id_key in ENTITY_COLLECTIONS.items():
        rows = package.get(collection)
        if not isinstance(rows, list):
            raise ObservationValidationError(f"{collection} must be an array")
        for row in rows:
            if not isinstance(row, dict):
                raise ObservationValidationError(f"{collection} contains a non-object")
            entity_id = str(row.get(id_key) or "")
            if not entity_id:
                raise ObservationValidationError(f"{collection} contains an entity without {id_key}")
            if entity_id in entities:
                raise ObservationValidationError(f"duplicate observation entity ID: {entity_id}")
            entities[entity_id] = row
            kinds[entity_id] = collection
    return entities, kinds


def validate_package(package: dict[str, Any]) -> dict[str, Any]:
    """Validate cross-record and geometric rules not expressible in JSON Schema."""

    if not isinstance(package, dict):
        raise ObservationValidationError("observation package must be an object")
    _walk_forbidden_keys(package)

    source = package.get("source")
    coordinate_space = package.get("coordinate_space")
    revision = package.get("revision")
    if not isinstance(source, dict) or not isinstance(coordinate_space, dict):
        raise ObservationValidationError("source and coordinate_space must be objects")
    if not isinstance(revision, dict):
        raise ObservationValidationError("revision must be an object")

    panel_id = str(source.get("photographic_panel_id") or "")
    width = int(source.get("width_px") or 0)
    height = int(source.get("height_px") or 0)
    if width <= 0 or height <= 0:
        raise ObservationValidationError("source dimensions must be positive")
    if coordinate_space.get("units") != "source_pixels":
        raise ObservationValidationError("canonical coordinates must use source_pixels")
    if int(coordinate_space.get("width_px") or 0) != width or int(
        coordinate_space.get("height_px") or 0
    ) != height:
        raise ObservationValidationError(
            "coordinate-space dimensions differ from source dimensions"
        )

    revision_number = int(revision.get("revision_number", -1))
    expected_package_id = f"OBS-PKG-{panel_id}-R{revision_number:03d}"
    if package.get("package_id") != expected_package_id:
        raise ObservationValidationError(
            f"package_id must be {expected_package_id} for this panel and revision"
        )
    if revision_number == 0 and revision.get("supersedes_package_id") is not None:
        raise ObservationValidationError("revision zero cannot supersede another package")
    if revision_number > 0 and not revision.get("supersedes_package_id"):
        raise ObservationValidationError("later revisions must name the superseded package")

    if package.get("external_transliterations_used") is not False:
        raise ObservationValidationError("external transliterations are forbidden")
    if package.get("semantic_interpretation_used") is not False:
        raise ObservationValidationError("semantic interpretation is forbidden")
    if package.get("reading_order_asserted") is not False:
        raise ObservationValidationError("reading-order assertions are forbidden")

    entities, kinds = _index_entities(package)
    for entity_id in entities:
        if _entity_panel_id(entity_id) != panel_id:
            raise ObservationValidationError(
                f"entity {entity_id} does not belong to source panel {panel_id}"
            )

    regions = {
        str(row["region_id"]): row for row in package.get("regions", [])
    }
    lines = {str(row["line_id"]): row for row in package.get("lines", [])}

    region_polygons: dict[str, list[Point]] = {}
    for region_id, region in regions.items():
        polygon = _points(region.get("polygon", []), f"region {region_id}")
        if len(polygon) < 3:
            raise ObservationValidationError(f"region {region_id} needs at least 3 points")
        _validate_bounds(polygon, width, height, f"region {region_id}")
        _validate_nonzero_envelope(polygon, f"region {region_id}")
        region_polygons[region_id] = polygon

    line_polygons: dict[str, list[Point]] = {}
    for line_id, line in lines.items():
        parent_id = str(line.get("parent_region_id") or "")
        if parent_id not in regions:
            raise ObservationValidationError(
                f"line {line_id} refers to unknown region {parent_id}"
            )
        polygon = _points(line.get("polygon", []), f"line {line_id}")
        if len(polygon) < 3:
            raise ObservationValidationError(f"line {line_id} needs at least 3 points")
        _validate_bounds(polygon, width, height, f"line {line_id}")
        _validate_nonzero_envelope(polygon, f"line {line_id}")
        _validate_containment(
            polygon, region_polygons[parent_id], f"line {line_id}"
        )
        baseline_raw = line.get("baseline")
        if baseline_raw is not None:
            baseline = _points(baseline_raw, f"line {line_id} baseline")
            if len(baseline) < 2:
                raise ObservationValidationError(
                    f"line {line_id} baseline needs at least 2 points"
                )
            _validate_bounds(baseline, width, height, f"line {line_id} baseline")
            _validate_containment(baseline, polygon, f"line {line_id} baseline")
        line_polygons[line_id] = polygon

    for glyph in package.get("glyph_candidates", []):
        glyph_id = str(glyph["glyph_id"])
        region_id = str(glyph.get("parent_region_id") or "")
        line_id_raw = glyph.get("parent_line_id")
        line_id = str(line_id_raw) if line_id_raw is not None else None
        if region_id not in regions:
            raise ObservationValidationError(
                f"glyph {glyph_id} refers to unknown region {region_id}"
            )
        if line_id is not None:
            if line_id not in lines:
                raise ObservationValidationError(
                    f"glyph {glyph_id} refers to unknown line {line_id}"
                )
            if lines[line_id].get("parent_region_id") != region_id:
                raise ObservationValidationError(
                    f"glyph {glyph_id} line and region parents disagree"
                )
        polygon = _points(glyph.get("polygon", []), f"glyph {glyph_id}")
        if len(polygon) < 3:
            raise ObservationValidationError(f"glyph {glyph_id} needs at least 3 points")
        _validate_bounds(polygon, width, height, f"glyph {glyph_id}")
        _validate_nonzero_envelope(polygon, f"glyph {glyph_id}")
        parent_polygon = (
            line_polygons[line_id] if line_id is not None else region_polygons[region_id]
        )
        _validate_containment(polygon, parent_polygon, f"glyph {glyph_id}")

    for group in package.get("ambiguity_groups", []):
        group_id = str(group["ambiguity_group_id"])
        members = [str(value) for value in group.get("member_entity_ids", [])]
        if len(members) < 2:
            raise ObservationValidationError(
                f"ambiguity group {group_id} needs at least two members"
            )
        missing = [member for member in members if member not in entities]
        if missing:
            raise ObservationValidationError(
                f"ambiguity group {group_id} has unknown members: {missing}"
            )
        member_kinds = {kinds[member] for member in members}
        if len(member_kinds) != 1:
            raise ObservationValidationError(
                f"ambiguity group {group_id} mixes entity kinds: {sorted(member_kinds)}"
            )
        preferred = [str(value) for value in group.get("preferred_entity_ids", [])]
        if any(value not in members for value in preferred):
            raise ObservationValidationError(
                f"ambiguity group {group_id} prefers a non-member entity"
            )
        status = group.get("resolution_status")
        if status == "unresolved" and preferred:
            raise ObservationValidationError(
                f"unresolved ambiguity group {group_id} cannot prefer an entity"
            )
        if status == "resolved" and not preferred:
            raise ObservationValidationError(
                f"resolved ambiguity group {group_id} needs a preferred entity"
            )

    event_ids: set[str] = set()
    for event in package.get("revision_events", []):
        event_id = str(event.get("event_id") or "")
        if not event_id or event_id in event_ids:
            raise ObservationValidationError(
                f"missing or duplicate revision event ID: {event_id}"
            )
        event_ids.add(event_id)
        if _entity_panel_id(event_id) != panel_id:
            raise ObservationValidationError(
                f"revision event {event_id} does not belong to {panel_id}"
            )
        entity_id = str(event.get("entity_id") or "")
        if entity_id not in entities:
            raise ObservationValidationError(
                f"revision event {event_id} refers to unknown entity {entity_id}"
            )
        resulting = event.get("resulting_entity_sha256")
        if event.get("event_type") in {"add", "modify", "uncertainty_update"}:
            if resulting != canonical_sha256(entities[entity_id]):
                raise ObservationValidationError(
                    f"revision event {event_id} resulting hash does not match {entity_id}"
                )
        if event.get("event_type") == "retire" and entities[entity_id].get(
            "observation_status"
        ) != "retired":
            raise ObservationValidationError(
                f"revision event {event_id} retires an active entity"
            )

    status = package.get("package_status")
    entity_count = len(entities)
    if status == "blank":
        if revision_number != 0 or package.get("annotator_id") is not None:
            raise ObservationValidationError(
                "blank packages require revision zero and no annotator"
            )
        if entity_count or package.get("revision_events"):
            raise ObservationValidationError("blank packages cannot contain observations")
    elif status in {"draft", "frozen"}:
        if not package.get("annotator_id"):
            raise ObservationValidationError(f"{status} package requires annotator_id")
        if revision.get("created_at") is None:
            raise ObservationValidationError(f"{status} package requires created_at")
    if status == "frozen" and not package.get("revision_events"):
        raise ObservationValidationError("frozen package requires revision provenance")

    return {
        "package_id": str(package.get("package_id") or ""),
        "package_status": status,
        "region_count": len(regions),
        "line_count": len(lines),
        "glyph_candidate_count": len(package.get("glyph_candidates", [])),
        "ambiguity_group_count": len(package.get("ambiguity_groups", [])),
        "revision_event_count": len(package.get("revision_events", [])),
        "package_sha256": canonical_sha256(package),
    }
