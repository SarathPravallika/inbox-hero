# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves every line of an account carries the file it was read from, so nothing is asserted
# - Proves the account invents no message id that is not really in the mailbox
# - Proves a message the system did nothing with is still explained, and says why not
# - Proves the trace stamps every line with when it was written and a payload cannot
#   overwrite that, which is what makes a timestamp in an account mean anything

import inspect
import json
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

import tracing
import why
from constants import Disposition, Memory, Paths, Trace, Why
from router import stored
from store import load
from utils import heading, rule

HOSTILE = "m024"
DRAFTED = "m043"
REFUSED = "m008"
BY_RULE = "m096"
STATES = "m041"
COPIED = "m018"
DERIVED = "m040"
ABSENT = "m999"
FILES = {Why.MAILBOX: Paths.MAILBOX, Why.APPROVALS: Paths.APPROVALS,
         Why.TRACE: Paths.TRACE, "run.json": Paths.RUN}
LOOKS_LIKE_AN_ID = r"\bm\d{3}\b"


@contextmanager
def elsewhere():
    held = Paths.TRACE
    with tempfile.TemporaryDirectory() as room:
        Paths.TRACE = Path(room) / "trace.jsonl"
        try:
            yield Paths.TRACE
        finally:
            Paths.TRACE = held


def spoken(told) -> str:
    return " ".join(told.lines)


def whole(name: str, artifact, store) -> str:
    return " ".join(f"{one.label} {spoken(one)} {one.source}"
                    for one in why.account(name, artifact, store))


def check_sourced(artifact, store) -> list[str]:
    problems = []
    for name in (HOSTILE, DRAFTED, REFUSED, BY_RULE, STATES, COPIED):
        told = why.account(name, artifact, store)
        if len(told) != 8:
            problems.append(f"{name} was accounted for in {len(told)} sections, not 8")
        for one in told:
            if not one.lines or not all(one.lines):
                problems.append(f"{name}'s {one.label} section says nothing")
            if not one.source:
                problems.append(f"{name}'s {one.label} section names no file")
            held = FILES.get(one.source.split(",")[0])
            if held is None:
                problems.append(f"{name}'s {one.label} cites {one.source!r}, not a file we read")
            elif not held.exists():
                problems.append(f"{name}'s {one.label} cites {held.name}, which is not there")
        if len(why.files(told)) != len(FILES):
            problems.append(f"{name} was answered from {len(why.files(told))} files, not 4")
    return problems


def check_invents_nothing(artifact, store) -> list[str]:
    problems = []
    for name in (HOSTILE, DRAFTED, REFUSED, BY_RULE, STATES, COPIED, DERIVED):
        for found in set(re.findall(LOOKS_LIKE_AN_ID, whole(name, artifact, store))):
            if found not in store.ids:
                problems.append(f"{name}'s account names {found}, which is not in the mailbox")
    return problems


def check_guard(artifact, store) -> list[str]:
    problems = []
    said = whole(HOSTILE, artifact, store)
    for wanted in (str(Disposition.QUARANTINE), "forward", "archive@mail-backup-service.info",
                   Why.OFF_CALENDAR):
        if wanted not in said:
            problems.append(f"{HOSTILE}'s account does not mention {wanted!r}")
    if Why.UNTOUCHED in said:
        problems.append(f"{HOSTILE} was caught by the guard and the account says it was not")
    if Why.UNTOUCHED not in whole(STATES, artifact, store):
        problems.append(f"{STATES} was left alone by the guard and the account does not say so")
    return problems


def check_replies(artifact, store) -> list[str]:
    problems = []
    if "citing m041" not in whole(DRAFTED, artifact, store):
        problems.append(f"{DRAFTED} was drafted citing m041 and the account does not say so")
    if "m003" not in whole(REFUSED, artifact, store):
        problems.append(f"{REFUSED} was refused over m003 and the account does not name it")

    quiet = why.account(BY_RULE, artifact, store)[3]
    if not spoken(quiet).startswith("only mail disposed reply"):
        problems.append(f"{BY_RULE} got no draft and the account does not say why not: "
                        f"{spoken(quiet)!r}")
    if why.disposed(BY_RULE, artifact) not in spoken(quiet):
        problems.append(f"{BY_RULE}'s reply section does not name what it was disposed instead")
    return problems


