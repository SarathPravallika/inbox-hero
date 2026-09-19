# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves a 9:00am that breaks Sam's own rule is answered with three times that do not
# - Proves a 3:00pm that lands on a confirmed appointment moves day rather than time, and
#   that the appointment is what blocked it and is named nowhere in the reply
# - Proves two requests for the same slot are left for Sam, because neither is settled and
#   deciding between them is not the system's to do
# - Proves the model may decline and offer but may never name a time this code did not work out

from dataclasses import replace

import offers
from commitments import Commitment
from constants import Kind, Offers, Settled
from memory import remember
from store import load
from utils import heading, rule

DIARY = (
    ("m043", "meeting with partner", "2026-09-14", "09:00", Settled.PROPOSED),
    ("m010", "Intro call", "2026-09-15", "15:00", Settled.PROPOSED),
    ("m061", "dental cleaning with Dr. Osei", "2026-09-15", "15:00", Settled.SETTLED),
    ("m013", "weekly 1:1", "2026-09-16", "14:00", Settled.PROPOSED),
    ("m016", "product demo", "2026-09-16", "14:00", Settled.PROPOSED),
    ("m038", "quarterly board review", "2026-09-18", "10:00", Settled.SETTLED),
)
COUNTERED = {"m043", "m010"}
LEFT = {"m013", "m016"}
BLOCKER = "m061"
RULE = "m041"
WANTED = {"m043": ("2026-09-14 11:00", "2026-09-14 14:00", "2026-09-14 16:00"),
          "m010": ("2026-09-16 15:00", "2026-09-17 15:00", "2026-09-18 15:00")}
GOOD = ("9:00am will not work I am afraid. Could you do Monday the 14th at 11:00am, "
        "2:00pm or 4:00pm instead?")
LATE = "Could you do Monday the 14th at 11:00am, 2:00pm or 5:00pm instead?"
ELSEWHERE = "Could you do Tuesday the 15th at 11:00am instead?"
LEAKS = ("Tuesday will not work, I have a dental cleaning then. "
         "Could you do Wednesday the 16th at 3:00pm?")
FINE = "Tuesday will not work I am afraid. Could you do Wednesday the 16th at 3:00pm?"


def diary() -> list[Commitment]:
    return [Commitment(id=name, what=what, said=what, when=when, at=at,
                       settled=str(standing), cited=(name,))
            for name, what, when, at, standing in DIARY]


def standing(store) -> tuple:
    return (remember(Kind.SCHEDULING, store.message(RULE), store),)


def made(store) -> dict:
    held, known = diary(), standing(store)
    found = {}
    for one in offers.wanted(held, known):
        slots, blocked = offers.search(one, held, known)
        found[one.id] = replace(one, slots=slots, blocked=blocked)
    return found


def check_which(store) -> list[str]:
    problems = []
    found = made(store)
    if set(found) != COUNTERED:
        problems.append(f"{sorted(found)} were countered, not {sorted(COUNTERED)}")
    for name in LEFT:
        if name in found:
            problems.append(f"{name} is one of two requests for a slot and was answered "
                            f"rather than left for Sam")
    if "before 11:00am" not in found["m043"].because:
        problems.append(f"m043 reads {found['m043'].because!r}, naming no rule")
    if found["m010"].because != Offers.TAKEN:
        problems.append(f"m010 reads {found['m010'].because!r}")
    if found["m043"].cited != (RULE,):
        problems.append(f"m043 cites {found['m043'].cited}, not the rule that ruled it out")
    if found["m010"].cited:
        problems.append(f"m010 cites {found['m010'].cited}, naming what Sam is doing instead")
    return problems


def check_slots(store) -> list[str]:
    problems = []
    found, known = made(store), standing(store)
    for name, wanted in WANTED.items():
        if found[name].slots != wanted:
            problems.append(f"{name} was offered {found[name].slots}, not {wanted}")
        if len(found[name].slots) != Offers.OFFERED:
            problems.append(f"{name} was offered {len(found[name].slots)} times")
        for slot in found[name].slots:
            when, at = slot.split(" ")
            if offers.breaks(at, known)[0]:
                problems.append(f"{name} was offered {slot}, which breaks Sam's own rule")
            if offers.busy(diary(), when, at, name):
                problems.append(f"{name} was offered {slot}, which is already taken")
    if found["m010"].blocked != (BLOCKER,):
        problems.append(f"m010 was blocked by {found['m010'].blocked}, not {BLOCKER}")
    if found["m043"].blocked:
        problems.append(f"m043 was blocked by {found['m043'].blocked}, not by a rule")
    if offers.spoken("2026-09-14 11:00") != "Monday 14 September at 11:00am":
        problems.append(f"a slot reads {offers.spoken('2026-09-14 11:00')!r}")
    return problems


def check_body(store) -> list[str]:
    problems = []
    found, held = made(store), diary()
    if offers.checked(GOOD, found["m043"], held):
        problems.append(f"a reply offering only what it was given was refused: "
                        f"{offers.checked(GOOD, found['m043'], held)}")
    if not offers.checked(LATE, found["m043"], held).startswith("the reply named"):
        problems.append("a reply naming a time that was never offered was allowed")
    if offers.checked(ELSEWHERE, found["m043"], held) != Offers.MISDATED:
        problems.append("a reply naming a day that was never offered was allowed")
    if offers.checked(FINE, found["m010"], held):
        problems.append(f"m010's reply was refused: "
                        f"{offers.checked(FINE, found['m010'], held)}")
    if offers.checked(LEAKS, found["m010"], held) != Offers.DISCLOSED:
        problems.append("a reply saying what the other appointment is was allowed")
    return problems


def check_no_model(store) -> list[str]:
    problems = []
    asked = {"calls": 0}

    def never(system, text, shape):
        asked["calls"] += 1
        return None

    found = {one.id: one for one in
             offers.gather(store, diary(), standing(store), ask=never)}
    if asked["calls"] != 1:
        problems.append(f"{asked['calls']} calls were made for {len(COUNTERED)} counter-offers")
    if set(found) != COUNTERED:
        problems.append(f"a silent model changed who was countered: {sorted(found)}")
    for one in found.values():
        if one.body:
            problems.append(f"{one.id} carries words a silent model did not write")
        if one.refused != Offers.SILENT:
            problems.append(f"{one.id} reads {one.refused!r} with nothing written")
        if len(one.slots) != Offers.OFFERED:
            problems.append(f"{one.id} lost its alternatives when the model went quiet")
        if not one.to:
            problems.append(f"{one.id} does not say who the offer would go to")
    return problems


def run() -> bool:
    heading("inboxHero counter-offer check")
    store = load()
    problems = []
    for name, found in (("which times", check_which(store)),
                        ("what is free", check_slots(store)),
                        ("what it may say", check_body(store)),
                        ("without a model", check_no_model(store))):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
