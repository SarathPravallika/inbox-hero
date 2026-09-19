# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves every date is worked out from the words a message used, with no model involved
# - Proves the board deck lands on the 16th from two messages, neither of which says so
# - Proves two things at the same moment are called out rather than listed quietly

from datetime import date

from commitments import (Commitment, clash, clashes, clocked, dated, gather, joined, merged,
                         placed, read, relative, settled, waiting)
from constants import Commitments, Settled
from store import load
from utils import heading, rule

SAID = (
    ("m038", "quarterly board review", "the 18th, 10:00am", Settled.SETTLED),
    ("m040", "board deck circulated", "two days before the board review", Settled.OWED),
    ("m026", "launch", "the 20th", Settled.SETTLED),
    ("m030", "approve final pricing copy", "by the 12th", Settled.OWED),
    ("m010", "investor intro call", "Tuesday the 15th at 3:00pm", Settled.PROPOSED),
    ("m061", "dental cleaning", "Tuesday, September 15 at 3:00 PM", Settled.SETTLED),
    ("m013", "weekly 1:1 moved", "Wednesday at 2:00pm", Settled.PROPOSED),
    ("m016", "product demo", "Wednesday at 2:00pm", Settled.PROPOSED),
    ("m018", "sign the SAFE", "by Friday", Settled.OWED),
    ("m048", "flag corrections to board minutes", "by Monday", Settled.OWED),
    ("m055", "sign IP assignment", "before month-end", Settled.OWED),
    ("m117", "submit timesheet", "Friday 5pm", Settled.OWED),
)

DATES = {"m038": "2026-09-18", "m040": "2026-09-16", "m026": "2026-09-20",
         "m030": "2026-09-12", "m010": "2026-09-15", "m061": "2026-09-15",
         "m013": "2026-09-16", "m016": "2026-09-16", "m018": "2026-09-11",
         "m048": "2026-09-14", "m055": "2026-09-30", "m117": "2026-09-11"}
TIMES = {"m038": "10:00", "m010": "15:00", "m061": "15:00", "m013": "14:00",
         "m016": "14:00", "m117": "17:00"}
CLASHING = {("m010", "m061"), ("m013", "m016")}
DERIVED = ("m040", ("m040", "m038"))
DATELESS = ("m096", "m003")
TWINS = (("m026", "launch", "the 20th"), ("m036", "the launch", "the 20th"))
PHISHING = ("m021", "m023", "m045")


def resolved():
    raw = [Commitment(id=name, what=what, said=said, settled=str(standing), cited=(name,))
           for name, what, said, standing in SAID]
    return {one.id: one for one in joined(placed(raw))}


def check_snapshot() -> list[str]:
    problems = []
    here = date.fromisoformat(Commitments.TODAY)
    if here.strftime("%A") != "Wednesday":
        problems.append(f"the snapshot {Commitments.TODAY} is a {here.strftime('%A')}")
    for day, name in ((11, "Friday"), (14, "Monday"), (15, "Tuesday"), (16, "Wednesday"),
                      (18, "Friday"), (20, "Sunday")):
        if date(2026, 9, day).strftime("%A") != name:
            problems.append(f"September {day} 2026 is not a {name}")
    return problems


def check_reading() -> list[str]:
    problems = []
    for text, wanted in (("the 18th, 10:00am", "10:00"), ("at 3:00 PM", "15:00"),
                         ("Friday 5pm", "17:00"), ("noon", "")):
        if clocked(text) != wanted:
            problems.append(f"{text!r} gave the time {clocked(text)!r}, not {wanted!r}")
    if settled("nothing datelike here") is not None:
        problems.append("a date was read out of text that has none")
    moved = relative("two days before the board review")
    if moved != (2, "before", "the board review"):
        problems.append(f"the relative phrase read as {moved}")
    if relative("the 18th, 10:00am") is not None:
        problems.append("a plain date was read as a relative one")
    return problems


def check_dates() -> list[str]:
    problems = []
    found = resolved()
    for name, wanted in DATES.items():
        got = found[name].when
        if got != wanted:
            problems.append(f"{name} ({found[name].said!r}) landed on {got or '?'}, not {wanted}")
    for name, wanted in TIMES.items():
        if found[name].at != wanted:
            problems.append(f"{name} is at {found[name].at or '--'}, not {wanted}")
    for one in found.values():
        if one.unresolved:
            problems.append(f"{one.id} could not be placed: {one.unresolved}")
        if one.settled not in tuple(Settled):
            problems.append(f"{one.id} is {one.settled!r}, which is not a standing we know")
    return problems


