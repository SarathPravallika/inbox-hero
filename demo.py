# cert-aai-2026-06-0061  Sarath Chandra
#
# - The one command a grader runs to see any capability
# - Holds a completed run open so ten demonstrations cost one run of model calls
# - Refuses to start work if the model provider has not been configured

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from constants import Capability, Paths
from utils import heading, rule

def sibling(folder: str, module: str):
    path = str(ROOT / folder)

    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(module)


def keyed() -> None:
    settings = importlib.import_module("config")
    if settings.API_KEY and settings.MODEL:
        return
    print("API_KEY and MODEL both have to be set before inboxHero can put the inbox "
          "through a model.")
    raise SystemExit("Copy .env.example to .env and fill it in, then try again.")


def ensure_run(fresh: bool) -> dict:
    router = importlib.import_module("router")
    if Paths.RUN.exists() and not fresh:
        return router.stored()
    keyed()
    return router.run()


def zeroed(artifact: dict) -> None:
    heading("R1  every message carries one disposition and a reason")
    for decision in artifact["decisions"]:
        print(f"  {decision['id']}  {decision['disposition']:<11} {decision['by']:<6} "
              f"{decision['reason'][:42]}")
    rule()
    print(f"{artifact['messages_processed']} messages, "
          f"{artifact['rule_handled']} by rule, {artifact['model_handled']} by model")
    print(f"undecided: {artifact['messages_processed'] - len(artifact['decisions'])}")


VIEWS = {Capability.R1: zeroed}


def capability(name: str, args) -> None:
    if name not in Capability:
        print(f"There is no capability called {name}")
        raise SystemExit(f"Capabilities: {', '.join(Capability)}")

    artifact = ensure_run(args.fresh)
    view = VIEWS.get(Capability(name))
    if view is None:
        print(f"{name} is not built yet.")
        return
    view(artifact)


def main() -> None:
    parser = argparse.ArgumentParser(prog="inboxhero")
    parser.add_argument("--cap", metavar="ID", help="demonstrate one capability by id")
    parser.add_argument(
        "--all",
        action="store_true",
        help="demonstrate every capability, in the order the manifest lists them",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="rebuild the run from the inbox instead of reading the artifact on disk",
    )
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

    if args.cap:
        capability(args.cap, args)
        return

    if args.all:
        for name in Capability:
            capability(name, args)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
