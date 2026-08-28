import re
from pydantic import BaseModel, Field

class ParseError(Exception):
    pass

class Zone(BaseModel):
    role: str
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: str | None = None
    max_drones: int | None = None

class Connection(BaseModel):
    z1: str
    z2: str
    max_link_capacity: int | None = None

class RouteConfig(BaseModel):
    nb_drones: int = Field(gt=0)
    zones: dict[str, Zone]
    connections: list[Connection]

class Parser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self) -> RouteConfig:
        self.raw_data = {"zones": {}, "connections": []}
        self.seen_connections = set()
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
        if not self.parsed_nb_drones:
            self._parse_nb_drones(line, line_num)

        elif line.startswith(("start_hub:", "hub:", "end_hub:")):
            self._parse_zone(line, line_num)

        elif line.startswith("connection:"):
            self._parse_connection(line, line_num)

        else:
            raise ParseError(f"Line {line_num}: Invalid syntax -> '{line}'")

    def _parse_nb_drones(self, line: str, line_num: int):
        match = re.match(r'^nb_drones\s*:\s*(-?\d+)$', line)
        if not match:
            raise ParseError(f"Line {line_num}: First uncommented line must define 'nb_drones: <int>'.")
        
        nb_val = int(match.group(1))
        if nb_val <= 0:
            raise ParseError(f"Line {line_num}: nb_drones must be positive.")
        
        self.raw_data["nb_drones"] = nb_val
        self.parsed_nb_drones = True

    def _parse_zone(self, line: str, line_num: int):
        zone_match = re.match(r'^(start_hub|hub|end_hub)\s*:\s*([^\s]+)\s+(-?\d+)\s+(-?\d+)(?:\s+\[(.*?)\])?$', line)
        if not zone_match:
            raise ParseError(f"Line {line_num}: Invalid zone syntax.")
            
        role, name, x, y, meta_str = zone_match.groups()
        
        if "-" in name:
            raise ParseError(f"Line {line_num}: Zone '{name}' contains invalid character '-'.")

        if name in self.raw_data["zones"]:
            raise ParseError(f"Line {line_num}: Duplicate zone '{name}'.")
        
        if role == "start_hub": self.start_count += 1
        if role == "end_hub": self.end_count += 1

        meta_dict = self._parse_metadata(meta_str, line_num)
        zone_type = meta_dict.get("zone", "normal")
        
        if zone_type not in ["normal", "blocked", "restricted", "priority"]:
            raise ParseError(f"Line {line_num}: Invalid zone type '{zone_type}'.")
        
        max_drones = None
        if "max_drones" in meta_dict:
            if not meta_dict["max_drones"].isdigit() or int(meta_dict["max_drones"]) <= 0:
                raise ParseError(f"Line {line_num}: max_drones must be a positive integer.")

            max_drones = int(meta_dict["max_drones"])

        self.raw_data["zones"][name] = {
            "role": role, "name": name, "x": int(x), "y": int(y), 
            "zone_type": zone_type, "color": meta_dict.get("color"), "max_drones": max_drones
        }

    def _parse_connection(self, line: str, line_num: int):
        conn_match = re.match(r'^connection\s*:\s*([^-]+)-([^\s]+)(?:\s+\[(.*?)\])?$', line)
        if not conn_match:
            raise ParseError(f"Line {line_num}: Invalid connection syntax.")
            
        z1, z2, meta_str = conn_match.groups()

        if z1 not in self.raw_data["zones"] or z2 not in self.raw_data["zones"]:
            raise ParseError(f"Line {line_num}: Connection uses undefined zones ({z1} or {z2}).")
        
        sorted_conn = tuple(sorted([z1, z2]))
        if sorted_conn in self.seen_connections:
            raise ParseError(f"Line {line_num}: Duplicate connection {z1}-{z2}.")
        
        meta_dict = self._parse_metadata(meta_str, line_num)
        max_capacity = None

        if "max_link_capacity" in meta_dict:
            if not meta_dict["max_link_capacity"].isdigit() or int(meta_dict["max_link_capacity"]) <= 0:
                raise ParseError(f"Line {line_num}: max_link_capacity must be a positive integer.")
            max_capacity = int(meta_dict["max_link_capacity"])
        
        self.seen_connections.add(sorted_conn)
        self.raw_data["connections"].append({
            "z1": z1, "z2": z2, "max_link_capacity": max_capacity
        })

    def _parse_metadata(self, meta_string: str | None, line_num: int) -> dict:
        if not meta_string:
            return {}
        meta_dict = {}

        for pair in meta_string.strip().split():
            if "=" not in pair:
                raise ParseError(f"Line {line_num}: Invalid metadata syntax '{pair}'. Expected 'key=value'.")
            key, val = pair.split("=", 1)
            meta_dict[key] = val

        return meta_dict

    def _validate_file_completeness(self):
        if self.start_count != 1 or self.end_count != 1:
            raise ParseError(f"End of file: Expected exactly 1 start_hub and 1 end_hub.")