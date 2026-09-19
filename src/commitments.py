# cert-aai-2026-06-0061  Sarath Chandra
#
# - Pulls the dates, deadlines and obligations out of the inbox and puts them on a calendar
# - The model copies out the words a message used; every date is worked out here, in code
# - A deadline written as "two days before the board review" is resolved against the message
#   that holds the review date, and the entry cites both
# - Says whether something is settled, merely proposed, or owed by Sam, because an inbox is
#   mostly requests and treating a request as a fixture is how a calendar starts lying
# - The same thing said twice in one thread becomes one entry citing both messages
# - Two different entries at the same moment are called out rather than listed quietly
# - Nothing is put on the calendar from mail the system refused to act on, so a demand for
#   a wire transfer in a phishing message never appears as something Sam owes

import re
from dataclasses import dataclass
from datetime import date, timedelta
from constants import Commitments, Decided, Disposition, Settled
import prompts


@dataclass(frozen=True, slots=True)
class Commitment:
    id: str
    what: str
    said: str
    when: str = ""
    at: str = ""
    settled: str = ""
    cited: tuple[str, ...] = ()
    unresolved: str = ""


def today() -> date:
    return date.fromisoformat(Commitments.TODAY)


def dated(message) -> bool:
    return bool(re.search(Commitments.DATED, f"{message.subject} {message.body}", re.I))


def waiting(store, decisions) -> list:
    refused = {one.id for one in decisions
               if one.by is not Decided.MODEL
               or one.disposition is Disposition.QUARANTINE}
    return [message for message in store.messages
            if message.id not in refused and dated(message)]


def clocked(text: str) -> str:
    found = re.search(Commitments.CLOCK, text, re.I)
    if not found:
        return ""
    hour = int(found.group(1)) % 12
    if found.group(3).lower() == "pm":
        hour += 12
    return f"{hour:02d}:{int(found.group(2) or 0):02d}"


def ordinal(text: str) -> date | None:
    found = re.search(Commitments.ORDINAL, text, re.I)
    if not found:
        return None
    return onward(int(found.group(1)))


def onward(day: int) -> date | None:
    here = today()
    try:
        soon = here.replace(day=day)
    except ValueError:
        return None
    if soon >= here:
        return soon
    month = here.month % 12 + 1
    year = here.year + (1 if month == 1 else 0)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def named(text: str) -> date | None:
    found = re.search(Commitments.NAMED, text, re.I)
    if not found:
        return None
    month = ["january", "february", "march", "april", "may", "june", "july", "august",
             "september", "october", "november", "december"].index(found.group(1).lower()) + 1
    try:
        return date(today().year, month, int(found.group(2)))
    except ValueError:
        return None


def weekday(text: str) -> date | None:
    lowered = text.lower()
    for number, name in enumerate(Commitments.WEEKDAYS):
        if name in lowered:
            here = today()
            ahead = (number - here.weekday()) % 7 or 7
            return here + timedelta(days=ahead)
    return None


def closing(text: str) -> date | None:
    if not re.search(Commitments.MONTH_END, text, re.I):
        return None
    here = today()
    month = here.month % 12 + 1
    year = here.year + (1 if month == 1 else 0)
    return date(year, month, 1) - timedelta(days=1)


def soon(text: str) -> date | None:
    if re.search(Commitments.TODAY_WORDS, text, re.I):
        return today()
    if re.search(Commitments.TOMORROW, text, re.I):
        return today() + timedelta(days=1)
    return None


def settled(text: str) -> date | None:
    for reader in (named, ordinal, closing, soon, weekday):
        found = reader(text)
        if found is not None:
            return found
    return None


def relative(text: str) -> tuple[int, str, str] | None:
    found = re.search(Commitments.RELATIVE, text, re.I)
    if not found:
        return None
    count = Commitments.COUNTS.get(found.group(1).lower())
    if count is None and found.group(1).isdigit():
        count = int(found.group(1))
    if count is None:
        return None
    days = count * (7 if found.group(2).lower().startswith("week") else 1)
    return days, found.group(3).lower(), found.group(4).strip(" .?")


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z]+", text.lower())
            if len(word) >= Commitments.SHORTEST}


