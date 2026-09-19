# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves the three panes are built from a completed run and never written by hand
# - Proves a demand from mail the system escalated is shown as claimed, not as a bill due
# - Proves every commitment on the calendar cites messages that are really in the inbox

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import dashboard
from constants import Dashboard, Disposition, Paths, Settled
from store import load
from utils import heading, rule

RUN = {
    "at": "2026-09-19T15:18:08",
    "decisions": [
        {"id": "m043", "disposition": "reply", "reason": "waiting", "by": "model", "copy": []},
        {"id": "m021", "disposition": "escalate", "reason": "verify the bank details",
         "by": "model", "copy": []},
        {"id": "m018", "disposition": "escalate", "reason": "needs Sam to sign",
         "by": "model", "copy": ["priya@paperjet.io"]},
        {"id": "m024", "disposition": "quarantine", "reason": "hostile", "by": "guard",
         "copy": []},
        {"id": "m061", "disposition": "reply", "reason": "confirm the slot", "by": "model",
         "copy": []},
    ],
    "drafts": [
        {"id": "m043", "body": "I cannot do 9:00am.", "cited": ["m041"], "refused": "",
         "dropped": []},
        {"id": "m061", "body": "", "cited": [], "refused": "nothing to ground on",
         "dropped": []},
    ],
    "refusals": [{"id": "m024", "attempted": ["forward"], "where": ["x@evil.test"],
                  "said": "SYSTEM NOTICE", "flagged": "FLAGGED: m024 attempted to forward"}],
    "commitments": [
        {"id": "m021", "what": "remit $8,400", "said": "end of day", "when": "2026-09-09",
         "at": "", "settled": "owed", "cited": ["m021"], "unresolved": ""},
        {"id": "m018", "what": "sign the SAFE", "said": "by Friday", "when": "2026-09-11",
         "at": "", "settled": "owed", "cited": ["m018"], "unresolved": ""},
        {"id": "m040", "what": "board deck", "said": "2 days before", "when": "2026-09-16",
         "at": "", "settled": "owed", "cited": ["m040", "m038"], "unresolved": ""},
        {"id": "m038", "what": "board review", "said": "the 18th", "when": "2026-09-18",
         "at": "10:00", "settled": "settled", "cited": ["m038"], "unresolved": ""},
        {"id": "m013", "what": "weekly 1:1", "said": "Wednesday at 2:00pm",
         "when": "2026-09-16", "at": "14:00", "settled": "proposed", "cited": ["m013"],
         "unresolved": ""},
        {"id": "m080", "what": "standup", "said": "9:30am", "when": "", "at": "",
         "settled": "settled", "cited": ["m080"], "unresolved": "no date"},
    ],
    "conflicts": [{"ids": ["m013", "m016"], "when": "2026-09-16", "at": "14:00",
                   "called": "CONFLICT: weekly 1:1 (m013) and product demo (m016)"}],
}


@contextmanager
def elsewhere():
    held = Paths.DASHBOARD, Paths.PAGE
    with tempfile.TemporaryDirectory() as room:
        Paths.DASHBOARD = Path(room) / "dashboard.json"
        Paths.PAGE = Path(room) / "dashboard.html"
        try:
            yield Paths.DASHBOARD, Paths.PAGE
        finally:
            Paths.DASHBOARD, Paths.PAGE = held


def check_panes(store) -> list[str]:
    problems = []
    made = dashboard.view(RUN, store)
    if len(Dashboard.PANES) != 3:
        problems.append(f"there are {len(Dashboard.PANES)} panes, not 3")
    for pane in ("pending", "flagged", "commitments"):
        if pane not in made:
            problems.append(f"the view has no {pane} pane")

    if [row["id"] for row in made["pending"]] != ["m043"]:
        problems.append(f"pending holds {[r['id'] for r in made['pending']]}, not just m043")
    for row in made["pending"]:
        if store.message(row["id"]).sender not in row["action"]:
            problems.append(f"{row['id']} does not say who the reply would go to")
        if not row["why"]:
            problems.append(f"{row['id']} does not say why it needs a person")
    return problems