def check_two_sources() -> list[str]:
    problems = []
    found = resolved()
    name, wanted = DERIVED
    if found[name].cited != wanted:
        problems.append(f"{name} cites {found[name].cited}, not {wanted}")
    if "board review" not in found[name].said:
        problems.append(f"{name} no longer says what it was measured from: {found[name].said!r}")
    if found[name].when >= found["m038"].when:
        problems.append(f"{name} is not earlier than the review it is measured from")
    alone = [one for one in found.values() if len(one.cited) > 1]
    if not alone:
        problems.append("no commitment draws on more than one message")
    for one in found.values():
        for cited in one.cited:
            if cited not in DATES:
                problems.append(f"{one.id} cites {cited}, which carries no date here")
    return problems


def check_twins() -> list[str]:
    problems = []
    raw = [Commitment(id=name, what=what, said=said, settled=str(Settled.SETTLED),
                      cited=(name,)) for name, what, said in TWINS]
    kept = merged(joined(placed(raw)))
    if len(kept) != 1:
        problems.append(f"the same launch in two messages stayed as {len(kept)} entries")
    elif kept[0].cited != ("m026", "m036"):
        problems.append(f"the merged entry cites {kept[0].cited}, not both messages")

    apart = merged(joined(placed([
        Commitment(id="m013", what="weekly 1:1", said="Wednesday at 2:00pm",
                   settled=str(Settled.PROPOSED), cited=("m013",)),
        Commitment(id="m016", what="product demo", said="Wednesday at 2:00pm",
                   settled=str(Settled.PROPOSED), cited=("m016",))])))
    if len(apart) != 2:
        problems.append("two different things in the same slot were merged into one")
    return problems


def check_refused(store) -> list[str]:
    problems = []
    import guard
    import rules
    from constants import Decided, Disposition
    from rules import Decision

    decisions = []
    for message in store.messages:
        made = guard.decide(message) or rules.decide(message)
        if made is None:
            disposed = (Disposition.QUARANTINE if message.id in PHISHING
                        else Disposition.ARCHIVE)
            made = Decision(id=message.id, disposition=disposed, reason="by hand",
                            by=Decided.MODEL)
        decisions.append(made)

    looked = {message.id for message in waiting(store, decisions)}
    for name in PHISHING:
        if name in looked:
            problems.append(f"{name} was refused and its demands still reached the calendar")
    for name in ("m017", "m024", "m039", "m047"):
        if name in looked:
            problems.append(f"{name} is hostile and was read for commitments")
    for name in ("m038", "m040", "m010"):
        if name not in looked:
            problems.append(f"{name} carries a real date and was left out")
    return problems


def check_conflicts() -> list[str]:
    problems = []
    found = resolved()
    pairs = {tuple(sorted((one.id, other.id))) for one, other in clashes(list(found.values()))}
    for wanted in sorted(CLASHING - pairs):
        problems.append(f"{wanted[0]} and {wanted[1]} share a slot and were not called out")
    for extra in sorted(pairs - CLASHING):
        problems.append(f"{extra[0]} and {extra[1]} were called a conflict and are not one")
    for one, other in clashes(list(found.values())):
        said = clash((one, other))
        if not said.startswith("CONFLICT: ") or one.id not in said or other.id not in said:
            problems.append(f"a conflict reads {said!r}")
    return problems


def check_candidates(store) -> list[str]:
    problems = []
    for name in DATES:
        if not dated(store.message(name)):
            problems.append(f"{name} carries a date and the filter did not see one")
    for name in DATELESS:
        if dated(store.message(name)):
            problems.append(f"{name} carries no date and the filter thought it did")

    asked = {"calls": 0}

    def never(system, text, shape):
        asked["calls"] += 1
        return None

    if gather(store, (), ask=never):
        problems.append("a silent model still produced commitments")
    if not asked["calls"]:
        problems.append("nothing was put in front of the model at all")
    return problems


def check_invented(store) -> list[str]:
    problems = []
    made = read([{"id": "m999", "when": "the 18th", "what": "invented", "settled": "settled"},
                 {"id": "m038", "when": "", "what": "nothing", "settled": "settled"},
                 {"id": "m038", "when": "the 18th", "what": "board review", "settled": "maybe"},
                 {"id": "m038", "when": "the 18th", "what": "board review",
                  "settled": "settled"}], store)
    if len(made) != 2:
        problems.append(f"{len(made)} entries survived checking, not 2")
    if any(one.id == "m999" for one in made):
        problems.append("a commitment was kept against a message that does not exist")
    if any(one.settled == "maybe" for one in made):
        problems.append("a standing outside the vocabulary survived")
    return problems


def run() -> bool:
    heading("inboxHero commitments check")
    store = load()
    problems = []
    for name, found in (("snapshot", check_snapshot()), ("reading", check_reading()),
                        ("dates", check_dates()), ("two sources", check_two_sources()),
                        ("twins", check_twins()), ("refused", check_refused(store)),
                        ("conflicts", check_conflicts()),
                        ("candidates", check_candidates(store)),
                        ("invented", check_invented(store))):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
