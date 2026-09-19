# cert-aai-2026-06-0061  Sarath Chandra
#
# - Finds a proposed time that breaks something Sam has said, or lands on something settled,
#   and answers it with three times that do neither
# - A proposal blocks a slot we are about to offer and never counts as settled when the
#   calendar is being described, because committing Sam and describing his week are
#   different jobs and a calendar built out of an inbox is mostly requests
# - Every time in the reply has to be one this code worked out, so the model can decline and
#   offer but can never invent a slot
# - The reply says when Sam is free and never what he is doing, so a counter-offer to somebody
#   outside the company exposes availability and nothing else
# - Nothing is sent from here; the reply is held for the same approval as any other send

import re
from dataclasses import dataclass, replace
from datetime import date, timedelta

import commitments
import prompts
import retrieve
from constants import Commitments, Kind, Offers as Setting, Retrieval, Settled


@dataclass(frozen=True, slots=True)
class Offer:
    id: str
    to: str
    what: str
    when: str
    at: str
    because: str
    cited: tuple[str, ...] = ()
    blocked: tuple[str, ...] = ()
    slots: tuple[str, ...] = ()
    body: str = ""
    refused: str = ""


def scheduling(standing) -> list:
    return [one for one in standing if one.kind == Kind.SCHEDULING]


def breaks(at: str, standing) -> tuple[str, str]:
    for one in scheduling(standing):
        edge = commitments.clocked(one.value)
        if not edge:
            continue
        if (one.bound == "before" and at < edge) or (one.bound == "after" and at > edge):
            return Setting.BREAKS.format(subject=one.subject, bound=one.bound,
                                         value=one.value), one.source
    return "", ""


def busy(diary, when: str, at: str, skip: str) -> list:
    return [one for one in diary
            if one.id != skip and one.when == when and one.at == at]


def working(when: str) -> list[str]:
    here, found = date.fromisoformat(when), []
    while len(found) < Setting.DAYS:
        if here.weekday() not in Setting.WEEKEND:
            found.append(here.isoformat())
        here += timedelta(days=1)
    return found


def candidates(one) -> list[str]:
    days = working(one.when)
    found = [f"{when} {one.at}" for when in days]
    for when in days:
        found.extend(f"{when} {at}" for at in Setting.SLOTS if at != one.at)
    return found


def search(one, diary, standing) -> tuple[tuple[str, ...], tuple[str, ...]]:
    offered, blocked = [], []
    for slot in candidates(one):
        when, at = slot.split(" ")
        if breaks(at, standing)[0]:
            continue
        taken = busy(diary, when, at, one.id)
        if taken:
            blocked.extend(other.id for other in taken)
            continue
        offered.append(slot)
        if len(offered) == Setting.OFFERED:
            break
    return tuple(offered), tuple(dict.fromkeys(blocked))


def spoken(slot: str) -> str:
    when, at = slot.split(" ")
    hour, minute = (int(part) for part in at.split(":"))
    return Setting.SHOWN.format(
        day=date.fromisoformat(when).strftime("%A %-d %B").replace(" 0", " "),
        at=f"{hour % 12 or 12}:{minute:02d}{'am' if hour < 12 else 'pm'}")


def wanted(diary, standing) -> list[Offer]:
    found = []
    for one in diary:
        if one.settled != Settled.PROPOSED or not one.when or not one.at:
            continue
        why, source = breaks(one.at, standing)
        held = [other for other in busy(diary, one.when, one.at, one.id)
                if other.settled == Settled.SETTLED]
        if not why and not held:
            continue
        found.append(Offer(id=one.id, to="", what=one.what, when=one.when, at=one.at,
                           because=why or Setting.TAKEN,
                           cited=(source.removeprefix("email:"),) if source else ()))
    return found


def times(text: str) -> set[str]:
    found = {commitments.clocked(match.group(0))
             for match in re.finditer(Commitments.CLOCK, text, re.I)}
    for match in re.finditer(Setting.PLAIN, text):
        found.add(f"{int(match.group(1)):02d}:{match.group(2)}")
    return found - {""}


def dates(text: str) -> set[int]:
    return {int(match.group(1))
            for match in re.finditer(Commitments.ORDINAL, text, re.I)}


def weekdays(text: str) -> set[str]:
    lowered = text.lower()
    return {name for name in Commitments.WEEKDAYS if name in lowered}


def allowed(one: Offer) -> tuple[set[str], set[int], set[str]]:
    when = [slot.split(" ")[0] for slot in one.slots]
    return ({slot.split(" ")[1] for slot in one.slots} | {one.at},
            {date.fromisoformat(day).day for day in when + [one.when]},
            {date.fromisoformat(day).strftime("%A").lower() for day in when + [one.when]})


def discloses(body: str, diary, one: Offer) -> bool:
    said = retrieve.words(body)
    for other in diary:
        if other.id in one.blocked and retrieve.words(other.what) & said:
            return True
    return False


def checked(body: str, one: Offer, diary) -> str:
    clock, days, named = allowed(one)
    stray = sorted(times(body) - clock)
    if stray:
        return Setting.INVENTED.format(times=", ".join(stray))
    if dates(body) - days or weekdays(body) - named:
        return Setting.MISDATED
    if discloses(body, diary, one):
        return Setting.DISCLOSED
    return ""


def read(answer, waiting: dict, diary) -> dict:
    written = {}
    for record in answer or ():
        name = str(record.get("id") or "")
        body = str(record.get("body") or "").strip()
        if name not in waiting or not body:
            continue
        written[name] = (body, checked(body, waiting[name], diary))
    return written


def gather(store, diary, standing, ask=None) -> list[Offer]:
    if ask is None:
        import llm
        ask = llm.ask

    found = []
    for one in wanted(diary, standing):
        slots, blocked = search(one, diary, standing)
        found.append(replace(one, to=store.message(one.id).sender, slots=slots,
                             blocked=blocked))
    empty = Setting.NOTHING.format(days=Setting.DAYS)
    waiting = {one.id: one for one in found if one.slots}
    if not waiting:
        return [replace(one, refused=empty) for one in found]

    written = read(ask(prompts.OFFER_SYSTEM,
                       prompts.offer([(store.message(one.id),
                                       [spoken(slot) for slot in one.slots])
                                      for one in waiting.values()]),
                       prompts.OFFER_SHAPE), waiting, diary)

    done = []
    for one in found:
        if not one.slots:
            done.append(replace(one, refused=empty))
            continue
        body, wrong = written.get(one.id, ("", Setting.SILENT))
        done.append(replace(one, body="" if wrong else body,
                            refused=wrong or ("" if body else Setting.SILENT)))
    return done
