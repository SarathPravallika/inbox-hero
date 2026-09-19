# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves no message escapes without a decision, whatever the model returns

import re
from classify import classify
from constants import Classify, Decided, Disposition
from rules import decide
from store import load
from utils import heading, rule

LEFT = 44
SIZES = [10, 10, 10, 10, 4]

def fake(skip=(), mangle=(), invent=()):
    box = {"calls": 0, "sizes": [], "prompts": []}

    def ask(system, text, shape):
        box["calls"] += 1
        box["prompts"].append(text)
        names = re.findall(r'<message id="(m\d+)"', text)
        box["sizes"].append(len(names))
        answers = [{"id": name,
                    "disposition": "not-a-disposition" if name in mangle else "archive",
                    "reason": "looks routine"}
                   for name in names if name not in skip]
        answers += [{"id": name, "disposition": "reply", "reason": "invented"}
                    for name in invent]
        return answers

    return ask, box


def waiting(store) -> list:
    return [message for message in store.messages if decide(message) is None]


def check_coverage(left) -> list[str]:
    problems = []
    ask, box = fake()
    decisions = classify(left, ask=ask)
    if len(decisions) != len(left):
        problems.append(f"{len(decisions)} decisions came back for {len(left)} messages")
    if [d.id for d in decisions] != [m.id for m in left]:
        problems.append("the decisions are not in the order the messages were given")
    if any(d.by is not Decided.MODEL for d in decisions):
        problems.append("a decision is not marked as decided by the model")
    if any(not d.reason for d in decisions):
        problems.append("a decision carries no reason")
    return problems


def check_batching(left) -> list[str]:
    problems = []
    ask, box = fake()
    classify(left, ask=ask)
    if box["sizes"] != SIZES:
        problems.append(f"batches were {box['sizes']}, not {SIZES}")
    if box["calls"] * Classify.BATCH_SIZE < len(left):
        problems.append(f"{box['calls']} calls cannot cover {len(left)} messages")
    return problems


def check_silence(left) -> list[str]:
    problems = []
    missing, broken = left[0].id, left[1].id
    ask, box = fake(skip=(missing,), mangle=(broken,))
    found = {d.id: d for d in classify(left, ask=ask)}
    for name, why in ((missing, "was left out by the model"), (broken, "came back mangled")):
        if found[name].disposition is not Disposition.ESCALATE:
            problems.append(f"{name} {why} but was not escalated")
        if found[name].reason != Classify.SILENT:
            problems.append(f"{name} {why} but does not say so")
    return problems


def check_invented(left) -> list[str]:
    problems = []
    ask, box = fake(invent=("m999", "m000"))
    decisions = classify(left, ask=ask)
    for name in ("m999", "m000"):
        if name in {d.id for d in decisions}:
            problems.append(f"{name} was invented by the model and became a decision")
    return problems


def check_untrusted(left) -> list[str]:
    problems = []
    ask, box = fake()
    classify(left, ask=ask)
    quoted = "\n".join(box["prompts"])
    for message in left:
        if f'<message id="{message.id}"' not in quoted:
            problems.append(f"{message.id} did not reach the model inside an envelope")
        if message.body and message.body.splitlines()[0] not in quoted:
            problems.append(f"{message.id} body was not passed through")
    return problems


def run() -> bool:
    heading("inboxHero classify check")
    left = waiting(load())
    problems = []
    if len(left) != LEFT:
        problems.append(f"{len(left)} messages reached the model, not {LEFT}")
    for name, found in (("coverage", check_coverage(left)),
                        ("batching", check_batching(left)),
                        ("silence", check_silence(left)),
                        ("invented", check_invented(left)),
                        ("untrusted", check_untrusted(left))):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(left)} messages classified, {len(problems)} problems")
    return not problems
