import time


class SimulationOutput:
    """Format simulation results for terminals and text files."""

    RESET = "\033[0m"
    COLORS = {
        "normal": "\033[37m",
        "priority": "\033[36m",
        "restricted": "\033[35m",
        "goal": "\033[32m",
        "transit": "\033[33m",
    }

    @staticmethod
    def format_movements(movements: list[str]) -> str:
        """Join movement tokens into one space-separated turn line."""
        return " ".join(movements)

    @classmethod
    def print_lines(cls, lines: list[str]) -> None:
        """Print plain simulation lines to the terminal."""
        if lines:
            print("\n".join(lines))

    @classmethod
    def print_visual(cls, lines: list[str], graph, goal: str) -> None:
        """Print all simulation lines with colors and turn labels."""
        cls.print_visual_header()

        for turn, line in enumerate(lines, start=1):
            cls.print_visual_turn(line, graph, goal, turn)

    @classmethod
    def print_visual_header(cls) -> None:
        """Print the color legend used by the visualizer."""
        print(
            "Legend: "
            "normal "
            f"{cls.COLORS['normal']}normal{cls.RESET} | "
            "priority "
            f"{cls.COLORS['priority']}priority{cls.RESET} | "
            "restricted transit "
            f"{cls.COLORS['transit']}in-flight{cls.RESET} | "
            "delivered "
            f"{cls.COLORS['goal']}goal{cls.RESET}"
        )

    @classmethod
    def print_visual_turn(
        cls,
        line: str,
        graph,
        goal: str,
        turn: int,
        delay: float = 0.2,
    ) -> None:
        """Print one colored turn and optionally pause the animation."""
        colored_moves = [
            cls._color_movement(move, graph, goal)
            for move in line.split()
        ]
        print(f"Turn {turn}: " + " ".join(colored_moves), flush=True)
        if delay > 0:
            time.sleep(delay)

    @classmethod
    def _color_movement(cls, movement: str, graph, goal: str) -> str:
        """Color one movement according to its destination state."""
        parts = movement.split("-")
        destination = parts[-1]

        if len(parts) >= 3:
            color = cls.COLORS["transit"]
        elif destination == goal:
            color = cls.COLORS["goal"]
        else:
            zone_type = graph.zone(destination).zone_type
            color = cls.COLORS.get(zone_type, cls.COLORS["normal"])

        return f"{color}{movement}{cls.RESET}"

    @classmethod
    def write_file(cls, filename: str, lines: list[str]) -> None:
        """Write simulation lines to a plain text file."""
        with open(filename, "w") as file:
            file.write("\n".join(lines))
            if lines:
                file.write("\n")
