# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves the nine-message launch thread comes down to the one message still waiting on Sam
# - Proves the credential Raghav was sent never reaches the model that summarises its thread
# - Proves the open question is lifted out of the message word for word, not written afresh
# - Proves a summary naming a message from outside the conversation is thrown away whole

import digest
import drafts
import prompts
from constants import Digest, Inbox
from store import load
from utils import heading, rule

LONG = (("t-launch", 9), ("t-api", 4))
LAUNCH = ("m026", "m027", "m028", "m029", "m030", "m033", "m034", "m035", "m036")
OPEN = {"t-launch": "m030", "t-api": "m008"}
ASKS = {"m030": "approve the final pricing copy", "m008": "resend the URL"}
SILENT = "m005"
SAM_WROTE = "m003"
SECRET = "Rk7-quiet-otter-51"
OUTSIDE = "m077"


def thread(store, name: str) -> tuple:
    return store.thread(name)


def check_which(store) -> list[str]:
    problems = []
    found = [(group[0].thread_id, len(group)) for group in digest.long(store)]
    if tuple(found) != LONG:
        problems.append(f"the long conversations are {found}, not {list(LONG)}")
    for name, count in found:
        if count < Digest.SHORTEST:
            problems.append(f"{name} has {count} messages and was still summarised")
    if tuple(one.id for one in thread(store, "t-launch")) != LAUNCH:
        problems.append("the launch thread is not in the order it was written")
    return problems


def check_withheld(store) -> list[str]:
    problems = []
    raw = store.message(SAM_WROTE)
    if not drafts.secret(raw.body):
        problems.append(f"{SAM_WROTE} is meant to carry a credential and does not")
    if drafts.secret(digest.masked(raw).body):
        problems.append(f"{SAM_WROTE} still carries a credential after masking")
    if Digest.WITHHELD not in digest.masked(raw).body:
        problems.append(f"{SAM_WROTE} was masked without saying anything was taken out")

    shown = prompts.conversation(tuple(digest.masked(one)
                                       for one in thread(store, "t-api")))
    if SECRET in shown:
        problems.append("the credential reaches the model that summarises the thread")
    if "m008" not in shown or "resend the URL" not in shown:
        problems.append("masking took out the question the thread is waiting on")
    for one in thread(store, "t-launch"):
        if digest.masked(one).body != one.body:
            problems.append(f"{one.id} carries no credential and was masked anyway")
    return problems


def check_question(store) -> list[str]:
    problems = []
    for name, wanted in ASKS.items():
        asked = digest.question(store.message(name))
        if wanted not in asked:
            problems.append(f"{name}'s open question reads {asked!r}")
        if asked and asked not in store.message(name).body:
            problems.append(f"{name}'s question is not word for word out of the message")
        if asked and not asked.endswith("?"):
            problems.append(f"{name}'s question does not read as one: {asked!r}")
    if digest.question(store.message(SILENT)):
        problems.append(f"{SILENT} asks nothing and a question was read out of it")
    return problems


def told(store, name: str, answer) -> digest.Digest:
    return digest.read(answer, thread(store, name), store)


def check_open(store) -> list[str]:
    problems = []
    for name, wanted in OPEN.items():
        made = told(store, name, {"summary": "what happened", "needs": wanted,
                                  "settled": [thread(store, name)[0].id]})
        if made.needs != wanted:
            problems.append(f"{name} should still be waiting on {wanted}, not {made.needs!r}")
        if not made.asked or made.asked not in store.message(wanted).body:
            problems.append(f"{name}'s question was not lifted out of {wanted}")
        if made.dropped:
            problems.append(f"{name} was summarised and dropped: {made.dropped}")
        if made.settled != (thread(store, name)[0].id,):
            problems.append(f"{name} kept {made.settled} as already answered")
    return problems


def check_refuses(store) -> list[str]:
    problems = []
    stranger = told(store, "t-api", {"summary": "what happened", "needs": OUTSIDE,
                                     "settled": []})
    if stranger.needs:
        problems.append(f"{OUTSIDE} is in another conversation and was named as open")
    if OUTSIDE not in stranger.dropped:
        problems.append(f"naming {OUTSIDE} was not reported: {stranger.dropped!r}")

    spoke = told(store, "t-api", {"summary": "what happened", "needs": SAM_WROTE,
                                  "settled": []})
    if spoke.needs:
        problems.append(f"{SAM_WROTE} is Sam's own message and was named as waiting on him")
    if SAM_WROTE not in spoke.dropped:
        problems.append(f"naming Sam's own message was not reported: {spoke.dropped!r}")

    invented = told(store, "t-api", {"summary": f"see {OUTSIDE} for the rest",
                                     "needs": "m008", "settled": []})
    if invented.summary:
        problems.append("a summary naming a message outside the conversation was kept")
    if OUTSIDE not in invented.dropped:
        problems.append(f"the invented citation was not named: {invented.dropped!r}")

    leaked = told(store, "t-api", {"summary": f"the url is {SECRET} and the password too",
                                   "needs": "m008", "settled": []})
    if leaked.summary:
        problems.append("a summary carrying a credential was kept")
    if leaked.dropped != Digest.LEAKED:
        problems.append(f"the leak was reported as {leaked.dropped!r}")

    kept = told(store, "t-api", {"summary": "what happened", "needs": "",
                                 "settled": ["m001", OUTSIDE]})
    if OUTSIDE in kept.settled:
        problems.append(f"{OUTSIDE} was kept as already answered in another conversation")
    return problems


def check_no_model(store) -> list[str]:
    problems = []
    asked = {"calls": 0}

    def never(system, text, shape):
        asked["calls"] += 1
        return None

    made = digest.gather(store, ask=never)
    if asked["calls"] != len(LONG):
        problems.append(f"{asked['calls']} conversations were put to the model, not {len(LONG)}")
    for one in made:
        if one.summary or one.needs or one.asked:
            problems.append(f"{one.thread} was summarised by a model that said nothing")
        if not one.ids:
            problems.append(f"{one.thread} lost the messages it was built from")
    return problems


def run() -> bool:
    heading("inboxHero digest check")
    store = load()
    problems = []
    for name, found in (("which threads", check_which(store)),
                        ("withheld", check_withheld(store)),
                        ("question", check_question(store)),
                        ("still open", check_open(store)),
                        ("refuses", check_refuses(store)),
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
