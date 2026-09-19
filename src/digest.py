# cert-aai-2026-06-0061  Sarath Chandra
#
# - Reduces a long conversation to what it is about and the one thing still waiting on Sam
# - Credentials are taken out of the thread before the model reads it, so a summary of the
#   conversation that shared a password cannot repeat the password
# - The model names which message is still open; the question itself is lifted out of that
#   message by code, so the words Sam reads are the words the sender wrote and no secret
#   the masking took out can come back through the quote
# - A summary naming a message from outside the conversation is dropped whole, because an
#   invented citation in a summary is worse than no summary

import re
from dataclasses import dataclass, replace
from constants import Digest as Setting
from constants import Inbox
import drafts
import prompts


@dataclass(frozen=True, slots=True)
class Digest:
    thread: str
    ids: tuple[str, ...]
    summary: str = ""
    needs: str = ""
    asked: str = ""
    settled: tuple[str, ...] = ()
    dropped: str = ""


def long(store) -> list[tuple]:
    return sorted((group for group in store.threads.values()
                   if len(group) >= Setting.SHORTEST),
                  key=lambda group: (-len(group), group[0].timestamp))


def sentences(text: str) -> list[str]:
    return [one for one in re.split(r"(?<=[.!?])\s+", text.strip()) if one]


def hidden(body: str) -> str:
    return " ".join(Setting.WITHHELD if drafts.secret(one) else one
                    for one in sentences(body))


def masked(message):
    if not drafts.secret(message.body):
        return message
    return replace(message, body=hidden(message.body))


def question(message) -> str:
    found = re.findall(Setting.QUESTION, message.body)
    for one in reversed(found):
        asked = one.strip()
        if asked and asked != Setting.WITHHELD and not drafts.secret(asked):
            return asked
    return ""


def named(text: str) -> set[str]:
    return set(re.findall(r"\bm\d{3}\b", text))


def read(answer, group, store) -> Digest:
    ids = tuple(one.id for one in group)
    known = set(ids)
    thread = group[0].thread_id

    summary = str((answer or {}).get("summary") or "").strip()
    strangers = sorted(named(summary) - known)
    if strangers:
        return Digest(thread=thread, ids=ids,
                      dropped=Setting.INVENTED.format(ids=", ".join(strangers)))
    if drafts.secret(summary):
        return Digest(thread=thread, ids=ids, dropped=Setting.LEAKED)

    needs = str((answer or {}).get("needs") or "").strip()
    settled = tuple(name for name in ((answer or {}).get("settled") or ())
                    if name in known)
    dropped = ""
    if needs and needs not in known:
        dropped, needs = Setting.STRANGER.format(id=needs), ""
    elif needs and group[ids.index(needs)].sender.lower() == Inbox.OWNER:
        dropped, needs = Setting.SPOKE.format(id=needs), ""

    asked = question(group[ids.index(needs)]) if needs else ""
    if needs and not asked:
        dropped = Setting.UNQUOTED
    return Digest(thread=thread, ids=ids, summary=summary, needs=needs, asked=asked,
                  settled=settled, dropped=dropped)


def gather(store, ask=None) -> list[Digest]:
    if ask is None:
        import llm
        ask = llm.ask

    found = []
    for group in long(store):
        shown = tuple(masked(one) for one in group)
        found.append(read(ask(prompts.THREAD_SYSTEM, prompts.conversation(shown),
                              prompts.THREAD_SHAPE), group, store))
    return found
