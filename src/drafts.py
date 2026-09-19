# cert-aai-2026-06-0061  Sarath Chandra
#
# - Writes replies grounded in earlier mail, from this conversation and from elsewhere
# - Refuses when nothing grounds an answer, or when answering would disclose a credential
# - Lets a reply that commits to nothing go out uncited, using only words the sender used
# - Keeps confidential mail out of sight entirely when the reply is going outside the company

import re
from dataclasses import dataclass
import prompts
import retrieve
from constants import Drafts, Inbox, Retrieval
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


def proposes(message: Message) -> bool:
    return bool(re.search(Drafts.PROPOSES, message.body, re.I))


def declines(body: str) -> bool:
    lowered = body.lower()
    return any(word in lowered for word in Drafts.DECLINES)


def describes(body: str) -> bool:
    return bool(re.search(Drafts.DESCRIBES, body, re.I))


def public(message: Message) -> bool:
    text = f"{message.subject} {message.body}".lower()
    return any(word in text for word in Drafts.PUBLIC)


def outside(message: Message) -> bool:
    return not message.sender.lower().endswith(f"@{Inbox.DOMAIN}")


def confidential(message: Message) -> bool:
    text = f"{message.subject} {message.body}".lower()
    return any(re.search(rf"\b{word}\b", text) for word in Drafts.CONFIDENTIAL)


def shown(message: Message, candidates) -> tuple:
    if not outside(message):
        return candidates
    return tuple(found for found in candidates if not confidential(found))


def said(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - Retrieval.STOPWORDS


def acknowledges(body: str, message: Message) -> bool:
    known = said(retrieve.spoken(message)) | Drafts.DEFERRAL
    return not (said(body) - known)


def checked(answer: dict, allowed: set[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    claimed = [str(name) for name in answer.get("cited") or ()]
    return (tuple(name for name in claimed if name in allowed),
            tuple(name for name in claimed if name not in allowed))


def draft(store: Store, message: Message, ask=None) -> Draft:
    if ask is None:
        import llm
        ask = llm.ask

    before = retrieve.earlier(store, message)
    candidates = shown(message, retrieve.nearby(store, message))
    if not before and not candidates:
        return Draft(id=message.id, refused=Drafts.UNGROUNDED)

    leaking = guarded(before + candidates)
    if leaking:
        return Draft(id=message.id, cited=leaking,
                     refused=f"answering would disclose credentials held in "
                             f"{', '.join(leaking)}")

    answer = ask(prompts.DRAFT_SYSTEM,
                 prompts.context(before, candidates, message, press=public(message)),
                 prompts.DRAFT_SHAPE)
    allowed = {found.id for found in before} | {found.id for found in candidates}
    cited, dropped = checked(answer or {}, allowed)
    body = str((answer or {}).get("body") or "").strip()

    if not body:
        return Draft(id=message.id, refused=Drafts.UNANSWERED, dropped=dropped)
    if not cited and not acknowledges(body, message):
        return Draft(id=message.id, refused=Drafts.INVENTED, dropped=dropped)
    if public(message) and describes(body):
        return Draft(id=message.id, refused=Drafts.PUBLISHED, dropped=dropped)
    if proposes(message) and not declines(body):
        return Draft(id=message.id, refused=Drafts.ACCEPTED, dropped=dropped)
    return Draft(id=message.id, body=body, cited=cited, dropped=dropped)
