# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves a full run covers every message once and records it faithfully

import re
from constants import Decided, Disposition, Drafts, Kind
from memory import remember
from router import build, claimed, counted, replies, sorted_out
from store import load
from utils import heading, rule

COUNT = 100
BY_RULE = 56
BY_MODEL = 44
LEGAL = {"m018", "m048", "m055"}
COPIES = "priya@paperjet.io"
STANDING = ()

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


def check_drafts(store, decisions) -> list[str]:
    problems = []
    wanted = [d.id for d in decisions if d.disposition is Disposition.REPLY]
    made = replies(store, decisions, STANDING, ask=lambda system, text, shape:
                   {"body": "drafted by the fake", "cited": ["m010"]})
    if [d.id for d in made] != wanted:
        problems.append("a reply was left without a draft or refusal")
    for draft in made:
        if not draft.body and not draft.refused:
            problems.append(f"{draft.id} has neither a body nor a reason for refusing")
        if draft.body and not draft.cited:
            problems.append(f"{draft.id} was drafted without citing anything")
        for name in draft.cited:
            if name not in store.ids:
                problems.append(f"{draft.id} cited {name}, which is not in the inbox")
    if not any(d.refused == Drafts.UNGROUNDED for d in made):
        problems.append("no reply was refused for want of anything to ground on")
    return problems


def check_artifact(store, decisions) -> list[str]:
    problems = []
    standing = (remember(Kind.COPYING, store.message("m015"), store),)
    made = replies(store, decisions, STANDING, ask=lambda system, text, shape:
                   {"body": "drafted by the fake", "cited": ["m010"]})
    recorded = claimed(store, decisions)
    artifact = build(store, decisions, made, standing, recorded, "fake", "fake-model")
    if len(artifact["drafts"]) != len(made):
        problems.append("the artifact lost a draft")
    for row in artifact["drafts"]:
        if set(row) != {"id", "body", "cited", "refused", "dropped"}:
            problems.append(f"draft {row.get('id')} has fields {', '.join(sorted(row))}")
            break
    lawyers = [row for row in artifact["decisions"] if row["copy"]]
    if {row["id"] for row in lawyers} != LEGAL:
        problems.append(f"the copying rule reached {sorted(row['id'] for row in lawyers)}")
    if any(row["copy"] != [COPIES] for row in lawyers):
        problems.append(f"a legal message is copied to somebody other than {COPIES}")
    if artifact["messages_processed"] != COUNT:
        problems.append(f"the artifact says {artifact['messages_processed']} messages")
    if artifact["rule_handled"] != BY_RULE:
        problems.append(f"the artifact says {artifact['rule_handled']} by rule")
    if len(artifact["decisions"]) != COUNT:
        problems.append("the artifact lost a decision")
    for row in artifact["decisions"]:
        if set(row) != {"id", "disposition", "reason", "by", "copy"}:
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
                        ("drafts", check_drafts(store, decisions)),
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