def anchor(phrase: str, others) -> Commitment | None:
    wanted = words(phrase)
    best, most = None, 0
    for other in others:
        if not other.when:
            continue
        shared = len(wanted & words(other.what))
        if shared > most:
            best, most = other, shared
    return best


def read(answer, store) -> list[Commitment]:
    found = []
    for record in answer or ():
        name = str(record.get("id") or "")
        said = str(record.get("when") or "").strip()
        what = str(record.get("what") or "").strip()
        if name not in store.ids or not said or not what:
            continue
        try:
            standing = Settled(record.get("settled"))
        except ValueError:
            standing = Settled.OWED
        found.append(Commitment(id=name, what=what, said=said, settled=str(standing),
                                cited=(name,)))
    return found


def placed(raw: list[Commitment]) -> list[Commitment]:
    fixed = []
    for one in raw:
        when = settled(one.said)
        if when is None:
            fixed.append(one)
            continue
        fixed.append(Commitment(id=one.id, what=one.what, said=one.said,
                                when=when.isoformat(), at=clocked(one.said),
                                settled=one.settled, cited=one.cited))
    return fixed


def joined(fixed: list[Commitment]) -> list[Commitment]:
    done = []
    for one in fixed:
        if one.when:
            done.append(one)
            continue
        moved = relative(one.said)
        if moved is None:
            done.append(Commitment(id=one.id, what=one.what, said=one.said,
                                   settled=one.settled, cited=one.cited,
                                   unresolved=Commitments.NOTHING.format(said=one.said)))
            continue
        days, way, phrase = moved
        held = anchor(phrase, fixed)
        if held is None:
            done.append(Commitment(id=one.id, what=one.what, said=one.said,
                                   settled=one.settled, cited=one.cited,
                                   unresolved=Commitments.NOTHING.format(said=one.said)))
            continue
        shift = timedelta(days=days if way == "after" else -days)
        done.append(Commitment(
            id=one.id, what=one.what,
            said=Commitments.ANCHORED.format(days=days, way=way, anchor=held.what),
            when=(date.fromisoformat(held.when) + shift).isoformat(),
            at=one.at, settled=one.settled, cited=tuple(dict.fromkeys(one.cited + held.cited))))
    return done


def same(one: Commitment, other: Commitment) -> bool:
    return (one.when == other.when and one.at == other.at
            and bool(words(one.what) & words(other.what)))


def merged(found: list[Commitment]) -> list[Commitment]:
    kept = []
    for one in found:
        twin = next((held for held in kept if held.when and same(held, one)), None)
        if twin is None:
            kept.append(one)
            continue
        kept[kept.index(twin)] = Commitment(
            id=twin.id, what=twin.what, said=twin.said, when=twin.when, at=twin.at,
            settled=twin.settled, cited=tuple(dict.fromkeys(twin.cited + one.cited)))
    return kept


def clashes(found: list[Commitment]) -> list[tuple[Commitment, Commitment]]:
    seen = {}
    pairs = []
    for one in sorted(found, key=lambda c: (c.when, c.at, c.id)):
        if not one.when or not one.at:
            continue
        key = (one.when, one.at)
        if key in seen:
            pairs.append((seen[key], one))
        else:
            seen[key] = one
    return pairs


def clash(pair) -> str:
    one, other = pair
    return Commitments.CLASH.format(what=f"{one.what} ({one.id}) and {other.what} ({other.id})",
                                    when=f"{one.when} {one.at}")


def gather(store, decisions, ask=None) -> list[Commitment]:
    if ask is None:
        import llm
        ask = llm.ask

    left = waiting(store, decisions)
    raw = []
    for start in range(0, len(left), Commitments.BATCH):
        group = left[start:start + Commitments.BATCH]
        raw.extend(read(ask(prompts.DIARY_SYSTEM, prompts.diary(group), prompts.DIARY_SHAPE),
                        store))
    return sorted(merged(joined(placed(raw))), key=lambda c: (c.when or "9999", c.at, c.id))
