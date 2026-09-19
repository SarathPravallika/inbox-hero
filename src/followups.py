# cert-aai-2026-06-0061  Sarath Chandra
#
# - Finds the mail Sam sent that nobody has answered, and writes him something to send again
# - Reports every message he sent, not only the ones worth chasing, so the ones left alone
#   carry the reason they were left alone
# - A nudge may use only the words his own message used, a grammatical form of one, or a
#   closed nudging vocabulary, so a chase cannot invent a deadline he never set
# - Nothing quarantined is ever chased, because a chase is mail leaving the building

from dataclasses import dataclass, replace
from datetime import date
from constants import Disposition, Drafts, Followups as Setting, Inbox
import drafts
import prompts
import retrieve


@dataclass(frozen=True, slots=True)
class Followup:
    id: str
    to: str
    subject: str
    sent: str
    waiting: int
    chased: bool = False
    why: str = ""
    body: str = ""
    refused: str = ""


def mine(store) -> list:
    return [message for message in store.messages
            if message.sender.lower() == Inbox.OWNER]


def waited(message) -> int:
    return (date.fromisoformat(Setting.TODAY)
            - date.fromisoformat(message.timestamp[:10])).days


def answered(store, message):
    for one in store.thread(message.thread_id):
        if one.timestamp > message.timestamp and one.sender.lower() != Inbox.OWNER:
            return one
    return None


def quarantined(name: str, decisions) -> bool:
    return any(one.id == name and one.disposition is Disposition.QUARANTINE
               for one in decisions)


def looked(store, decisions) -> list[Followup]:
    found = []
    for message in mine(store):
        days = waited(message)
        one = Followup(id=message.id, to=message.to, subject=message.subject,
                       sent=message.timestamp, waiting=days)
        reply = answered(store, message)
        if quarantined(message.id, decisions):
            found.append(replace(one, why=Setting.HELD))
        elif message.to.lower() == Inbox.OWNER:
            found.append(replace(one, why=Setting.SELF))
        elif reply is not None:
            found.append(replace(one, why=Setting.ANSWERED.format(by=reply.id)))
        elif days < Setting.PATIENCE:
            found.append(replace(one, why=Setting.RECENT.format(
                days=days, patience=Setting.PATIENCE)))
        else:
            found.append(replace(one, chased=True))
    return found


def rooted(word: str, known: set[str]) -> bool:
    if word in known:
        return True
    if len(word) < Setting.ROOT:
        return False
    return any(one[:Setting.ROOT] == word[:Setting.ROOT]
               for one in known if len(one) >= Setting.ROOT)


def nudges(body: str, message) -> bool:
    known = drafts.said(retrieve.spoken(message)) | Drafts.DEFERRAL | Setting.NUDGE
    return all(rooted(word, known) for word in drafts.said(body))


def read(answer, waiting, store) -> dict:
    written = {}
    for record in answer or ():
        name = str(record.get("id") or "")
        body = str(record.get("body") or "").strip()
        if name not in waiting or not body:
            continue
        written[name] = (body if nudges(body, store.message(name)) else "")
    return written


def gather(store, decisions, ask=None) -> list[Followup]:
    if ask is None:
        import llm
        ask = llm.ask

    found = looked(store, decisions)
    waiting = [one for one in found if one.chased]
    if not waiting:
        return found

    written = {}
    for start in range(0, len(waiting), Setting.BATCH):
        group = waiting[start:start + Setting.BATCH]
        written.update(read(ask(prompts.CHASE_SYSTEM,
                                prompts.chase([(store.message(one.id), one.waiting)
                                               for one in group]),
                                prompts.CHASE_SHAPE), {one.id for one in group}, store))

    return [one if not one.chased
            else replace(one, body=written.get(one.id, ""),
                         refused=("" if written.get(one.id)
                                  else (Setting.INVENTED if one.id in written
                                        else Setting.SILENT)))
            for one in found]
