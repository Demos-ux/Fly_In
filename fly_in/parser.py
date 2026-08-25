from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

from .models import Connection, MapGraph, VALID_ZONE_TYPES, Zone


ZONE_PATTERN = re.compile(r"^(start_hub|end_hub|hub):\s+(\S+)\s+(-?\d+)\s+(-?\d+)(?:\s+(\[[^\]]*\]))?\s*$")
CONNECTION_PATTERN = re.compile(r"^connection:\s*(\S+)-(\S+)(?:\s+(\[[^\]]*\]))?\s*$")


def _parse_metadata(raw: Optional[str]) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    if not raw:
        return metadata
    content = raw.strip()[1:-1].strip()
    if not content:
        return metadata
    for part in content.split():
        if "=" not in part:
            raise ValueError(f"Malformed metadata entry: {part}")
        key, value = part.split("=", 1)
        metadata[key] = value
    return metadata


def _parse_positive_int(value: str, field_name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}: {value}") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return parsed


def parse_map(content: str) -> MapGraph:
    """Parse a drone map from a text string and build the graph."""

    graph = MapGraph()
    seen_connection_keys = set()
    seen_zone_names = set()

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("nb_drones:"):
            value = line.split(":", 1)[1].strip()
            graph.nb_drones = _parse_positive_int(value, "nb_drones")
            continue

        zone_match = ZONE_PATTERN.match(line)
        if zone_match:
            prefix, name, x_str, y_str, metadata_raw = zone_match.groups()
            if name in seen_zone_names:
                raise ValueError(f"Duplicate zone name: {name}")
            seen_zone_names.add(name)

            x = int(x_str)
            y = int(y_str)
            metadata = _parse_metadata(metadata_raw)

            zone_type = metadata.get("zone", "normal")
            if zone_type not in VALID_ZONE_TYPES:
                raise ValueError(f"Invalid zone type on line {line_number}: {zone_type}")

            max_drones = _parse_positive_int(metadata.get("max_drones", "1"), "max_drones")
            zone = Zone(
                name=name,
                x=x,
                y=y,
                zone_type=zone_type,
                color=metadata.get("color"),
                max_drones=max_drones,
            )
            graph.add_zone(zone, is_start=(prefix == "start_hub"), is_end=(prefix == "end_hub"))
            continue

        connection_match = CONNECTION_PATTERN.match(line)
        if connection_match:
            zone_a, zone_b, metadata_raw = connection_match.groups()
            if "-" in zone_a or "-" in zone_b:
                raise ValueError(f"Invalid connection name on line {line_number}: {line}")
            if zone_a in seen_zone_names and zone_b in seen_zone_names:
                pass
            else:
                # Keep validation strict by checking zones are defined before use.
                if zone_a not in seen_zone_names or zone_b not in seen_zone_names:
                    raise ValueError(
                        f"Connection references undefined zones on line {line_number}: {line}"
                    )

            metadata = _parse_metadata(metadata_raw)
            capacity = _parse_positive_int(metadata.get("max_link_capacity", "1"), "max_link_capacity")
            connection = Connection(zone_a=zone_a, zone_b=zone_b, max_link_capacity=capacity)
            key = connection.sorted_pair
            if key in seen_connection_keys:
                raise ValueError(f"duplicate connection: {zone_a}-{zone_b}")
            seen_connection_keys.add(key)
            graph.add_connection(connection)
            continue

        raise ValueError(f"Parse error on line {line_number}: {line}")

    if graph.nb_drones <= 0:
        raise ValueError("nb_drones must be a positive integer")
    if graph.start_zone is None:
        raise ValueError("Map must define a start_hub")
    if graph.end_zone is None:
        raise ValueError("Map must define an end_hub")
    graph.validate_start_and_end()

    return graph


def parse_map_file(path: str | Path) -> MapGraph:
    """Parse a drone map from a file path."""
    file_path = Path(path)
    content = file_path.read_text(encoding="utf-8")
    return parse_map(content)
