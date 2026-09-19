# cert-aai-2026-06-0061  Sarath Chandra
#
# - Records the standing instructions the owner states in his own mail
# - A preference is a typed record, never free text, so it can say only certain things
# - A message asking to be remembered is refused unless it fits one of those shapes
# - Every recorded preference names the message it came from and when it was first written,
#   so a later run can show that what it obeyed predates it
# - What the model is told is built from a template and the checked fields, never from the
#   sentence the mail used, so a preference cannot carry an instruction along with it

import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from constants import Kind, Memory, Paths
from store import Message, Store


@dataclass(frozen=True, slots=True)
class Preference:
    kind: str = ""
    subject: str = ""
    value: str = ""
    bound: str = ""
    said: str = ""
    source: str = ""
    at: str = ""
    refused: str = ""


def flattened(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def spoken(message: Message) -> str:
    return f"{message.subject}\n{message.body}"


def clocked(text: str) -> str:
    found = re.search(Memory.CLOCK, text, re.I)
    return found.group(0).strip() if found else ""


def domains(store: Store) -> dict[str, str]:
    found = {}
    for message in store.messages:
        if "@" in message.sender:
            whole = message.sender.rsplit("@", 1)[-1].lower()
            found[whole.split(".")[0]] = whole
    return found


def about(text: str, store: Store) -> str:
    squashed = flattened(text)
    known = sorted(domains(store).items(), key=lambda pair: -len(pair[0]))
    for label, whole in known:
        if len(label) >= Memory.SHORTEST and label in squashed:
            return whole
    return ""


def sentence(text: str, needle: str) -> str:
    for part in re.split(r"(?<=[.!?])\s+|\n+", text):
        if needle and needle in flattened(part):
            return part.strip()
    return ""


def bounded(text: str, value: str) -> str:
    place = text.lower().find(value.lower())
    if place < 0:
        return ""
    run = text[max(0, place - Memory.REACH):place].lower()
    seen = [(run.rfind(word), word) for word in Memory.BOUNDS if word in run]
    return Memory.OPPOSITE[max(seen)[1]] if seen else ""


def scheduled(message: Message, store: Store) -> tuple[str, str, str]:
    text = spoken(message)
    found = clocked(text)
    bound = bounded(text, found) if found else ""
    return (Memory.MEETINGS, found, bound) if found and bound else ("", "", "")


def copied(message: Message, store: Store) -> tuple[str, str, str]:
    found = about(spoken(message), store)
    return (found, message.sender, "") if found else ("", "", "")


SHAPES = {Kind.SCHEDULING: scheduled, Kind.COPYING: copied}


def instruction(preference: Preference) -> str:
    return Memory.SAYS[Kind(preference.kind)].format(
        subject=preference.subject, value=preference.value,
        bound=preference.bound).replace("  ", " ")


def came_from(preference: Preference) -> str:
    return preference.source.removeprefix(Memory.FROM)


def sources(preferences) -> set[str]:
    return {came_from(one) for one in preferences if one.source}


def copies(message: Message, preferences) -> tuple[str, ...]:
    whole = message.sender.rsplit("@", 1)[-1].lower()
    return tuple(one.value for one in preferences
                 if one.kind == Kind.COPYING and one.subject == whole)


def remember(kind: str, message: Message, store: Store) -> Preference:
    source = Memory.SOURCE.format(id=message.id)
    if kind not in tuple(Kind):
        return Preference(source=source, refused=Memory.UNKNOWN.format(kind=kind))

    wanted = Kind(kind)
    subject, value, bound = SHAPES[wanted](message, store)
    if not subject or not value:
        return Preference(kind=wanted, source=source,
                          refused=Memory.SHAPELESS.format(kind=wanted,
                                                          wanted=Memory.WANTED[wanted]))

    needle = flattened(value if wanted is Kind.SCHEDULING else subject.split(".")[0])
    return Preference(kind=wanted, subject=subject, value=value, bound=bound,
                      said=sentence(spoken(message), needle), source=source,
                      at=datetime.now().isoformat(timespec="seconds"))


def held() -> tuple[Preference, ...]:
    if not Paths.MEMORY.exists():
        return ()
    return tuple(Preference(**record) for record in json.loads(Paths.MEMORY.read_text()))


def keep(preferences) -> tuple[Preference, ...]:
    merged = {found.source: found for found in held()}
    for found in preferences:
        if found.refused:
            continue
        standing = merged.get(found.source)
        merged[found.source] = replace(found, at=standing.at if standing else found.at)
    standing = tuple(merged.values())
    Paths.MEMORY.write_text(json.dumps([asdict(one) for one in standing], indent=2) + "\n")
    return standing


def recall(kind: str = None) -> tuple[Preference, ...]:
    return tuple(one for one in held() if kind is None or one.kind == kind)


def forget() -> None:
    if Paths.MEMORY.exists():
        Paths.MEMORY.unlink()
