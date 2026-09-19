# cert-aai-2026-06-0061  Sarath Chandra
#
# - Decides what to do with the mail the rules would not touch
# - Guarantees every message ends with a decision even when the model answers badly

import prompts
from constants import Classify, Decided, Disposition, Memory
from rules import Decision


def batches(messages: list, size: int = Classify.BATCH_SIZE):
    for start in range(0, len(messages), size):
        yield messages[start:start + size]


def understood(answers) -> dict:
    found = {}
    for answer in answers or ():
        try:
            disposition = Disposition(answer.get("disposition"))
        except (ValueError, AttributeError):
            continue
        name = answer.get("id")
        reason = str(answer.get("reason") or "").strip()
        claimed = str(answer.get("preference") or Memory.NONE)
        if name and reason:
            found[name] = Decision(id=name, disposition=disposition, reason=reason,
                                   by=Decided.MODEL,
                                   preference="" if claimed == Memory.NONE else claimed)
    return found


def silent(message) -> Decision:
    return Decision(id=message.id, disposition=Disposition.ESCALATE, reason=Classify.SILENT,
                    by=Decided.MODEL)


def classify(messages, ask=None) -> list[Decision]:
    if ask is None:
        import llm
        ask = llm.ask

    messages = list(messages)
    found = {}

    for group in batches(messages):
        found.update(understood(ask(prompts.SYSTEM, prompts.batch(group), prompts.SHAPE)))
    return [found.get(message.id) or silent(message) for message in messages]
