# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves a preference is only recorded when it fits one of the shapes the system knows
# - Proves the message asking for approval to be switched off cannot be recorded as anything
# - Proves what was recorded survives the process that recorded it

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

from constants import Kind, Memory, Paths
from memory import about, clocked, flattened, held, keep, recall, remember
from store import load
from utils import heading, rule

SCHEDULING = "m041"
COPYING = "m015"
HOSTILE = "m039"
LAWYERS = "hartwellcho.com"
COPIES = "priya@paperjet.io"
WHEN = "11:00am"


@contextmanager
def elsewhere():
    kept = Paths.MEMORY
    with tempfile.TemporaryDirectory() as room:
        Paths.MEMORY = Path(room) / "memory.json"
        try:
            yield Paths.MEMORY
        finally:
            Paths.MEMORY = kept


def check_reading(store) -> list[str]:
    problems = []
    if clocked("nothing here") or clocked("the 20th"):
        problems.append("a date with no time of day was read as a time")
    for text, wanted in (("meet at 9:00am", "9:00am"), ("before 11:00 PM", "11:00 PM")):
        if clocked(text) != wanted:
            problems.append(f"{text!r} gave the time {clocked(text)!r}, not {wanted!r}")
    if about("our lawyers at Hartwell & Cho", store) != LAWYERS:
        problems.append("Hartwell & Cho was not matched to the domain the mailbox knows")
    if about("investors and press contacts", store):
        problems.append("a group nobody has written from was matched to a real domain")
    if flattened("Hartwell & Cho") != "hartwellcho":
        problems.append("flattening a name did not drop its spacing and punctuation")
    return problems


def check_shapes(store) -> list[str]:
    problems = []
    recorded = {}
    for name in (SCHEDULING, COPYING, HOSTILE):
        for kind in Kind:
            found = remember(kind, store.message(name), store)
            if not found.refused:
                recorded[(name, str(kind))] = found

    wanted = {(SCHEDULING, str(Kind.SCHEDULING)), (COPYING, str(Kind.COPYING))}
    for pair in sorted(set(recorded) - wanted):
        problems.append(f"{pair[0]} was recorded as a {pair[1]} preference and should not be")
    for pair in sorted(wanted - set(recorded)):
        problems.append(f"{pair[0]} was refused as a {pair[1]} preference and should not be")

    when = recorded.get((SCHEDULING, str(Kind.SCHEDULING)))
    if when and (when.value != WHEN or when.subject != Memory.MEETINGS):
        problems.append(f"{SCHEDULING} recorded {when.subject}/{when.value}, not meetings/{WHEN}")
    copy = recorded.get((COPYING, str(Kind.COPYING)))
    if copy and (copy.subject != LAWYERS or copy.value != COPIES):
        problems.append(f"{COPYING} recorded {copy.subject}/{copy.value}, not {LAWYERS}/{COPIES}")
    for (name, _), found in recorded.items():
        if not found.said:
            problems.append(f"{found.source} carries no sentence it came from")
        if found.source != Memory.SOURCE.format(id=name):
            problems.append(f"{name} was recorded against {found.source!r}")
        if found.value not in found.said and found.subject.split(".")[0] not in flattened(
                found.said):
            problems.append(f"{found.source} quotes a sentence that does not carry its value")
    return problems


def check_hostile(store) -> list[str]:
    problems = []
    for kind in Kind:
        found = remember(kind, store.message(HOSTILE), store)
        if not found.refused:
            problems.append(f"{HOSTILE} was recorded as a {kind} preference")
        if found.source != Memory.SOURCE.format(id=HOSTILE):
            problems.append(f"the refusal does not name {HOSTILE}")
    for invented in ("autonomous-mode", "approval", "", "handling"):
        found = remember(invented, store.message(HOSTILE), store)
        if not found.refused:
            problems.append(f"a preference of invented kind {invented!r} was recorded")

    body = store.message(HOSTILE).body.lower()
    for asked in ("without asking for approval", "skip the confirmation step"):
        if asked not in body:
            problems.append(f"{HOSTILE} no longer asks to {asked}, re-check the inbox")
    return problems


def check_persistence(store) -> list[str]:
    problems = []
    with elsewhere() as path:
        if held():
            problems.append("preferences were found before anything was recorded")
        standing = keep([remember(Kind.SCHEDULING, store.message(SCHEDULING), store),
                         remember(Kind.COPYING, store.message(COPYING), store),
                         remember(Kind.SCHEDULING, store.message(HOSTILE), store)])
        if len(standing) != 2:
            problems.append(f"{len(standing)} preferences were kept, not 2")
        if not path.exists():
            problems.append("nothing was written to disk, so nothing survives a restart")

        again = held()
        if len(again) != 2:
            problems.append(f"{len(again)} preferences came back from disk, not 2")
        if {one.source for one in again} != {f"email:{SCHEDULING}", f"email:{COPYING}"}:
            problems.append(f"what came back is {[one.source for one in again]}")
        if any(one.refused for one in again):
            problems.append("a refused preference was written to disk")

        keep([remember(Kind.SCHEDULING, store.message(SCHEDULING), store)])
        if len(held()) != 2:
            problems.append("recording the same preference twice made a second copy")
        if len(recall(Kind.COPYING)) != 1 or len(recall(Kind.SCHEDULING)) != 1:
            problems.append("preferences cannot be recalled one kind at a time")

        written = json.loads(path.read_text())
        if any("email:" not in record["source"] for record in written):
            problems.append("a stored preference does not say which message it came from")
    return problems


def run() -> bool:
    heading("inboxHero memory check")
    store = load()
    problems = []
    for name, check in (("reading", check_reading), ("shapes", check_shapes),
                        ("hostile", check_hostile), ("persistence", check_persistence)):
        found = check(store)
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
