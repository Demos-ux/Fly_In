from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from .engine import SimulationResult
from .models import MapGraph


MOVE_PATTERN = re.compile(r"D(\d+)-(.+)")

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_COLORS = {
    "normal": "\033[37m",
    "blocked": "\033[90m",
    "restricted": "\033[31m",
    "priority": "\033[36m",
}


class TerminalVisualizer:
    """Render simulation turns as colored terminal output."""

    def __init__(self, graph: MapGraph, *, use_color: bool = True) -> None:
        self.graph = graph
        self.use_color = use_color

    def _color_zone(self, zone_name: str) -> str:
        zone = self.graph.get_zone(zone_name)
        if not self.use_color:
            return zone_name
        color = ANSI_COLORS.get(zone.zone_type, ANSI_COLORS["normal"])
        return f"{color}{zone_name}{ANSI_RESET}"

    def _format_move(self, move: str) -> str:
        match = MOVE_PATTERN.fullmatch(move)
        if match is None:
            return move
        drone_id, zone_name = match.groups()
        return f"{ANSI_BOLD}D{drone_id}{ANSI_RESET}-{self._color_zone(zone_name)}"

    def render_turn(self, turn_line: str) -> str:
        """Format one engine log line with colored drone and zone names."""

        prefix, _, move_text = turn_line.partition(": ")
        if not self.use_color:
            return f"{prefix}: {move_text}"
        if move_text == "wait":
            return f"{ANSI_BOLD}{prefix}{ANSI_RESET}: wait"
        moves = " ".join(self._format_move(move) for move in move_text.split())
        return f"{ANSI_BOLD}{prefix}{ANSI_RESET}: {moves}"

    def render(self, log: Iterable[str], *, delay: float = 0.0) -> None:
        """Print every simulation turn, optionally pausing between turns."""

        for turn_line in log:
            print(self.render_turn(turn_line))
            if delay > 0:
                time.sleep(delay)


def write_simulation_output(log: Iterable[str], output_path: str) -> None:
    """Write simulation movements to a file in assignment format."""

    with Path(output_path).open("w", encoding="utf-8") as output_file:
        for turn_line in log:
            _, separator, move_text = turn_line.partition(": ")
            if not separator:
                raise ValueError(f"Invalid simulation log line: {turn_line}")
            output_file.write(move_text if move_text != "wait" else "")
            output_file.write("\n")


class PygameVisualizer:
    """Replay a simulation on a simple coordinate-based Pygame canvas."""

    def __init__(
        self,
        graph: MapGraph,
        *,
        width: int = 1100,
        height: int = 720,
        delay: float = 0.35,
    ) -> None:
        self.graph = graph
        self.width = width
        self.height = height
        self.delay = delay

    def _positions(self) -> Dict[str, Tuple[int, int]]:
        coordinates = [(zone.x, zone.y) for zone in self.graph.zones.values()]
        min_x = min(x for x, _ in coordinates)
        max_x = max(x for x, _ in coordinates)
        min_y = min(y for _, y in coordinates)
        max_y = max(y for _, y in coordinates)
        span_x = max(max_x - min_x, 1)
        span_y = max(max_y - min_y, 1)
        margin = 80
        usable_width = self.width - 2 * margin
        usable_height = self.height - 2 * margin

        return {
            zone.name: (
                margin + int((zone.x - min_x) * usable_width / span_x),
                self.height - margin - int((zone.y - min_y) * usable_height / span_y),
            )
            for zone in self.graph.zones.values()
        }

    def _load_pygame(self) -> Any:
        try:
            import pygame
        except ImportError as error:
            raise RuntimeError(
                "Pygame mode requires pygame. Install it with: python3 -m pip install pygame"
            ) from error
        return pygame

    def _draw_graph(
        self,
        pygame: Any,
        screen: Any,
        positions: Dict[str, Tuple[int, int]],
    ) -> None:
        screen.fill((18, 24, 32))
        for connection in self.graph.connections.values():
            start = positions[connection.zone_a]
            end = positions[connection.zone_b]
            pygame.draw.line(screen, (75, 88, 105), start, end, 3)

        zone_colors = {
            "normal": (190, 198, 210),
            "blocked": (75, 80, 88),
            "restricted": (235, 88, 88),
            "priority": (69, 205, 202),
        }
        for zone in self.graph.zones.values():
            color = zone_colors.get(zone.zone_type, zone_colors["normal"])
            pygame.draw.circle(screen, color, positions[zone.name], 18)
            label = pygame.font.Font(None, 20).render(zone.name, True, (235, 240, 245))
            screen.blit(label, (positions[zone.name][0] - label.get_width() // 2, positions[zone.name][1] + 25))

    def _draw_drones(
        self,
        pygame: Any,
        screen: Any,
        positions: Dict[str, Tuple[int, int]],
        drones: Dict[int, str],
    ) -> None:
        for drone_id, zone_name in drones.items():
            if zone_name not in positions:
                continue
            x, y = positions[zone_name]
            offset = ((drone_id - 1) % 5 - 2) * 9
            pygame.draw.circle(screen, (255, 206, 76), (x + offset, y - 9), 7)
            label = pygame.font.Font(None, 16).render(f"D{drone_id}", True, (20, 24, 30))
            screen.blit(label, (x + offset - label.get_width() // 2, y - 15))

    def replay(self, log: Iterable[str]) -> None:
        """Open a window and replay the supplied simulation log."""

        pygame = self._load_pygame()
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Fly-In drone simulation")
        clock = pygame.time.Clock()
        positions = self._positions()
        drones = {
            drone_id: self.graph.start_name
            for drone_id in range(1, self.graph.nb_drones + 1)
        }

        try:
            for turn_line in log:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                _, _, move_text = turn_line.partition(": ")
                for move in move_text.split():
                    match = MOVE_PATTERN.fullmatch(move)
                    if match is not None:
                        drone_id, zone_name = match.groups()
                        drones[int(drone_id)] = zone_name
                self._draw_graph(pygame, screen, positions)
                self._draw_drones(pygame, screen, positions, drones)
                pygame.display.flip()
                clock.tick(max(1, int(1 / self.delay)))
        finally:
            pygame.quit()


def visualize_result(
    graph: MapGraph,
    result: SimulationResult,
    mode: str,
    *,
    delay: float = 0.0,
    use_color: bool = True,
) -> None:
    """Render a simulation result in terminal or Pygame mode."""

    if mode == "terminal":
        TerminalVisualizer(graph, use_color=use_color).render(result["log"], delay=delay)
    elif mode == "pygame":
        PygameVisualizer(graph, delay=max(delay, 0.05)).replay(result["log"])
    else:
        raise ValueError(f"Unknown visualization mode: {mode}")
