from pathlib import Path

import pytest

from fly_in.models import MapGraph
from fly_in.parser import parse_map
from fly_in.visualizer import (
    TerminalVisualizer,
    visualize_result,
    write_simulation_output,
)


def make_graph() -> MapGraph:
    return parse_map(
        """
        nb_drones: 1
        start_hub: start 0 0
        end_hub: goal 1 0
        connection: start-goal
        """
    )


def test_terminal_visualizer_formats_moves_without_color() -> None:
    output = TerminalVisualizer(make_graph(), use_color=False).render_turn(
        "turn 1: D1-goal"
    )

    assert output == "turn 1: D1-goal"


def test_terminal_visualizer_adds_ansi_color() -> None:
    output = TerminalVisualizer(make_graph()).render_turn("turn 1: D1-goal")

    assert "\033[" in output
    assert "D1" in output
    assert "goal" in output


def test_visualize_result_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unknown visualization mode"):
        visualize_result(
            make_graph(),
            {"turns": 0, "delivered": 0, "log": [], "peak_occupancy": {}},
            "text",
        )


def test_write_simulation_output_uses_movement_only_lines(tmp_path: Path) -> None:
    output_path = tmp_path / "moves.txt"

    write_simulation_output(
        ["turn 1: D1-goal", "turn 2: wait", "turn 3: D1-goal"],
        str(output_path),
    )

    assert output_path.read_text(encoding="utf-8") == "D1-goal\n\nD1-goal\n"
