# cert-aai-2026-06-0061  Sarath Chandra

import prompts
from constants import Decided, Disposition, Model
from rules import Decision

SILENT = "the model returned no usable disposition, so a person has to look"


def batches(messages: list, size: int = Model.BATCH_SIZE):
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
        if name and reason:
            found[name] = Decision(id=name, disposition=disposition, reason=reason,
                                   by=Decided.MODEL)
    return found


def silent(message) -> Decision:
    return Decision(id=message.id, disposition=Disposition.ESCALATE, reason=SILENT,
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
