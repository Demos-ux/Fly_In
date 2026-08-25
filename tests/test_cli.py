import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_runs_terminal_visualizer() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "fly_in",
            "maps/easy/01_linear_path.txt",
            "--visual",
            "terminal",
            "--no-color",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Completed in 4 turns: 2 drones delivered." in completed.stdout


def test_cli_reports_missing_map() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "fly_in", "maps/missing.txt"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "maps/missing.txt" in completed.stderr
