import argparse

from .engine import SimulationEngine
from .parser import parse_map_file
from .visualizer import visualize_result, write_simulation_output


def main() -> None:
    """Run a map simulation with the selected visualization mode."""

    parser = argparse.ArgumentParser(description="Simulate and visualize drone routes.")
    parser.add_argument("map_file", help="Path to a Fly-In map file")
    parser.add_argument(
        "--visual",
        choices=("terminal", "pygame"),
        default="terminal",
        help="Visualization backend to use",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds between turns (terminal and Pygame)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in terminal mode",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write movement-only simulation output to PATH",
    )
    args = parser.parse_args()

    try:
        graph = parse_map_file(args.map_file)
        result = SimulationEngine(graph).run()
        if args.output:
            write_simulation_output(result["log"], args.output)
        visualize_result(
            graph,
            result,
            args.visual,
            delay=max(args.delay, 0.0),
            use_color=not args.no_color,
        )
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    print(f"Completed in {result['turns']} turns: {result['delivered']} drones delivered.")


if __name__ == "__main__":
    main()
