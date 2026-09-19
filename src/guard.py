# cert-aai-2026-06-0061  Sarath Chandra
#
# - Reads every message before the rules and before the model ever see it
# - Catches mail that talks to the assistant rather than to Sam, and asks it to act
# - Only names an address as a target when it sits in the same sentence as the asking, so a
#   quoted correspondent in a forwarded thread is not reported as somewhere mail would go
# - Names what was attempted in a fixed vocabulary, so a refusal says something checkable
# - Quarantines and never deletes, so the attempt stays in the mailbox as evidence
# - Both conditions are required: a note to the assistant that asks for nothing is a
#   preference, not an attack, which is how Sam's own calendar rule gets through

import re
from dataclasses import dataclass
from constants import Attempt, Decided, Disposition, Guard, Inbox
from rules import Decision
from store import Message


@dataclass(frozen=True, slots=True)
class Threat:
    id: str
    attempts: tuple[str, ...]
    where: tuple[str, ...] = ()
    said: str = ""


def spoken(message: Message) -> str:
    return f"{message.subject}\n{message.body}"


def sentences(text: str):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def addressed(text: str) -> str:
    for part in sentences(text):
        if re.search(Guard.SPOKEN_TO, part, re.I):
            return part
    return ""


def tried(text: str) -> tuple[str, ...]:
    return tuple(str(name) for name, patterns in Guard.TRIES.items()
                 if any(re.search(pattern, text, re.I) for pattern in patterns))


def asking(text: str) -> str:
    best, most = "", 0
    for part in sentences(text):
        found = len(tried(part))
        if found > most:
            best, most = part, found
    return best


def elsewhere(message: Message, text: str) -> tuple[str, ...]:
    ours = {message.sender.lower(), Inbox.OWNER.lower()}
    found = []
    for part in sentences(text):
        if not any(re.search(pattern, part, re.I) for pattern in Guard.TRIES[Attempt.FORWARD]):
            continue
        for address in re.findall(Guard.ADDRESS, part):
            whole = address.lower()
            if whole in ours or whole.endswith(f"@{Inbox.DOMAIN}") or whole in found:
                continue
            found.append(whole)
    return tuple(found)


def inspect(message: Message) -> Threat | None:
    text = spoken(message)
    said = addressed(text)
    if not said:
        return None
    attempts = tried(text)
    if not attempts:
        return None
    return Threat(id=message.id, attempts=attempts, where=elsewhere(message, text), said=said)


def wording(threat: Threat) -> str:
    spelt = []
    for name in threat.attempts:
        said = Guard.SAYS[Attempt(name)]
        if name == str(Attempt.FORWARD) and threat.where:
            said += Guard.TO.format(where=", ".join(threat.where))
        spelt.append(said)
    if len(spelt) == 1:
        return spelt[0]
    return ", ".join(spelt[:-1]) + f" and {spelt[-1]}"


def flagged(threat: Threat) -> str:
    return Guard.FLAGGED.format(id=threat.id, tried=wording(threat))


def decide(message: Message) -> Decision | None:
    threat = inspect(message)
    if threat is None:
        return None
    return Decision(id=message.id, disposition=Disposition.QUARANTINE,
                    reason=Guard.REASON.format(tried=wording(threat)), by=Decided.GUARD)


def sweep(store) -> tuple[Threat, ...]:
    return tuple(found for found in (inspect(message) for message in store.messages)
                 if found is not None)
