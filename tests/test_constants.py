# cert-aai-2026-06-0061  Sarath Chandra

import json
from constants import Capability, Disposition, Paths, Tier
from utils import heading, rule

KEYS = {"id", "thread_id", "from", "to", "subject", "timestamp", "body", "unread"}
COUNT = 100
ORDER = ("R1", "R2", "R3", "R4", "R5", "R6", "X1", "X2", "X3", "X4")

def check_vocabulary() -> list[str]:
    problems = []
    if len(Disposition) != 6:
        problems.append(f"there are {len(Disposition)} dispositions, not 6")
    for value in Disposition:
        if value != value.lower():
            problems.append(f"disposition {value!r} is not lower case")
    if Disposition.ESCALATE == Disposition.QUARANTINE:
        problems.append("escalate and quarantine are the same value")
    if len(Tier) != 3:
        problems.append(f"there are {len(Tier)} tiers, not 3")
    if tuple(Capability) != ORDER:
        problems.append(f"the capability ids are {', '.join(Capability)}, not {', '.join(ORDER)}")
    for vocabulary, stranger in ((Disposition, "nonsense"), (Tier, "D"), (Capability, "R9")):
        try:
            vocabulary(stranger)
            problems.append(f"{vocabulary.__name__} accepted {stranger!r}")
        except ValueError:
            pass
    return problems


def check_inbox() -> list[str]:
    problems = []
    if not Paths.INBOX.exists():
        return [f"there is no inbox at {Paths.INBOX}"]
    try:
        messages = json.loads(Paths.INBOX.read_text())
    except json.JSONDecodeError as exc:
        return [f"the inbox does not parse: {exc}"]
    if not isinstance(messages, list):
        return [f"the inbox is a {type(messages).__name__}, not a list"]
    if len(messages) != COUNT:
        problems.append(f"the inbox holds {len(messages)} messages, not {COUNT}")
    seen = set()
    for position, message in enumerate(messages):
        missing = KEYS - set(message)
        if missing:
            problems.append(f"message {position} is missing {', '.join(sorted(missing))}")
        spare = set(message) - KEYS
        if spare:
            problems.append(f"message {position} carries {', '.join(sorted(spare))}")
        if message.get("id") in seen:
            problems.append(f"message id {message['id']} appears more than once")
        seen.add(message.get("id"))
    return problems


def run() -> bool:
    heading("inboxHero setup check")
    problems = []
    for name, check in (("vocabulary", check_vocabulary), ("inbox", check_inbox)):
        found = check()
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
