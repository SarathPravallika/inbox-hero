# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves the one message Sam sent that nobody answered is found, and the three that need
#   no chase each carry the reason they were left alone
# - Proves a chase may only use words his own message used, a form of one, or a nudging word,
#   so nothing can put a deadline or an amount in his mouth that he never wrote
# - Proves nothing the run quarantined is ever chased, because a chase is mail going out

import followups
import guard
import rules
from constants import Decided, Disposition, Followups, Inbox
from rules import Decision
from store import load
from utils import heading, rule

SENT = ("m003", "m044", "m041", "m039")
CHASED = "m044"
WAITED = 7
ANSWERED = ("m003", "m005")
SELF = "m041"
HOSTILE = "m039"
GOOD = "Priya, any update on the contractor invoice approval? It is still blocking payment."
INVENTED = "Priya, I need the invoice approved by Friday or we lose the $8,400."
STRANGER = "m001"


def decided(store) -> list:
    made = []
    for message in store.messages:
        one = guard.decide(message) or rules.decide(message)
        if one is None:
            one = Decision(id=message.id, disposition=Disposition.ARCHIVE,
                           reason="by hand", by=Decided.MODEL)
        made.append(one)
    return made


def check_sent(store) -> list[str]:
    problems = []
    found = tuple(one.id for one in followups.mine(store))
    if set(found) != set(SENT):
        problems.append(f"Sam sent {sorted(found)}, not {sorted(SENT)}")
    for one in followups.mine(store):
        if one.sender.lower() != Inbox.OWNER:
            problems.append(f"{one.id} is not from Sam and was counted as his")
    if followups.waited(store.message(CHASED)) != WAITED:
        problems.append(f"{CHASED} has waited "
                        f"{followups.waited(store.message(CHASED))} days, not {WAITED}")
    return problems


def check_who(store) -> list[str]:
    problems = []
    found = {one.id: one for one in followups.looked(store, decided(store))}
    if set(found) != set(SENT):
        problems.append(f"{sorted(found)} were looked at, not {sorted(SENT)}")

    chasing = sorted(one.id for one in found.values() if one.chased)
    if chasing != [CHASED]:
        problems.append(f"{chasing} would be chased, not just {CHASED}")
    if found[CHASED].why:
        problems.append(f"{CHASED} is being chased and carries a reason not to")

    answered, by = ANSWERED
    if by not in found[answered].why:
        problems.append(f"{answered} was answered by {by} and the reason does not say so")
    if found[SELF].why != Followups.SELF:
        problems.append(f"{SELF} went to Sam himself and reads {found[SELF].why!r}")
    if found[HOSTILE].why != Followups.HELD:
        problems.append(f"{HOSTILE} is quarantined and reads {found[HOSTILE].why!r}")
    for one in found.values():
        if one.chased == bool(one.why):
            problems.append(f"{one.id} is neither plainly chased nor plainly left alone")
    return problems


def check_words(store) -> list[str]:
    problems = []
    if not followups.rooted("approval", {"approve"}):
        problems.append("a grammatical form of a word Sam used was treated as a new word")
    if followups.rooted("friday", {"finance", "invoice"}):
        problems.append("an unrelated word was treated as a form of one Sam used")
    if followups.rooted("pay", {"payment"}):
        problems.append("a word shorter than the root length was let through")

    asked = store.message(CHASED)
    if not followups.nudges(GOOD, asked):
        problems.append(f"a chase built from his own words was refused: {GOOD!r}")
    if followups.nudges(INVENTED, asked):
        problems.append(f"a chase naming a deadline and an amount was allowed: {INVENTED!r}")
    return problems


def check_read(store) -> list[str]:
    problems = []
    written = followups.read([{"id": CHASED, "body": GOOD},
                              {"id": STRANGER, "body": GOOD},
                              {"id": CHASED, "body": ""}], {CHASED}, store)
    if written.get(CHASED) != GOOD:
        problems.append(f"the chase for {CHASED} came back as {written.get(CHASED)!r}")
    if STRANGER in written:
        problems.append(f"a chase was kept for {STRANGER}, which was never put to the model")

    refused = followups.read([{"id": CHASED, "body": INVENTED}], {CHASED}, store)
    if refused.get(CHASED):
        problems.append("a chase that invented a deadline was kept")
    return problems


def check_no_model(store) -> list[str]:
    problems = []
    asked = {"calls": 0}

    def never(system, text, shape):
        asked["calls"] += 1
        return None

    found = {one.id: one for one in followups.gather(store, decided(store), ask=never)}
    if asked["calls"] != 1:
        problems.append(f"{asked['calls']} calls were made for one message to chase")
    if found[CHASED].body:
        problems.append(f"{CHASED} was chased with words a silent model did not write")
    if found[CHASED].refused != Followups.SILENT:
        problems.append(f"{CHASED} reads {found[CHASED].refused!r} with nothing written")
    for name in (SELF, HOSTILE, ANSWERED[0]):
        if found[name].body or found[name].refused:
            problems.append(f"{name} needs no chase and one was written for it anyway")
    return problems


def run() -> bool:
    heading("inboxHero follow-up check")
    store = load()
    problems = []
    for name, found in (("what Sam sent", check_sent(store)),
                        ("who is chased", check_who(store)),
                        ("only his words", check_words(store)),
                        ("reading back", check_read(store)),
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
