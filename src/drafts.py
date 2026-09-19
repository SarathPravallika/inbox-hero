# cert-aai-2026-06-0061  Sarath Chandra
#
# - Writes replies grounded in earlier mail, and records what they drew on
# - Refuses when nothing grounds an answer, or when answering would disclose a credential

import re
from dataclasses import dataclass
import prompts
import retrieve
from constants import Drafts
from store import Message, Store


@dataclass(frozen=True, slots=True)
class Draft:
    id: str
    body: str = ""
    cited: tuple[str, ...] = ()
    refused: str = ""
    dropped: tuple[str, ...] = ()


def secret(text: str) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in Drafts.SECRETS)


def guarded(before) -> tuple[str, ...]:
    return tuple(found.id for found in before if secret(found.body))


def checked(answer: dict, allowed: set[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    claimed = [str(name) for name in answer.get("cited") or ()]
    return (tuple(name for name in claimed if name in allowed),
            tuple(name for name in claimed if name not in allowed))


def draft(store: Store, message: Message, ask=None) -> Draft:
    if ask is None:
        import llm
        ask = llm.ask

    before = retrieve.earlier(store, message)
    if not before:
        return Draft(id=message.id, refused=Drafts.UNGROUNDED)

    leaking = guarded(before)
    if leaking:
        return Draft(id=message.id, cited=leaking,
                     refused=f"answering would disclose credentials held in "
                             f"{', '.join(leaking)}")

    answer = ask(prompts.DRAFT_SYSTEM, prompts.thread(before, message), prompts.DRAFT_SHAPE)
    cited, dropped = checked(answer or {}, retrieve.offered(store, message))
    body = str((answer or {}).get("body") or "").strip()

    if not body or not cited:
        return Draft(id=message.id, refused=Drafts.INVENTED, dropped=dropped)
    return Draft(id=message.id, body=body, cited=cited, dropped=dropped)
