# cert-aai-2026-06-0061  Sarath Chandra

import re
from constants import Decided, Disposition
from router import build, counted, sorted_out
from store import load
from utils import heading, rule

COUNT = 100
BY_RULE = 56
BY_MODEL = 44

def fake(skip=()):
    def ask(system, text, shape):
        names = re.findall(r'<message id="(m\d+)"', text)
        return [{"id": name, "disposition": "reply", "reason": "answered by the fake"}
                for name in names if name not in skip]
    return ask


def check_coverage(store, decisions) -> list[str]:
    problems = []
    if len(decisions) != COUNT:
        problems.append(f"{len(decisions)} decisions for {COUNT} messages")
    if [d.id for d in decisions] != [m.id for m in store.messages]:
        problems.append("the decisions are not one per message in store order")
    for decision in decisions:
        if decision.disposition not in tuple(Disposition):
            problems.append(f"{decision.id} carries {decision.disposition!r}")
        if not decision.reason:
            problems.append(f"{decision.id} carries no reason")
    return problems


def check_split(decisions) -> list[str]:
    problems = []
    if counted(decisions, Decided.RULE) != BY_RULE:
        problems.append(f"{counted(decisions, Decided.RULE)} by rule, not {BY_RULE}")
    if counted(decisions, Decided.MODEL) != BY_MODEL:
        problems.append(f"{counted(decisions, Decided.MODEL)} by model, not {BY_MODEL}")
    return problems


def check_silent_model(store) -> list[str]:
    problems = []
    decisions = sorted_out(store, ask=fake(skip=("m008", "m010")))
    if len(decisions) != COUNT:
        problems.append("a silent model left the run short of a decision")
    found = {d.id: d for d in decisions}
    for name in ("m008", "m010"):
        if found[name].disposition is not Disposition.ESCALATE:
            problems.append(f"{name} was skipped by the model but not escalated")
    return problems


def check_artifact(store, decisions) -> list[str]:
    problems = []
    artifact = build(store, decisions, "fake", "fake-model")
    if artifact["messages_processed"] != COUNT:
        problems.append(f"the artifact says {artifact['messages_processed']} messages")
    if artifact["rule_handled"] != BY_RULE:
        problems.append(f"the artifact says {artifact['rule_handled']} by rule")
    if len(artifact["decisions"]) != COUNT:
        problems.append("the artifact lost a decision")
    for row in artifact["decisions"]:
        if set(row) != {"id", "disposition", "reason", "by"}:
            problems.append(f"{row.get('id')} has fields {', '.join(sorted(row))}")
            break
        if not isinstance(row["disposition"], str):
            problems.append(f"{row['id']} disposition is not plain text in the artifact")
            break
    return problems


def run() -> bool:
    heading("inboxHero router check")
    store = load()
    decisions = sorted_out(store, ask=fake())

    problems = []
    for name, found in (("coverage", check_coverage(store, decisions)),
                        ("split", check_split(decisions)),
                        ("silent model", check_silent_model(store)),
                        ("artifact", check_artifact(store, decisions))):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(decisions)} decisions, undecided {COUNT - len(decisions)}, "
          f"{len(problems)} problems")
    return not problems
