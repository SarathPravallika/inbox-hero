# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves a reply is only written when earlier mail supports it, and never leaks a credential

from constants import Drafts, Inbox
from drafts import (acknowledges, confidential, declines, describes, draft, outside,
                    proposes, public, secret, shown)
from retrieve import earlier, meant, nearby, offered
from store import load
from utils import heading, rule

GROUNDED = "m043"
LEAKING = "m008"
HOLDS_SECRET = "m003"
ALONE = ("m096",)
UNSUPPORTED = "m051"
BORROWED = "m028"

def fake(body="I cannot do that time, it is before 11:00am.", cited=("m010",)):
    box = {"calls": 0, "prompts": []}

    def ask(system, text, shape):
        box["calls"] += 1
        box["prompts"].append(text)
        return {"body": body, "cited": list(cited)}

    return ask, box


def check_earlier(store) -> list[str]:
    problems = []
    seen = {name: tuple(m.id for m in earlier(store, store.message(name)))
            for name in (GROUNDED, LEAKING, "m012", "m046")}
    if seen[GROUNDED] != ("m010",):
        problems.append(f"{GROUNDED} sees {seen[GROUNDED]}, not ('m010',)")
    if seen[LEAKING] != ("m001", "m003", "m005"):
        problems.append(f"{LEAKING} sees {seen[LEAKING]}")
    for name in ("m012", "m046"):
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


def check_nearby(store) -> list[str]:
    problems = []
    for message in store.messages:
        inside = {found.id for found in store.thread(message.thread_id)}
        for found in nearby(store, message):
            if found.timestamp >= message.timestamp:
                problems.append(f"{message.id} was offered {found.id}, which is not earlier")
            if found.id in inside:
                problems.append(f"{message.id} was offered {found.id} from its own thread")
    if not nearby(store, store.message("m046")):
        problems.append("m046 has launch mail elsewhere but was offered nothing")
    if "m036" not in {found.id for found in nearby(store, store.message("m046"))}:
        problems.append("m046 was not offered m036, which holds the launch date")
    if "m041" not in {found.id for found in nearby(store, store.message("m043"))}:
        problems.append("m043 was not offered m041, which holds the rule that answers it")
    return problems


def check_confidential(store) -> list[str]:
    problems = []
    if not confidential(store.message("m038")):
        problems.append("m038 is the board review and was not treated as confidential")
    for name in ("m013", "m041", "m036"):
        if confidential(store.message(name)):
            problems.append(f"{name} is ordinary mail but was treated as confidential")
    if not outside(store.message("m051")):
        problems.append("m051 comes from outside the company and was not seen as external")
    if outside(store.message("m013")):
        problems.append("m013 comes from inside the company and was seen as external")

    friend = store.message("m051")
    if "m038" in {found.id for found in shown(friend, nearby(store, friend))}:
        problems.append("the board review was offered while replying to someone outside")
    colleague = store.message("m012")
    inside = nearby(store, colleague)
    if shown(colleague, inside) != inside:
        problems.append("mail was withheld while replying to a colleague")
    return problems


def check_proposals(store) -> list[str]:
    problems = []
    for name in ("m010", "m043", "m016", "m013"):
        if not proposes(store.message(name)):
            problems.append(f"{name} names a clock time and was not seen as a proposal")
    for name in ("m046", "m033", "m012", "m051"):
        if proposes(store.message(name)):
            problems.append(f"{name} names no clock time but was seen as a proposal")
    if declines("Tuesday the 15th at 3:00pm works for me."):
        problems.append("an acceptance was read as a refusal")
    if not declines("I cannot meet at 9:00am as I do not take meetings before 11:00am."):
        problems.append("a refusal was not read as one")

    ask, box = fake(body="Tuesday the 15th at 3:00pm works for me.", cited=("m041",))
    made = draft(store, store.message("m010"), ask=ask)
    if made.refused != Drafts.ACCEPTED:
        problems.append(f"a draft accepting a proposed time was kept: {made.refused!r}")
    if made.body:
        problems.append("a draft accepting a proposed time kept its body")
    if made.cited:
        problems.append(f"a refusal about the calendar blamed earlier mail: {made.cited}")

    ask, box = fake(body="I cannot do that time, it is before 11:00am.", cited=("m041",))
    made = draft(store, store.message("m010"), ask=ask)
    if made.refused:
        problems.append(f"a draft declining a proposed time was refused: {made.refused!r}")
    return problems


