# cert-aai-2026-06-0061  Sarath Chandra
#
# - Records the standing instructions the owner states in his own mail
# - A preference is a typed record, never free text, so it can say only certain things
# - A message asking to be remembered is refused unless it fits one of those shapes
# - Every recorded preference names the message it came from, so it can always be traced back

import json
import re
from dataclasses import asdict, dataclass
from constants import Kind, Memory, Paths
from store import Message, Store


@dataclass(frozen=True, slots=True)
class Preference:
    kind: str = ""
    subject: str = ""
    value: str = ""
    said: str = ""
    source: str = ""
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


def scheduled(message: Message, store: Store) -> tuple[str, str]:
    found = clocked(spoken(message))
    return (Memory.MEETINGS, found) if found else ("", "")


def copied(message: Message, store: Store) -> tuple[str, str]:
    found = about(spoken(message), store)
    return (found, message.sender) if found else ("", "")


SHAPES = {Kind.SCHEDULING: scheduled, Kind.COPYING: copied}


def remember(kind: str, message: Message, store: Store) -> Preference:
    source = Memory.SOURCE.format(id=message.id)
    if kind not in tuple(Kind):
        return Preference(source=source, refused=Memory.UNKNOWN.format(kind=kind))

    wanted = Kind(kind)
    subject, value = SHAPES[wanted](message, store)
    if not subject or not value:
        return Preference(kind=wanted, source=source,
                          refused=Memory.SHAPELESS.format(kind=wanted,
                                                          wanted=Memory.WANTED[wanted]))

    needle = flattened(value if wanted is Kind.SCHEDULING else subject.split(".")[0])
    return Preference(kind=wanted, subject=subject, value=value,
                      said=sentence(spoken(message), needle), source=source)


def held() -> tuple[Preference, ...]:
    if not Paths.MEMORY.exists():
        return ()
    return tuple(Preference(**record) for record in json.loads(Paths.MEMORY.read_text()))


def keep(preferences) -> tuple[Preference, ...]:
    merged = {found.source: found for found in held()}
    for found in preferences:
        if not found.refused:
            merged[found.source] = found
    standing = tuple(merged.values())
    Paths.MEMORY.write_text(json.dumps([asdict(one) for one in standing], indent=2) + "\n")
    return standing


def recall(kind: str = None) -> tuple[Preference, ...]:
    return tuple(one for one in held() if kind is None or one.kind == kind)


def forget() -> None:
    if Paths.MEMORY.exists():
        Paths.MEMORY.unlink()
