from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


@dataclass
class Zone:
    """A single zone in the drone network."""

    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = 1

    def __post_init__(self) -> None:
        if self.zone_type not in VALID_ZONE_TYPES:
            raise ValueError(f"Invalid zone type: {self.zone_type}")
        if self.max_drones <= 0:
            raise ValueError(f"Zone {self.name} has invalid max_drones value: {self.max_drones}")


@dataclass
class Connection:
    """A bidirectional link between two zones."""

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    def __post_init__(self) -> None:
        if self.max_link_capacity <= 0:
            raise ValueError(
                f"Connection {self.zone_a}-{self.zone_b} has invalid max_link_capacity: {self.max_link_capacity}"
            )

    @property
    def sorted_pair(self) -> Tuple[str, str]:
        if self.zone_a < self.zone_b:
            return self.zone_a, self.zone_b
        return self.zone_b, self.zone_a


@dataclass
class Drone:
    """A drone moving through the simulation."""

    drone_id: int
    current_zone: str
    delivered: bool = False
    path: List[str] = field(default_factory=list)


class MapGraph:
    """The drone network graph with zone and connection metadata."""

    def __init__(self, nb_drones: int = 0) -> None:
        self.nb_drones: int = nb_drones
        self.zones: Dict[str, Zone] = {}
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def add_zone(self, zone: Zone, *, is_start: bool = False, is_end: bool = False) -> None:
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name: {zone.name}")
        self.zones[zone.name] = zone
        if is_start:
            self.start_zone = zone
        if is_end:
            self.end_zone = zone

    def add_connection(self, connection: Connection) -> None:
        key = connection.sorted_pair
        if key in self.connections:
            raise ValueError(f"Duplicate connection: {connection.zone_a}-{connection.zone_b}")
        if connection.zone_a not in self.zones or connection.zone_b not in self.zones:
            raise ValueError(
                f"Connection {connection.zone_a}-{connection.zone_b} references undefined zones"
            )
        self.connections[key] = connection

    def get_zone(self, name: str) -> Zone:
        if name not in self.zones:
            raise KeyError(f"Unknown zone: {name}")
        return self.zones[name]

    def neighbors(self, zone_name: str) -> Iterable[str]:
        for (a, b), connection in self.connections.items():
            if a == zone_name:
                yield b
            elif b == zone_name:
                yield a

    def get_connection_capacity(self, zone_a: str, zone_b: str) -> int:
        key = (zone_a, zone_b) if zone_a < zone_b else (zone_b, zone_a)
        if key not in self.connections:
            raise KeyError(f"No connection between {zone_a} and {zone_b}")
        return self.connections[key].max_link_capacity

    def validate_start_and_end(self) -> None:
        if self.start_zone is None:
            raise ValueError("Missing start_hub declaration")
        if self.end_zone is None:
            raise ValueError("Missing end_hub declaration")

    @property
    def start_name(self) -> str:
        """Return the validated start zone name."""

        if self.start_zone is None:
            raise ValueError("Missing start_hub declaration")
        return self.start_zone.name

    @property
    def end_name(self) -> str:
        """Return the validated end zone name."""

        if self.end_zone is None:
            raise ValueError("Missing end_hub declaration")
        return self.end_zone.name
