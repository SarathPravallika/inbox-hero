# cert-aai-2026-06-0061  Sarath Chandra
#
# - Disposes of obvious mail without spending a model call
# - Only touches what is unmistakably routine, and passes anything unusual on untouched

from dataclasses import dataclass
from constants import Decided, Disposition, Rules
from store import Message


@dataclass(frozen=True, slots=True)
class Decision:
    id: str
    disposition: Disposition
    reason: str
    by: Decided


def automated(message: Message) -> bool:
    return message.sender.split("@")[0].lower() in Rules.AUTOMATED


def boilerplate(message: Message) -> bool:
    return len(message.body) <= Rules.BOILERPLATE_LIMIT


def named(message: Message) -> str:
    subject = message.subject.lower()
    if any(word in subject for word in Rules.RECEIPT):
        return "receipt"
    if any(word in subject for word in Rules.DIGEST):
        return "newsletter"
    return "notification"


def decide(message: Message) -> Decision | None:
    if not (automated(message) and boilerplate(message)):
        return None
    return Decision(
        id=message.id,
        disposition=Disposition.ARCHIVE,
        reason=f"{named(message)} from an automated address, "
               f"{len(message.body)} character body",
        by=Decided.RULE,
    )
