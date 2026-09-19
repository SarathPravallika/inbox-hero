# cert-aai-2026-06-0061  Sarath Chandra
#
# - Runs the checks and reports which passed

import importlib
from utils import heading, rule

SUITES = ("test_constants", "test_store", "test_rules", "test_classify", "test_router",
          "test_drafts", "test_gate", "test_memory", "test_guard")

def load(name: str):
    return importlib.import_module(name)

def run(choice: str) -> bool:
    names = list(SUITES) if choice == "all" else [choice]
    unknown = [name for name in names if name not in SUITES]
    if unknown:
        print(f"There is no suite called {unknown[0]}")
        print(f"Available suites: {', '.join(SUITES)}")
        return False
    outcomes = []
    for position, name in enumerate(names):
        if position:
            print()
        outcomes.append((name, load(name).run()))
    if len(outcomes) > 1:
        print()
        heading("Test summary")
        for name, good in outcomes:
            print(f"  {'pass' if good else 'FAIL'}  {name}")
        rule()
        failed = [name for name, good in outcomes if not good]
        print(f"{len(outcomes) - len(failed)}/{len(outcomes)} suites passed")
    return all(good for _, good in outcomes)
