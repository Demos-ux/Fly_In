import argparse


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the Fly_In simulation."""
    parser = argparse.ArgumentParser(
        description="Run the Fly_In drone simulation."
    )
    parser.add_argument(
        "-m",
        "--map",
        required=True,
        help="Path to the map file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write simulation movements to this file.",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Print simulation benchmark statistics.",
    )
    parser.add_argument(
        "-v",
        "--visual",
        action="store_true",
        help="Show colored drone movements in the terminal.",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.2,
        help="Seconds to wait between visual turns (default: 0.2).",
    )
    return parser.parse_args()
