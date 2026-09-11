from collections import Counter
from collections.abc import Callable

from objects import Drone
from pathfinder import Pathfinder


class Simulation:
    """Schedule drone movements while enforcing graph constraints."""

    def __init__(self, graph):
        """Initialize a simulation for the given graph."""
        self.graph = graph
        self.pathfinder = Pathfinder(graph)
        self.drones: list[Drone] = []

    def run(
        self,
        start: str,
        goal: str,
        on_turn: Callable[[str, int], None] | None = None,
    ) -> list[str] | None:
        """Run the simulation and return one output line per turn."""
        initial_path = self.pathfinder.shortest_path(start, goal)

        if initial_path is None:
            return None

        self.drones = [
            Drone(id=drone_id, zone=start, path=initial_path)
            for drone_id in range(1, self.graph.config.nb_drones + 1)
        ]

        output_lines = []
        while self.drones:
            movements, completed_flights = self._complete_flights()
            movements.extend(
                self._move_available_drones(start, goal, completed_flights)
            )

            self.drones = [
                drone
                for drone in self.drones
                if drone.zone != goal
            ]

            if not movements:
                raise RuntimeError("Simulation is blocked: no drone can move")

            turn_output = " ".join(movements)
            output_lines.append(turn_output)

            if on_turn is not None:
                on_turn(turn_output, len(output_lines))

        return output_lines

    def _complete_flights(self) -> tuple[list[str], set[int]]:
        """Complete restricted-zone flights that started in earlier turns."""
        movements = []
        completed = set()
        for drone in self.drones:
            if not drone.in_flight:
                continue

            if drone.destination is None:
                raise RuntimeError(
                    f"Drone {drone.id} is in flight without a destination"
                )

            drone.zone = drone.destination
            drone.destination = None
            drone.in_flight = False
            completed.add(drone.id)
            movements.append(f"D{drone.id}-{drone.zone}")

        return movements, completed

    def _move_available_drones(
        self,
        start: str,
        goal: str,
        completed_flights: set[int],
    ) -> list[str]:
        """Plan and apply valid movements for available drones."""
        movements = []
        occupied = Counter(
            drone.zone
            for drone in self.drones
            if not drone.in_flight
        )
        departures: Counter[str] = Counter()
        arrivals: Counter[str] = Counter()
        reserved_edges: Counter[frozenset[str]] = Counter()
        reserved_destinations: Counter[str] = Counter()

        for drone in sorted(self.drones, key=lambda item: item.id):
            if drone.in_flight or drone.id in completed_flights:
                continue

            forbidden = self._full_zones(drone)
            for destination in reserved_destinations:
                forbidden.add(destination)

            path = self._path_for_drone(drone, goal, forbidden)
            if path is None or len(path) < 2:
                continue

            next_zone = path[1]
            connection = self.graph.connection_between(
                drone.zone,
                next_zone,
            )
            if connection is None:
                continue

            zone = self.graph.zone(next_zone)
            if zone.zone_type == "blocked":
                continue

            edge = frozenset((drone.zone, next_zone))
            if not self._link_available(
                connection.max_link_capacity,
                reserved_edges[edge],
            ):
                continue

            if not self._zone_available(
                next_zone,
                occupied,
                departures,
                arrivals,
                reserved_destinations,
            ):
                continue

            drone.path = path
            drone.path_index = 1
            departures[drone.zone] += 1
            arrivals[next_zone] += 1
            reserved_edges[edge] += 1
            reserved_destinations[next_zone] += 1

            if zone.zone_type == "restricted":
                drone.destination = next_zone
                drone.in_flight = True
                movements.append(f"D{drone.id}-{drone.zone}-{next_zone}")
            else:
                drone.zone = next_zone
                movements.append(f"D{drone.id}-{next_zone}")

        return movements

    def _path_for_drone(
        self,
        drone: Drone,
        goal: str,
        forbidden: set[str],
    ) -> list[str] | None:
        """Reuse a drone path or find an alternative around blocked zones."""
        if drone.path is not None and drone.path_index + 1 < len(drone.path):
            if drone.path[drone.path_index + 1] not in forbidden:
                return drone.path[drone.path_index:]

        return self.pathfinder.shortest_path(
            drone.zone,
            goal,
            forbidden,
        )

    def _zone_available(
        self,
        zone_name: str,
        occupied: Counter[str],
        departures: Counter[str],
        arrivals: Counter[str],
        reserved: Counter[str],
    ) -> bool:
        """Check whether a destination can accept one more drone this turn."""
        if reserved[zone_name] > 0:
            return False

        zone = self.graph.zone(zone_name)
        if zone.max_drones is None:
            return True

        projected = (
            occupied[zone_name]
            - departures[zone_name]
            + arrivals[zone_name]
            + 1
        )
        return projected <= zone.max_drones

    def _full_zones(self, drone: Drone) -> set[str]:
        """Return explicitly capacity-limited zones that are currently full."""
        occupied = Counter(
            other.zone
            for other in self.drones
            if not other.in_flight and other.id != drone.id
        )
        full = set()

        for zone_name, count in occupied.items():
            capacity = self.graph.zone(zone_name).max_drones
            if capacity is not None and count >= capacity:
                full.add(zone_name)

        return full

    @staticmethod
    def _link_available(capacity: int | None, used: int) -> bool:
        """Check whether another drone can use a connection this turn."""
        return capacity is None or used < capacity
