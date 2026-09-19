# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves a reply is only written when earlier mail supports it, and never leaks a credential

from constants import Drafts
from drafts import draft, secret
from retrieve import earlier, offered
from store import load
from utils import heading, rule

GROUNDED = "m043"
LEAKING = "m008"
HOLDS_SECRET = "m003"
ALONE = ("m012", "m046")

def fake(body="Tuesday at 3pm still works, let us keep that slot.", cited=("m010",)):
    box = {"calls": 0, "prompts": []}

    def ask(system, text, shape):
        box["calls"] += 1
        box["prompts"].append(text)
        return {"body": body, "cited": list(cited)}

    return ask, box


def check_earlier(store) -> list[str]:
    problems = []
    seen = {name: tuple(m.id for m in earlier(store, store.message(name)))
            for name in (GROUNDED, LEAKING, *ALONE)}
    if seen[GROUNDED] != ("m010",):
        problems.append(f"{GROUNDED} sees {seen[GROUNDED]}, not ('m010',)")
    if seen[LEAKING] != ("m001", "m003", "m005"):
        problems.append(f"{LEAKING} sees {seen[LEAKING]}")
    for name in ALONE:
        if seen[name]:
            problems.append(f"{name} is alone in its thread but sees {seen[name]}")
    for message in store.messages:
        for found in earlier(store, message):
            if found.timestamp > message.timestamp:
                problems.append(f"{message.id} was offered the later message {found.id}")
    return problems


def check_secrets(store) -> list[str]:
    problems = []
    if not secret(store.message(HOLDS_SECRET).body):
        problems.append(f"{HOLDS_SECRET} holds a broker URL with a password and was not caught")
    for name in ("m001", "m005", "m010", "m043"):
        if secret(store.message(name).body):
            problems.append(f"{name} holds no secret but was flagged as one")
    return problems


def check_ungrounded(store) -> list[str]:
    problems = []
    for name in ALONE:
        ask, box = fake()
        made = draft(store, store.message(name), ask=ask)
        if made.refused != Drafts.UNGROUNDED:
            problems.append(f"{name} refused with {made.refused!r}")
        if made.body:
            problems.append(f"{name} has nothing to ground on but drafted a body")
        if box["calls"]:
            problems.append(f"{name} has nothing to ground on but still called the model")
    return problems


def check_credentials(store) -> list[str]:
    problems = []
    ask, box = fake()
    made = draft(store, store.message(LEAKING), ask=ask)
    if made.body:
        problems.append(f"{LEAKING} was drafted despite the credentials in {HOLDS_SECRET}")
    if HOLDS_SECRET not in made.cited:
        problems.append(f"the refusal does not name {HOLDS_SECRET}")
    if "credential" not in made.refused:
        problems.append(f"{LEAKING} refused with {made.refused!r}")
    if box["calls"]:
        problems.append(f"{HOLDS_SECRET} was sent to the model before the refusal")
    return problems


def check_grounded(store) -> list[str]:
    problems = []
    ask, box = fake()
    made = draft(store, store.message(GROUNDED), ask=ask)
    if made.refused:
        problems.append(f"{GROUNDED} is grounded in m010 but refused: {made.refused}")
    if made.cited != ("m010",):
        problems.append(f"{GROUNDED} cited {made.cited}, not ('m010',)")
    if not made.body:
        problems.append(f"{GROUNDED} produced no body")
    if 'id="m010"' not in "".join(box["prompts"]):
        problems.append("m010 was not put in front of the model")
    return problems


def check_citations(store) -> list[str]:
    problems = []
    ask, box = fake(cited=("m010", "m999", "m003"))
    made = draft(store, store.message(GROUNDED), ask=ask)
    if made.cited != ("m010",):
        problems.append(f"invented citations survived: {made.cited}")
    if set(made.dropped) != {"m999", "m003"}:
        problems.append(f"dropped {made.dropped}, expected m999 and m003")

    ask, box = fake(cited=("m999",))
    made = draft(store, store.message(GROUNDED), ask=ask)
    if made.refused != Drafts.INVENTED:
        problems.append(f"a draft citing only invented ids was kept: {made.refused!r}")
    if made.body:
        problems.append("a draft citing only invented ids kept its body")
    return problems


def run() -> bool:
    heading("inboxHero drafts check")
    store = load()
    problems = []
    for name, found in (("earlier", check_earlier(store)),
                        ("secrets", check_secrets(store)),
                        ("ungrounded", check_ungrounded(store)),
                        ("credentials", check_credentials(store)),
                        ("grounded", check_grounded(store)),
                        ("citations", check_citations(store))):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
