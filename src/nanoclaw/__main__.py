"""Entry point for python -m nanoclaw."""

import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from nanoclaw.setup import setup_main
        setup_main()
    else:
        from nanoclaw.cli import cli
        cli()


if __name__ == "__main__":
    main()
