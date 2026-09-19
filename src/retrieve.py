# cert-aai-2026-06-0061  Sarath Chandra
#
# - Finds the earlier mail that could answer a reply, inside its conversation and outside it
# - Ranks the outside mail by rare shared words, which measured better than ranking by meaning
# - Keeps the meaning-based ranking alongside it, unused, so the comparison stays reproducible
# - Only ever offers messages that genuinely came first, so a citation can never point forward

import json
import math
import re
from collections import Counter
from constants import Paths, Retrieval
from store import Message, Store


def spoken(message: Message) -> str:
    return f"{message.subject}\n{message.body}"


def words(text: str) -> set[str]:
    found = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in found
            if word not in Retrieval.STOPWORDS and len(word) > Retrieval.MINIMUM_WORD - 1}


def weights(store: Store) -> dict:
    seen = Counter()
    for message in store.messages:
        seen.update(words(spoken(message)))
    return {word: math.log(len(store) / (1 + count)) for word, count in seen.items()}


def stored() -> dict:
    if not Paths.VECTORS.exists():
        return {}
    return json.loads(Paths.VECTORS.read_text())


def written(store: Store, embed=None) -> dict:
    if embed is None:
        import llm
        embed = llm.embed

    held = {}
    messages = list(store.messages)
    for start in range(0, len(messages), Retrieval.EMBED_BATCH):
        group = messages[start:start + Retrieval.EMBED_BATCH]
        for message, vector in zip(group, embed([spoken(one) for one in group])):
            held[message.id] = vector
    Paths.VECTORS.write_text(json.dumps(held) + "\n")
    return held


def alike(one: list, other: list) -> float:
    return sum(a * b for a, b in zip(one, other)) / (
        math.sqrt(sum(a * a for a in one)) * math.sqrt(sum(b * b for b in other)))


def earlier(store: Store, message: Message) -> tuple[Message, ...]:
    thread = store.thread(message.thread_id)
    return thread[:thread.index(message)]


def outsiders(store: Store, message: Message):
    inside = {found.id for found in store.thread(message.thread_id)}
    return [other for other in store.messages
            if other.id not in inside and other.timestamp < message.timestamp]


def ranked(scored, limit: int) -> tuple:
    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    return tuple(found for _, found in scored[:limit])


def worded(store: Store, message: Message, limit: int = Retrieval.CANDIDATES) -> tuple:
    weighted = weights(store)
    mine = words(spoken(message))
    scored = []
    for other in outsiders(store, message):
        shared = mine & words(spoken(other))
        if shared:
            scored.append((sum(weighted[word] for word in shared), other))
    return ranked(scored, limit)


def meant(store: Store, message: Message, limit: int = Retrieval.CANDIDATES) -> tuple:
    held = stored()
    if message.id not in held:
        return ()
    scored = [(alike(held[message.id], held[other.id]), other)
              for other in outsiders(store, message) if other.id in held]
    return ranked(scored, limit)


def nearby(store: Store, message: Message, limit: int = Retrieval.CANDIDATES) -> tuple:
    return worded(store, message, limit)


def offered(store: Store, message: Message) -> set[str]:
    return ({found.id for found in earlier(store, message)} |
            {found.id for found in nearby(store, message)})
