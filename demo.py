# cert-aai-2026-06-0061  Sarath Chandra

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

def sibling(folder: str, module: str):
    path = str(ROOT / folder)

    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(module)


def main() -> None:
    parser = argparse.ArgumentParser(prog="inboxhero")
    parser.add_argument(
        "--test",
        nargs="?",
        const="all",
        metavar="SUITE",
        help="run one suite by name, or every suite when no name is given",
    )

    args = parser.parse_args()

    if args.test:
        raise SystemExit(0 if sibling("tests", "runner").run(args.test) else 1)

    parser.print_help()

if __name__ == "__main__":
    main()