def check_public(store) -> list[str]:
    problems = []
    if not public(store.message("m046")):
        problems.append("m046 asks for a line for publication and was not seen as press")
    for name in ("m016", "m043", "m013", "m051"):
        if public(store.message(name)):
            problems.append(f"{name} asks for nothing publishable but was seen as press")

    for invented in ("PaperJet is different because of our vision.",
                     "Our product helps teams move faster.",
                     "We streamline document workflows."):
        if not describes(invented):
            problems.append(f"a product description slipped through: {invented!r}")
    for safe in ("The launch date is September 20th.",
                 "The official wording will follow from Sam separately.",
                 "I cannot meet at 9:00am as I do not take meetings before 11:00am."):
        if describes(safe):
            problems.append(f"an ordinary sentence was read as a product claim: {safe!r}")

    ask, box = fake(body="PaperJet is different because of our vision.", cited=("m036",))
    made = draft(store, store.message("m046"), ask=ask)
    if made.refused != Drafts.PUBLISHED:
        problems.append(f"a draft describing the product was kept: {made.refused!r}")
    if made.body:
        problems.append("a draft describing the product kept its body")
    if made.cited:
        problems.append(f"a refusal about our own wording blamed earlier mail: {made.cited}")

    ask, box = fake(body="The launch date is September 20th, the wording follows separately.",
                    cited=("m036",))
    made = draft(store, store.message("m046"), ask=ask)
    if made.refused:
        problems.append(f"a press reply that describes nothing was refused: {made.refused!r}")
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


def check_uncited(store) -> list[str]:
    problems = []
    friend = store.message(UNSUPPORTED)
    if BORROWED in {found.id for found in nearby(store, friend)}:
        problems.append(f"{BORROWED} is internal mail and is still offered for {UNSUPPORTED}")
    if meant(store, friend, 1) and meant(store, friend, 1)[0].id != BORROWED:
        problems.append("the retrieval measurement no longer holds, rank the scorers again")

    kept = "Yes, I left AeroWing! Coffee sounds good. Let me check my week and come " \
           "back to you on a time."
    if not acknowledges(kept, friend):
        problems.append(f"a reply saying only what the sender said was refused: {kept!r}")
    for reaching in ("It is true that I have left AeroWing. I cannot confirm a time as I owe "
                     "a draft of the Product Hunt copy by Wednesday.",
                     "Yes, I left AeroWing. We launch on September 20th, coffee after that?",
                     "I cannot do that time, it is before 11:00am."):
        if acknowledges(reaching, friend):
            problems.append(f"an uncited reply reached past the sender: {reaching!r}")

    ask, box = fake(body=kept, cited=())
    made = draft(store, friend, ask=ask)
    if made.refused:
        problems.append(f"{UNSUPPORTED} refused a reply that discloses nothing: {made.refused!r}")
    if made.cited:
        problems.append(f"{UNSUPPORTED} claimed a citation it was not given: {made.cited}")
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

    ask, box = fake(body="", cited=("m010",))
    made = draft(store, store.message(GROUNDED), ask=ask)
    if made.refused != Drafts.UNANSWERED:
        problems.append(f"an empty draft was refused as {made.refused!r}, not unanswered")
    return problems


def run() -> bool:
    heading("inboxHero drafts check")
    store = load()
    problems = []
    for name, found in (("earlier", check_earlier(store)),
                        ("secrets", check_secrets(store)),
                        ("nearby", check_nearby(store)),
                        ("confidential", check_confidential(store)),
                        ("proposals", check_proposals(store)),
                        ("press", check_public(store)),
                        ("ungrounded", check_ungrounded(store)),
                        ("credentials", check_credentials(store)),
                        ("grounded", check_grounded(store)),
                        ("uncited", check_uncited(store)),
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
