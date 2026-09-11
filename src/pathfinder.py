from collections import deque


class Pathfinder:
    def __init__(self, graph):
        self.graph = graph

    def shortest_path(self, start: str, goal: str) -> list[str] | None:
        if start not in self.graph._zones or goal not in self.graph._zones:
            return None

        queue = deque([start])
        previous = {start: None}

        while queue:
            current = queue.popleft()

            if current == goal:
                return self._reconstruct_path(previous, goal)

            for neighbor in self.graph.neighbors(current):
                if neighbor in previous:
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
        path = []
        current: str | None = goal

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        return path
