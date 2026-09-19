# cert-aai-2026-06-0061  Sarath Chandra
#
# - Answers one question about one message: why was it treated the way it was
# - Every line is a record read back off disk, so nothing here is worked out on the spot
# - Each section names the file it was read from, which is what makes the answer checkable
# - The absences are answered too, because deciding not to reply is as much a decision as
#   replying, and a system that only explains what it did explains the easy half

from dataclasses import dataclass
from constants import Decided, Disposition, Kind, Memory, Why
import gate
import tracing


@dataclass(frozen=True, slots=True)
class Told:
    label: str
    lines: tuple[str, ...]
    source: str


def made(name: str, artifact: dict) -> dict:
    return next((one for one in artifact["decisions"] if one["id"] == name), {})


def disposed(name: str, artifact: dict) -> str:
    return made(name, artifact).get("disposition", "")


def known(name: str, artifact: dict, store) -> bool:
    return name in store.ids or bool(made(name, artifact))


def suggestions(artifact: dict) -> list[str]:
    wanted = []
    for by in Decided:
        found = next((one["id"] for one in artifact["decisions"] if one["by"] == by), None)
        if found:
            wanted.append(found)
    sent = next((one["id"] for one in artifact["drafts"] if not one["refused"]), None)
    if sent:
        wanted.append(sent)
    return wanted


def arrived(name: str, store) -> Told:
    if name not in store.ids:
        return Told(Why.ARRIVED, (Why.GONE,), Why.MAILBOX)
    message = store.message(name)
    thread = store.thread(message.thread_id)
    return Told(Why.ARRIVED,
                (Why.SUBJECT.format(subject=message.subject),
                 Why.SENDER.format(sender=message.sender, to=message.to,
                                   at=message.timestamp),
                 Why.THREAD.format(thread=message.thread_id,
                                   place=[one.id for one in thread].index(name) + 1,
                                   count=len(thread))),
                Why.MAILBOX)


def decided(name: str, artifact: dict) -> Told:
    part = Why.RUN.format(part="decisions[]")
    one = made(name, artifact)
    if not one:
        return Told(Why.DECIDED, (Why.UNDECIDED,), part)
    lines = [Why.BY[Decided(one["by"])].format(disposition=one["disposition"]),
             one["reason"]]
    if one["copy"]:
        lines.append(Why.COPIED.format(copy=", ".join(one["copy"])))
    return Told(Why.DECIDED, tuple(lines), part)


def guarded(name: str, artifact: dict) -> Told:
    part = Why.RUN.format(part="refusals[]")
    found = next((one for one in artifact.get("refusals") or () if one["id"] == name), None)
    if found is None:
        return Told(Why.GUARDED, (Why.UNTOUCHED,), part)
    lines = [Why.ATTEMPTED.format(tried=", ".join(found["attempted"]))]
    if found["where"]:
        lines.append(Why.NAMED.format(where=", ".join(found["where"])))
    lines.append(found["flagged"])
    return Told(Why.GUARDED, tuple(lines), part)


def drafted(name: str, artifact: dict) -> Told:
    part = Why.RUN.format(part="drafts[]")
    one = next((draft for draft in artifact["drafts"] if draft["id"] == name), None)
    if one is None:
        return Told(Why.DRAFTED,
                    (Why.NOT_REPLY.format(disposition=disposed(name, artifact)),), part)
    if one["refused"]:
        return Told(Why.DRAFTED, (Why.REFUSED_DRAFT.format(why=one["refused"]),), part)
    opening = (Why.CITED.format(cited=", ".join(one["cited"])) if one["cited"]
               else Why.UNCITED)
    return Told(Why.DRAFTED, (opening, one["body"]), part)


def dated(name: str, artifact: dict) -> Told:
    part = Why.RUN.format(part="commitments[]")
    found = [one for one in artifact["commitments"] if name in one["cited"]]
    if found:
        return Told(Why.DATED,
                    tuple(Why.ON_CALENDAR.format(when=one["when"] or "no date",
                                                 at=one["at"] or "     ",
                                                 settled=one["settled"], what=one["what"])
                          for one in found), part)
    if disposed(name, artifact) == Disposition.QUARANTINE:
        return Told(Why.DATED, (Why.OFF_CALENDAR,), part)
    return Told(Why.DATED, (Why.NO_DATES,), part)


def preferred(name: str, artifact: dict) -> Told:
    part = Why.RUN.format(part="recorded[] and standing[]")
    source = Memory.SOURCE.format(id=name)
    lines = [Why.RECORDED.format(said=one["said"]) for one in artifact["recorded"]
             if one["source"] == source]

    copies = made(name, artifact).get("copy") or ()
    for one in artifact["standing"]:
        if copies and one["kind"] == Kind.COPYING:
            lines.append(Why.APPLIED.format(who=", ".join(copies), source=one["source"]))

    draft = next((one for one in artifact["drafts"] if one["id"] == name), None)
    for one in artifact["standing"]:
        if draft and one["source"].removeprefix(Memory.FROM) in draft["cited"]:
            lines.append(Why.LEANED.format(source=one["source"]))
    return Told(Why.PREFERRED, tuple(lines) or (Why.NO_PREFERENCE,), part)


def approved(name: str) -> Told:
    found = [one for one in gate.records() if one["id"] == name]
    if not found:
        return Told(Why.APPROVED, (Why.NO_APPROVAL,), Why.APPROVALS)
    return Told(Why.APPROVED,
                tuple(Why.ANSWERED.format(action=one["action"], answer=one["answer"],
                                          at=one["at"], outcome=one["outcome"])
                      for one in found), Why.APPROVALS)


def mentions(event: dict, name: str) -> bool:
    return (event.get("id") == name
            or name in (event.get("ids") or ())
            or event.get("source") == Memory.SOURCE.format(id=name))


def traced(name: str) -> Told:
    found = [event for event in tracing.events() if mentions(event, name)]
    if not found:
        return Told(Why.TRACED, (Why.NO_TRACE,), Why.TRACE)
    return Told(Why.TRACED,
                tuple(Why.EVENT.format(at=event["at"], cap=event["cap"],
                                       event=event["event"]) for event in found),
                Why.TRACE)


def account(name: str, artifact: dict, store) -> list[Told]:
    return [arrived(name, store), decided(name, artifact), guarded(name, artifact),
            drafted(name, artifact), dated(name, artifact), preferred(name, artifact),
            approved(name), traced(name)]


def files(told: list[Told]) -> set[str]:
    return {one.source.split(",")[0] for one in told}
