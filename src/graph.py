from objects import Connection, RouteConfig, Zone


class Graph:
    """Represent map zones and their undirected connections."""

    def __init__(self, config: RouteConfig):
        """Build and validate a graph from a route configuration."""
        self.config = config
        self._zones = config.zones
        self._adjacency: dict = {
            zone_name: {}
            for zone_name in self._zones
        }

        self._validate_graph()

        for connection in config.connections:
            self._adjacency[connection.z1][connection.z2] = connection
            self._adjacency[connection.z2][connection.z1] = connection

    def _validate_graph(self):
        """Validate graph-specific rules before building adjacency data."""
        start_zones = [
            zone for zone in self._zones.values()
            if zone.role == "start_hub"
        ]
        end_zones = [
            zone for zone in self._zones.values()
            if zone.role == "end_hub"
        ]

        if len(start_zones) != 1:
            raise ValueError("Graph must contain exactly one start zone")

        if len(end_zones) != 1:
            raise ValueError("Graph must contain exactly one end zone")

        if start_zones[0].zone_type == "blocked":
            raise ValueError("The start zone cannot be blocked")

        if end_zones[0].zone_type == "blocked":
            raise ValueError("The end zone cannot be blocked")

        seen_edges = set()

        for connection in self.config.connections:
            if connection.z1 == connection.z2:
                raise ValueError(
                    f"Self-connections are not allowed: {connection.z1}"
                )

            if connection.z1 not in self._zones:
                raise ValueError(f"Unknown zone: {connection.z1}")

            if connection.z2 not in self._zones:
                raise ValueError(f"Unknown zone: {connection.z2}")

            edge = frozenset((connection.z1, connection.z2))

            if edge in seen_edges:
                raise ValueError(
                    f"Duplicate connection: "
                    f"{connection.z1}-{connection.z2}"
                )

            seen_edges.add(edge)

    def zone(self, name: str) -> Zone:
        """Return the zone with the given name."""
        return self._zones[name]

    def all_vertices(self) -> set[str]:
        """Return the names of all zones in the graph."""
        return set(self._zones)

    def neighbors(self, zone_name: str) -> list[str]:
        """Return zones directly connected to the given zone."""
        if zone_name not in self._adjacency:
            raise KeyError(f"Unknown zone: {zone_name}")

        return list(self._adjacency[zone_name])

    def edges(self, zone_name: str) -> list[Connection]:
        """Return connections leaving the given zone."""
        if zone_name not in self._adjacency:
            raise KeyError(f"Unknown zone: {zone_name}")

        return list(self._adjacency[zone_name].values())

    def connection_between(
        self,
        first: str,
        second: str,
    ) -> Connection | None:
        """Return the connection between two zones, if it exists."""
        return self._adjacency.get(first, {}).get(second)

    def all_edges(self) -> list[Connection]:
        """Return every connection in the graph exactly once."""
        return self.config.connections.copy()
