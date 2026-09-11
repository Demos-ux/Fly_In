from dataclasses import dataclass
from pydantic import BaseModel, Field


class Zone(BaseModel):
    """Describe a named map zone and its movement constraints."""

    role: str
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: str | None = None
    max_drones: int | None = None


class Connection(BaseModel):
    """Describe an undirected connection between two zones."""

    z1: str
    z2: str
    max_link_capacity: int | None = None


class RouteConfig(BaseModel):
    """Store the complete validated configuration of one map."""

    nb_drones: int = Field(gt=0)
    zones: dict[str, Zone]
    connections: list[Connection]


@dataclass
class Drone:
    """Store the current state of one simulated drone."""

    id: int
    zone: str
    path: list[str] | None = None
    path_index: int = 0
    in_flight: bool = False
    destination: str | None = None
