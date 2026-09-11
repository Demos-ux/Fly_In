from application import Application
from cli import parse_args


def main() -> None:
    """Start the command-line application."""
    Application(parse_args()).run()


if __name__ == "__main__":
    main()