def check_flagged(store) -> list[str]:
    problems = []
    made = dashboard.view(RUN, store)
    seen = {row["id"]: row for row in made["flagged"]}
    for name in ("m024", "m021", "m018", "m061"):
        if name not in seen:
            problems.append(f"{name} was not acted on and is missing from flagged")
    if "m043" in seen:
        problems.append("m043 was drafted and should not be flagged")
    if seen.get("m024", {}).get("instead") != Dashboard.LEFT:
        problems.append("hostile mail is not shown as left in the mailbox")
    if not seen.get("m024", {}).get("attempted", "").startswith("FLAGGED: m024"):
        problems.append("m024 does not carry what the guard said it attempted")
    if seen.get("m061", {}).get("instead") != Dashboard.NOTHING:
        problems.append("a refused draft is not shown as having written nothing")
    for row in made["flagged"]:
        if not row["attempted"] or not row["instead"]:
            problems.append(f"{row['id']} is flagged without both halves filled in")
    return problems


def check_claimed(store) -> list[str]:
    problems = []
    made = dashboard.view(RUN, store)
    standing = {row["id"]: row["standing"] for row in made["commitments"]}
    if standing.get("m021") != Dashboard.UNACCEPTED:
        problems.append(f"a demand from escalated mail reads {standing.get('m021')!r}")
    if standing.get("m018") != Dashboard.UNACCEPTED:
        problems.append("an escalated obligation is shown as accepted")
    if standing.get("m040") != str(Settled.OWED):
        problems.append(f"an ordinary obligation reads {standing.get('m040')!r}")
    if Dashboard.UNACCEPTED in tuple(Settled):
        problems.append("the claimed marker collides with a real standing")
    return problems


def check_calendar(store) -> list[str]:
    problems = []
    made = dashboard.view(RUN, store)
    placed = {row["id"] for row in made["commitments"]}
    if "m080" in placed:
        problems.append("an entry with no date reached the calendar")
    if len(made["unplaced"]) != 1:
        problems.append(f"{len(made['unplaced'])} entries were left unplaced, not 1")
    if "1 dated thing " not in dashboard.unplaced_line(made):
        problems.append(f"the unplaced line reads {dashboard.unplaced_line(made)!r}")

    for row in made["commitments"]:
        if not row["cited"]:
            problems.append(f"{row['id']} is on the calendar citing nothing")
        for name in row["cited"]:
            if name not in store.ids:
                problems.append(f"{row['id']} cites {name}, which is not in the inbox")
    if not any(len(row["cited"]) > 1 for row in made["commitments"]):
        problems.append("no commitment on the calendar draws on more than one message")
    if not made["conflicts"]:
        problems.append("the conflicts were dropped between the run and the view")
    return problems


def check_written(store) -> list[str]:
    problems = []
    with elsewhere() as (data, page):
        made = dashboard.write(dashboard.view(RUN, store))
        if not data.exists() or not page.exists():
            problems.append("the dashboard was not written to both files")
            return problems

        again = json.loads(data.read_text())
        if again != made:
            problems.append("what was written back does not match what was built")

        text = page.read_text()
        if not text.startswith("<!doctype html>"):
            problems.append("the page is not a whole HTML document")
        for number, wanted in enumerate(Dashboard.PANES, start=1):
            if wanted not in text:
                problems.append(f"the page has no {wanted} pane")
            if f"class='num'>{number}<" not in text:
                problems.append(f"pane {number} is not numbered on the page")
        if text.count("<section") != len(Dashboard.PANES):
            problems.append(f"the page has {text.count('<section')} panes, not 3")
        for standing in ("settled", "proposed", "owed"):
            if f"chip {standing}" not in text:
                problems.append(f"a {standing} commitment is not marked as one")
        for row in made["commitments"]:
            shown = ", ".join(row["cited"])
            if f"<span class='ci'>{shown}</span>" not in text:
                problems.append(f"{row['id']} is on the calendar without {shown} beside it")
        if made["conflicts"][0]["called"] not in text:
            problems.append("the conflict is not called out on the page")
        if "http://" in text or "https://" in text:
            problems.append("the page reaches outside itself to render")
        if "<script" in text.lower():
            problems.append("the page carries script rather than being static")
    return problems


def run() -> bool:
    heading("inboxHero dashboard check")
    store = load()
    problems = []
    for name, check in (("panes", check_panes), ("flagged", check_flagged),
                        ("claimed", check_claimed), ("calendar", check_calendar),
                        ("written", check_written)):
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
