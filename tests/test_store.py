# cert-aai-2026-06-0061  Sarath Chandra

from dataclasses import FrozenInstanceError, fields
from store import Message, load
from utils import heading, rule

COUNT = 100
THREADS = 88
API_ORDER = ("m001", "m003", "m005", "m008")
LAUNCH_ORDER = ("m026", "m027", "m028", "m029", "m030", "m033", "m034", "m035", "m036")
NAMES = {"id", "thread_id", "sender", "to", "subject", "timestamp", "body", "unread"}

def check_load(store) -> list[str]:
    problems = []
    if len(store) != COUNT:
        problems.append(f"the store holds {len(store)} messages, not {COUNT}")
    if len(store.ids) != COUNT:
        problems.append(f"{COUNT - len(store.ids)} message ids collided")
    if len(store.threads) != THREADS:
        problems.append(f"the store holds {len(store.threads)} threads, not {THREADS}")
    return problems


def check_fields(store) -> list[str]:
    problems = []
    named = {field.name for field in fields(Message)}
    if named != NAMES:
        problems.append(f"Message carries {', '.join(sorted(named))}")
    if store.message("m001").sender != "raghav@paperjet.io":
        problems.append("sender does not carry what the inbox called from")
    for message in store.messages:
        if not isinstance(message.unread, bool):
            problems.append(f"{message.id} has unread {message.unread!r}, not a boolean")
        if not message.id or not message.thread_id or not message.timestamp:
            problems.append(f"{message.id or '?'} is missing an id, thread or timestamp")
    return problems


def check_threads(store) -> list[str]:
    problems = []
    if tuple(m.id for m in store.thread("t-api")) != API_ORDER:
        problems.append(f"t-api is {', '.join(m.id for m in store.thread('t-api'))}")
    if tuple(m.id for m in store.thread("t-launch")) != LAUNCH_ORDER:
        problems.append(f"t-launch is {', '.join(m.id for m in store.thread('t-launch'))}")
    for name, group in store.threads.items():
        stamps = [message.timestamp for message in group]
        if stamps != sorted(stamps):
            problems.append(f"thread {name} is not oldest first")
    for message in store.messages:
        if message not in store.thread(message.thread_id):
            problems.append(f"{message.id} is missing from its own thread {message.thread_id}")
    return problems


def check_lookups(store) -> list[str]:
    problems = []
    try:
        store.message("m999")
        problems.append("message() accepted an id that is not in the inbox")
    except KeyError:
        pass
    try:
        store.thread("t-nothing")
        problems.append("thread() accepted a thread that is not in the inbox")
    except KeyError:
        pass
    try:
        store.message("m001").body = "changed"
        problems.append("a Message can be edited after loading")
    except FrozenInstanceError:
        pass
    return problems


def run() -> bool:
    heading("inboxHero store check")
    store = load()
    problems = []
    for name, check in (("load", check_load), ("fields", check_fields),
                        ("threads", check_threads), ("lookups", check_lookups)):
        found = check(store)
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
