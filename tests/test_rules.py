# cert-aai-2026-06-0061  Sarath Chandra

from constants import Decided, Disposition, Rules
from rules import decide
from store import load
from utils import heading, rule

HANDLED = 56
LEFT = 44

PLANTED = ("m017", "m021", "m023", "m024", "m045", "m047")
NEEDS_A_PERSON = ("m008", "m012", "m015", "m019", "m041")
ARCHIVABLE = ("m096", "m072", "m104", "m053", "m049", "m057")

def check_counts(store, taken, passed) -> list[str]:
    problems = []
    if len(taken) != HANDLED:
        problems.append(f"{len(taken)} messages went through rules, not {HANDLED}")
    if len(passed) != LEFT:
        problems.append(f"{len(passed)} messages were left for the model, not {LEFT}")
    if len(taken) + len(passed) != len(store):
        problems.append("the rule layer lost or duplicated a message")
    return problems


def check_safety(taken) -> list[str]:
    problems = []
    decided = {decision.id for decision in taken}
    for name in PLANTED:
        if name in decided:
            problems.append(f"{name} is an attack and a rule disposed of it")
    for name in NEEDS_A_PERSON:
        if name in decided:
            problems.append(f"{name} needs judgement and a rule disposed of it")
    return problems


def check_ceiling(store) -> list[str]:
    problems = []
    for name in PLANTED:
        message = store.message(name)
        if len(message.body) <= Rules.BOILERPLATE_LIMIT:
            problems.append(f"{name} is {len(message.body)} characters, inside the ceiling")
    for name in ARCHIVABLE:
        if decide(store.message(name)) is None:
            problems.append(f"{name} is boilerplate and no rule took it")
    return problems


def check_shape(store, taken) -> list[str]:
    problems = []
    for decision in taken:
        if decision.disposition is not Disposition.ARCHIVE:
            problems.append(f"{decision.id} was disposed {decision.disposition}, not archive")
        if decision.by is not Decided.RULE:
            problems.append(f"{decision.id} is marked decided by {decision.by}")
        if not decision.reason:
            problems.append(f"{decision.id} carries no reason")
        if decision.id not in store.ids:
            problems.append(f"{decision.id} is not a message in the inbox")
    return problems


def run() -> bool:
    heading("inboxHero rules check")
    store = load()
    taken, passed = [], []
    for message in store.messages:
        decision = decide(message)
        (taken if decision else passed).append(decision or message)

    problems = []
    for name, found in (("counts", check_counts(store, taken, passed)),
                        ("safety", check_safety(taken)),
                        ("ceiling", check_ceiling(store)),
                        ("shape", check_shape(store, taken))):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(taken)} of {len(store)} handled without a model, {len(problems)} problems")
    return not problems