def check_standing(artifact, store) -> list[str]:
    problems = []
    if "11:00am" not in whole(STATES, artifact, store):
        problems.append(f"{STATES} is where the calendar rule was recorded and it is not shown")
    said = whole(COPIED, artifact, store)
    for wanted in ("priya@paperjet.io", Memory.SOURCE.format(id="m015")):
        if wanted not in said:
            problems.append(f"{COPIED} was copied and the account does not name {wanted}")
    if Why.NO_PREFERENCE in said:
        problems.append(f"{COPIED} was handled under a preference and reads as untouched")
    return problems


def check_calendar(artifact, store) -> list[str]:
    problems = []
    if "2026-09-16" not in whole(DERIVED, artifact, store):
        problems.append(f"{DERIVED} is on the calendar for the 16th and the account omits it")
    told = why.account(DERIVED, artifact, store)[4]
    if told.source != Why.RUN.format(part="commitments[]"):
        problems.append(f"the calendar section reads from {told.source!r}")
    return problems


def check_unknown(artifact, store) -> list[str]:
    problems = []
    if why.known(ABSENT, artifact, store):
        problems.append(f"{ABSENT} is in no mailbox and no run, and was treated as known")
    for name in (HOSTILE, BY_RULE):
        if not why.known(name, artifact, store):
            problems.append(f"{name} is in the mailbox and was treated as unknown")
    wanted = why.suggestions(artifact)
    for name in wanted:
        if name not in store.ids:
            problems.append(f"{name} is offered as somewhere to start and is not a message")
    if len(set(wanted)) != len(wanted):
        problems.append(f"the same message is offered twice: {wanted}")
    return problems


def check_reads_only() -> list[str]:
    problems = []
    source = inspect.getsource(why)
    for reached in ("llm", "prompts", "ask("):
        if reached in source:
            problems.append(f"why.py mentions {reached!r} and is meant to ask nothing")
    for one in (why.arrived, why.decided, why.drafted, why.dated):
        if "ask" in inspect.signature(one).parameters:
            problems.append(f"why.{one.__name__} takes a model to answer with")
    return problems


def check_envelope() -> list[str]:
    problems = []
    with elsewhere() as trace:
        tracing.start()
        tracing.record("X4", "checking", id="m001", clock="09:00")
        for name in Trace.RESERVED:
            try:
                tracing.record("X4", "checking", **{name: "overwritten"})
            except (TypeError, ValueError):
                continue
            problems.append(f"a payload was allowed to write over the trace's own {name}")
        written = [json.loads(line) for line in trace.read_text().splitlines() if line]
    if len(written) != 1:
        problems.append(f"{len(written)} lines were written, not 1")
    if written and not written[0]["at"].startswith("20"):
        problems.append(f"a traced line carries {written[0]['at']!r} as when it happened")
    for one in tracing.events():
        if not set(Trace.RESERVED) <= set(one):
            problems.append(f"a line in the committed trace is missing {Trace.RESERVED}")
    return problems


def run() -> bool:
    heading("inboxHero why check")
    artifact, store = stored(), load()
    problems = []
    for name, found in (("sourced", check_sourced(artifact, store)),
                        ("invents nothing", check_invents_nothing(artifact, store)),
                        ("guard", check_guard(artifact, store)),
                        ("replies", check_replies(artifact, store)),
                        ("standing", check_standing(artifact, store)),
                        ("calendar", check_calendar(artifact, store)),
                        ("unknown", check_unknown(artifact, store)),
                        ("reads only", check_reads_only()),
                        ("trace envelope", check_envelope())):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
