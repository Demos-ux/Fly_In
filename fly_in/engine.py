from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TypedDict

from .models import Drone, MapGraph


@dataclass
class SimulationStep:
    """A single simulation turn with drone moves."""

    turn: int
    moves: List[str] = field(default_factory=list)


class SimulationResult(TypedDict):
    """Structured result returned by the simulation engine."""

    turns: int
    delivered: int
    log: List[str]
    peak_occupancy: Dict[str, int]


class SimulationEngine:
    """Turn-based drone simulation engine."""

    def __init__(self, graph: MapGraph) -> None:
        self.graph = graph
        self.drones: Dict[int, Drone] = {}
        self.turn = 0
        self.log: List[str] = []
        self.pending_transit: Dict[int, Tuple[str, str, int]] = {}
        self.connection_usage: Dict[Tuple[str, str], int] = {}
        self.peak_occupancy: Dict[str, int] = {}
        self._initialize_drones()

    def _initialize_drones(self) -> None:
        for drone_id in range(1, self.graph.nb_drones + 1):
            self.drones[drone_id] = Drone(
                drone_id=drone_id,
                current_zone=self.graph.start_name,
            )

    def _occupancy_snapshot(self) -> Dict[str, int]:
        occupancy: Dict[str, int] = {}
        for drone in self.drones.values():
            if drone.delivered:
                continue
            if drone.drone_id in self.pending_transit:
                continue
            occupancy[drone.current_zone] = occupancy.get(drone.current_zone, 0) + 1
        return occupancy

    def _local_capacity(self, zone_name: str, occupancy: Dict[str, int]) -> bool:
        if zone_name == self.graph.start_name or zone_name == self.graph.end_name:
            return True
        zone = self.graph.get_zone(zone_name)
        return occupancy.get(zone_name, 0) + 1 <= zone.max_drones

    def _edge_capacity(self, zone_a: str, zone_b: str) -> bool:
        if zone_a == zone_b:
            return True
        if zone_a not in self.graph.zones or zone_b not in self.graph.zones:
            return False
        key = (zone_a, zone_b) if zone_a < zone_b else (zone_b, zone_a)
        if key not in self.graph.connections:
            return False
        current_usage = self.connection_usage.get(key, 0)
        limit = self.graph.connections[key].max_link_capacity
        return current_usage + 1 <= limit

    def _zone_cost(self, zone_name: str, occupancy: Dict[str, int]) -> int:
        zone = self.graph.get_zone(zone_name)
        base_cost = {
            "normal": 2,
            "restricted": 4,
            "priority": 1,
        }.get(zone.zone_type, 1000)
        congestion_cost = occupancy.get(zone_name, 0) * 3
        return base_cost + congestion_cost

    def _compute_path(
        self,
        drone: Drone,
        occupancy: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        if drone.current_zone == self.graph.end_name:
            return []

        current_occupancy = occupancy or {}
        queue: List[Tuple[int, str]] = [(0, drone.current_zone)]
        distances: Dict[str, int] = {drone.current_zone: 0}
        previous: Dict[str, Optional[str]] = {drone.current_zone: None}

        while queue:
            distance, node = heapq.heappop(queue)
            if distance != distances[node]:
                continue
            if node == self.graph.end_name:
                break
            for neighbor in self.graph.neighbors(node):
                if self.graph.get_zone(neighbor).zone_type == "blocked":
                    continue
                new_distance = distance + self._zone_cost(neighbor, current_occupancy)
                if new_distance >= distances.get(neighbor, 10**9):
                    continue
                distances[neighbor] = new_distance
                previous[neighbor] = node
                heapq.heappush(queue, (new_distance, neighbor))

        if self.graph.end_name not in previous:
            return []

        path: List[str] = []
        current = self.graph.end_name
        while current is not None:
            path.append(current)
            parent = previous[current]
            if parent is None:
                break
            current = parent
        path.reverse()
        return path

    def _next_step(
        self,
        drone: Drone,
        occupancy: Optional[Dict[str, int]] = None,
    ) -> Optional[str]:
        path = self._compute_path(drone, occupancy)
        if len(path) < 2:
            return None
        return path[1]

    def _apply_turn_arrivals(self) -> None:
        for drone_id, (source_zone, destination_zone, arrival_turn) in list(self.pending_transit.items()):
            if arrival_turn != self.turn:
                continue
            drone = self.drones[drone_id]
            drone.current_zone = destination_zone
            self.pending_transit.pop(drone_id)
            if destination_zone == self.graph.end_name:
                drone.delivered = True

    def run(self) -> SimulationResult:
        """Run a capacity-aware simulation until all drones are delivered."""

        while True:
            self.turn += 1
            self._apply_turn_arrivals()
            occupancy = self._occupancy_snapshot()
            for zone_name, count in occupancy.items():
                self.peak_occupancy[zone_name] = max(
                    self.peak_occupancy.get(zone_name, 0), count
                )

            moves: List[str] = []
            self.connection_usage.clear()
            reserved_target_counts: Dict[str, int] = {}
            planned_moves: Dict[int, str] = {}
            planned_sources: Dict[int, str] = {}
            departures: Dict[str, int] = {}

            for drone in self.drones.values():
                if drone.delivered or drone.drone_id in self.pending_transit:
                    continue
                next_zone = self._next_step(drone, occupancy)
                if next_zone is not None:
                    departures[drone.current_zone] = departures.get(drone.current_zone, 0) + 1

            transit_targets: Dict[str, int] = {}
            for source_zone, destination_zone, _ in self.pending_transit.values():
                transit_targets[destination_zone] = transit_targets.get(destination_zone, 0) + 1
                connection_key = (
                    (source_zone, destination_zone)
                    if source_zone < destination_zone
                    else (destination_zone, source_zone)
                )
                self.connection_usage[connection_key] = (
                    self.connection_usage.get(connection_key, 0) + 1
                )

            for drone_id in sorted(self.drones):
                drone = self.drones[drone_id]
                if drone.delivered or drone.drone_id in self.pending_transit:
                    continue

                if drone.current_zone == self.graph.end_name:
                    drone.delivered = True
                    continue

                next_zone = self._next_step(drone, occupancy)
                if next_zone is None:
                    continue

                if self.graph.get_zone(next_zone).zone_type == "blocked":
                    continue

                if drone.current_zone not in self.graph.zones or next_zone not in self.graph.zones:
                    continue

                if next_zone == self.graph.start_name:
                    continue

                target_zone = self.graph.get_zone(next_zone)
                current_target_count = occupancy.get(next_zone, 0)
                current_target_count += transit_targets.get(next_zone, 0)
                current_target_count -= departures.get(next_zone, 0)
                current_target_count += reserved_target_counts.get(next_zone, 0)
                if target_zone.zone_type != "blocked":
                    is_special_zone = next_zone in (
                        self.graph.start_name,
                        self.graph.end_name,
                    )
                    if not is_special_zone and current_target_count >= target_zone.max_drones:
                        continue

                connection_key = (
                    (drone.current_zone, next_zone)
                    if drone.current_zone < next_zone
                    else (next_zone, drone.current_zone)
                )
                if any(
                    source == next_zone and target == drone.current_zone
                    for moved_drone_id, target in planned_moves.items()
                    for source in [planned_sources[moved_drone_id]]
                ):
                    continue
                if connection_key in self.graph.connections:
                    current_link_usage = self.connection_usage.get(connection_key, 0)
                    max_link_capacity = self.graph.connections[
                        connection_key
                    ].max_link_capacity
                    if current_link_usage + 1 > max_link_capacity:
                        continue

                reserved_target_counts[next_zone] = reserved_target_counts.get(next_zone, 0) + 1
                self.connection_usage[connection_key] = self.connection_usage.get(connection_key, 0) + 1
                planned_moves[drone_id] = next_zone
                planned_sources[drone_id] = drone.current_zone

            for drone_id in sorted(planned_moves):
                drone = self.drones[drone_id]
                next_zone = planned_moves[drone_id]
                moves.append(f"D{drone_id}-{next_zone}")

                if self.graph.get_zone(next_zone).zone_type == "restricted":
                    self.pending_transit[drone_id] = (drone.current_zone, next_zone, self.turn + 1)
                    continue

                drone.current_zone = next_zone
                if next_zone == self.graph.end_name:
                    drone.delivered = True

            self.log.append(f"turn {self.turn}: {' '.join(moves) if moves else 'wait'}")

            if all(drone.delivered for drone in self.drones.values()):
                break
            if not moves and not self.pending_transit:
                raise RuntimeError("Simulation is deadlocked: no valid drone movement remains")

        return {
            "turns": self.turn,
            "delivered": sum(1 for drone in self.drones.values() if drone.delivered),
            "log": self.log,
            "peak_occupancy": self.peak_occupancy,
        }
