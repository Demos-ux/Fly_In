from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Zone(BaseModel):
    """Describe a named map zone and its movement constraints."""

    role: Literal["start_hub", "hub", "end_hub"]
    name: str
    x: int
    y: int
    zone_type: Literal["normal", "blocked", "restricted", "priority"] = (
        "normal"
    )
    color: str | None = None
    max_drones: int | None = Field(default=None, gt=0)


class Connection(BaseModel):
    """Describe an undirected connection between two zones."""

    z1: str
    z2: str
    max_link_capacity: int | None = Field(default=None, gt=0)


class RouteConfig(BaseModel):
    """Store the complete validated configuration of one map."""

    nb_drones: int = Field(gt=0)
    zones: dict[str, Zone]
    connections: list[Connection]

    @model_validator(mode="after")
    def validate_zone_names(self):
        for zone_name, zone in self.zones.items():
            if zone.name != zone_name:
                raise ValueError(
                    f"Zone key does not match zone name: {zone_name}"
                )
        return self


@dataclass
class Drone:
    """Store the current state of one simulated drone."""

    id: int
    zone: str
    path: list[str] | None = None
    path_index: int = 0
    in_flight: bool = False
    destination: str | None = None
