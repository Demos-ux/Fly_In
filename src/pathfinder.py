from collections import deque
from typing import Optional


class Pathfinder:
    """Find routes through a graph while avoiding blocked zones."""

    def __init__(self, graph):
        """Store the graph used for path searches."""
        self.graph = graph

    def shortest_path(
        self,
        start: str,
        goal: str,
        forbidden: set[str] | None = None, #forbidden zones to avoid
    ) -> list[str] | None:
        """Return a shortest path while excluding forbidden zones."""
        forbidden = forbidden or set()
        zones = self.graph.all_vertices()

        if start not in zones or goal not in zones:
            return None

        if start in forbidden or goal in forbidden:
            return None

        queue = deque([start])
        previous: dict[str, Optional[str]] = {start: None} 

        while queue:
            current = queue.popleft()

            if current == goal:
                return self._reconstruct_path(previous, goal)

            for neighbor in self.graph.neighbors(current):
                if neighbor in previous:
                    continue

                if neighbor in forbidden:
                    continue

                if self.graph.zone(neighbor).zone_type == "blocked":
                    continue

                previous[neighbor] = current
                queue.append(neighbor)

        return None

    @staticmethod
    def _reconstruct_path(
        previous: dict[str, str | None],
        goal: str,
    ) -> list[str]:
        """Rebuild a path by following predecessors back to the start."""
        path = []
        current: str | None = goal

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        
        return path
