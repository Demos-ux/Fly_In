import time
from argparse import Namespace
from collections.abc import Callable
from pathlib import Path

from graph import Graph
from objects import RouteConfig
from output import SimulationOutput as Output
from parser import ParseError, Parser
from simulation import Simulation


TARGET_TURNS = {
        "01_linear_path.txt": 6,
        "02_simple_fork.txt": 6,
        "03_basic_capacity.txt": 8,
        "01_dead_end_trap.txt": 15,
        "02_circular_loop.txt": 20,
        "03_priority_puzzle.txt": 12,
        "01_maze_nightmare.txt": 45,
        "02_capacity_hell.txt": 60,
        "03_ultimate_challenge.txt": 35,
        "01_the_impossible_dream.txt": 45,
    }


class Application:
    """Coordinate the command-line workflow for one simulation run."""


    def __init__(self, args: Namespace):
        """Store command-line options and initialize the run timer."""
        self.args = args
        self.start_time = time.perf_counter()

    def run(self) -> None:
        """Load the map, run the simulation, and handle its output."""
        config, graph = self._load_map(self.args.map)
        start = self._find_endpoint(config, "start_hub")
        goal = self._find_endpoint(config, "end_hub")

        simulation = Simulation(graph)
        #checks for the visual flag and starts it
        turn_callback = self._create_turn_callback(graph, goal)
        
        lines = simulation.run(start, goal, on_turn=turn_callback)

        if lines is None:
            raise SystemExit("No path exists")

        live_visual = turn_callback is not None
        self._write_or_print_output(
            lines,
            graph,
            goal,
            live_visual,
        )

        if self.args.benchmark:
            self._print_benchmark(config, lines)

    @staticmethod
    def _load_map(path: str) -> tuple[RouteConfig, Graph]:
        """Parse a map file and build its validated graph."""
        try:
            config = Parser(path).parse()
            return config, Graph(config)
        except (OSError, ParseError, ValueError) as error:
            raise SystemExit(f"Map error: {error}") from None

    @staticmethod
    def _find_endpoint(config: RouteConfig, role: str) -> str:
        """Return the name of the zone with the requested role."""
        return next(
            zone.name
            for zone in config.zones.values()
            if zone.role == role
        )

    def _create_turn_callback(
        self,
        graph: Graph,
        goal: str,
    ) -> Callable[[str, int], None] | None:
        """Create the live visualizer callback when visual mode is active."""
        if not self.args.visual:
            return None
        if self.args.output or self.args.benchmark:
            return None

        Output.print_visual_header()

        def show_turn(line: str, turn: int) -> None:
            """Render one simulation turn in the terminal."""
            Output.print_visual_turn(
                line,
                graph,
                goal,
                turn,
                self.args.delay,
            )

        return show_turn

    def _write_or_print_output(
        self,
        lines: list[str],
        graph: Graph,
        goal: str,
        live_visual: bool,
    ) -> None:
        """Write, visualize, or print the simulation result."""
        if self.args.output:
            Output.write_file(self.args.output, lines)
        elif self.args.benchmark or live_visual:
            return
        elif self.args.visual:
            Output.print_visual(lines, graph, goal)
        else:
            Output.print_lines(lines)

    def _print_benchmark(
        self,
        config: RouteConfig,
        lines: list[str],
    ) -> None:
        """Print benchmark statistics for the completed simulation."""
        elapsed = time.perf_counter() - self.start_time
        turns = len(lines)
        target = self._target_for_map(self.args.map)

        if target is None:
            result = "no target defined"
        elif turns <= target:
            result = "within target"
        else:
            result = "above target"

        print(f"map={self.args.map}")
        print(f"drones={config.nb_drones}")
        print(f"turns={turns}")
        print(f"runtime_seconds={elapsed:.6f}")
        print(f"target_turns={target if target is not None else 'n/a'}")
        print(f"result={result}")

    @staticmethod
    def _target_for_map(map_path: str) -> int | None:
        """Return the configured turn target for a map file name."""
        return TARGET_TURNS.get(Path(map_path).name)
