import re

from objects import Connection, RouteConfig, Zone

__all__ = ["Connection", "RouteConfig", "Zone", "ParseError", "Parser"]


ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
NB_DRONES_PATTERN = re.compile(r"^nb_drones\s*:\s*(-?\d+)$")
ZONE_PATTERN = re.compile(
    r"^(start_hub|hub|end_hub)\s*:\s*([^\s]+)\s+"
    r"(-?\d+)\s+(-?\d+)(?:\s+\[(.*?)\])?$"
)
CONNECTION_PATTERN = re.compile(
    r"^connection\s*:\s*([^-]+?)\s*-\s*([^\s]+)"
    r"(?:\s+\[(.*?)\])?$"
)


class ParseError(Exception):
    """Report an invalid map-file format or value."""

    pass


class Parser:
    """Parse a map file into a validated route configuration."""

    def __init__(self, file_path):
        """Store the path of the map file to parse."""
        self.file_path = file_path

    def parse(self) -> RouteConfig:
        """Read the map file and return its route configuration."""
        self.raw_data: dict = {"zones": {}, "connections": []}
        self.seen_connections: set[tuple[str, str]] = set()
        self.start_count = 0
        self.end_count = 0
        self.parsed_nb_drones = False

        with open(self.file_path, 'r') as file:
            for line_num, line in enumerate(file, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                self._route_line(line, line_num)

        self._validate_file_completeness()
        return RouteConfig(**self.raw_data)

    def _route_line(self, line: str, line_num: int):
        """Dispatch one non-empty map line to its specialized parser."""
        if not self.parsed_nb_drones:
            self._parse_nb_drones(line, line_num)

        elif line.startswith(("start_hub:", "hub:", "end_hub:")):
            self._parse_zone(line, line_num)

        elif line.startswith("connection:"):
            self._parse_connection(line, line_num)

        else:
            raise ParseError(f"Line {line_num}: Invalid syntax -> '{line}'")

    def _parse_nb_drones(self, line: str, line_num: int):
        """Parse and validate the number of drones declared by the map."""
        match = NB_DRONES_PATTERN.match(line)
        if not match:
            raise ParseError(
                f"Line {line_num}: First uncommented line must define "
                "'nb_drones: <int>'."
            )

        nb_val = int(match.group(1))
        if nb_val <= 0:
            raise ParseError(f"Line {line_num}: nb_drones must be positive.")

        self.raw_data["nb_drones"] = nb_val
        self.parsed_nb_drones = True

    def _parse_zone(self, line: str, line_num: int):
        """Parse one zone declaration and store its raw data."""
        zone_match = ZONE_PATTERN.match(line)
        if not zone_match:
            raise ParseError(f"Line {line_num}: Invalid zone syntax.")

        role, name, x, y, meta_str = zone_match.groups()

        if "-" in name:
            raise ParseError(
                f"Line {line_num}: Zone '{name}' contains invalid "
                "character '-'."
            )

        if name in self.raw_data["zones"]:
            raise ParseError(f"Line {line_num}: Duplicate zone '{name}'.")

        if role == "start_hub":
            self.start_count += 1
        if role == "end_hub":
            self.end_count += 1

        meta_dict = self._parse_metadata(
            meta_str,
            line_num,
            allowed_keys={"zone", "color", "max_drones"},
        )
        zone_type = meta_dict.get("zone", "normal")

        if zone_type not in ZONE_TYPES:
            raise ParseError(
                f"Line {line_num}: Invalid zone type '{zone_type}'.")

        max_drones = self._positive_metadata_value(
            meta_dict,
            "max_drones",
            line_num,
        )

        self.raw_data["zones"][name] = {
            "role": role,
            "name": name,
            "x": int(x),
            "y": int(y),
            "zone_type": zone_type,
            "color": meta_dict.get("color"),
            "max_drones": max_drones,
        }

    def _parse_connection(self, line: str, line_num: int):
        """Parse one connection declaration and store its raw data."""
        conn_match = CONNECTION_PATTERN.match(line)
        if not conn_match:
            raise ParseError(f"Line {line_num}: Invalid connection syntax.")

        z1, z2, meta_str = conn_match.groups()
        z1 = z1.strip()
        z2 = z2.strip()

        if (
            z1 not in self.raw_data["zones"]
            or z2 not in self.raw_data["zones"]
        ):
            raise ParseError(
                f"Line {line_num}: Connection uses undefined zones"
                f"({z1} or {z2}).")

        sorted_conn = (min(z1, z2), max(z1, z2))
        if sorted_conn in self.seen_connections:
            raise ParseError(
                f"Line {line_num}: Duplicate connection {z1}-{z2}.")

        meta_dict = self._parse_metadata(
            meta_str,
            line_num,
            allowed_keys={"max_link_capacity"},
        )
        max_capacity = self._positive_metadata_value(
            meta_dict,
            "max_link_capacity",
            line_num,
        )

        self.seen_connections.add(sorted_conn)
        self.raw_data["connections"].append({
            "z1": z1, "z2": z2, "max_link_capacity": max_capacity
        })

    def _parse_metadata(
        self,
        meta_string: str | None,
        line_num: int,
        allowed_keys: set[str],
    ) -> dict:
        """Parse metadata and reject unknown or duplicate keys."""
        if not meta_string:
            return {}
        meta_dict = {}

        for pair in meta_string.strip().split():
            if "=" not in pair:
                raise ParseError(
                    f"Line {line_num}: Invalid metadata syntax '{pair}'"
                    f". Expected 'key=value'.")
            key, val = pair.split("=", 1)
            if key not in allowed_keys:
                raise ParseError(
                    f"Line {line_num}: Unknown metadata key '{key}'.")

            if key in meta_dict:
                raise ParseError(
                    f"Line {line_num}: Duplicate metadata key '{key}'.")

            meta_dict[key] = val

        return meta_dict

    def _positive_metadata_value(
        self,
        metadata: dict,
        key: str,
        line_num: int,
    ) -> int | None:
        """Return a positive integer metadata value when one is present."""
        value = metadata.get(key)
        if value is None:
            return None

        if not value.isdigit() or int(value) <= 0:
            raise ParseError(
                f"Line {line_num}: {key} must be a positive integer."
            )

        return int(value)

    def _validate_file_completeness(self):
        """Ensure the map contains exactly one start and end hub."""
        if self.start_count != 1 or self.end_count != 1:
            raise ParseError(
                "End of file: Expected exactly 1 start_hub and 1 end_hub.")
