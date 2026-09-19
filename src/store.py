# cert-aai-2026-06-0061  Sarath Chandra
#
# - Loads the inbox and makes it answerable by message and by conversation
# - Messages cannot be edited once loaded, so nothing can rewrite mail during a run

import json
from dataclasses import dataclass
from pathlib import Path
from constants import Inbox, Paths


@dataclass(frozen=True, slots=True)
class Message:
    id: str
    thread_id: str
    sender: str
    to: str
    subject: str
    timestamp: str
    body: str
    unread: bool


class Store:
    def __init__(self, messages):
        self.messages = tuple(messages)
        self.ids = {message.id: message for message in self.messages}

        grouped = {}
        for message in sorted(self.messages, key=lambda message: message.timestamp):
            grouped.setdefault(message.thread_id, []).append(message)
        self.threads = {name: tuple(group) for name, group in grouped.items()}

    def __len__(self) -> int:
        return len(self.messages)

    def message(self, name: str) -> Message:
        if name not in self.ids:
            raise KeyError(f"there is no message {name}")
        return self.ids[name]

    def thread(self, name: str) -> tuple[Message, ...]:
        if name not in self.threads:
            raise KeyError(f"there is no thread {name}")
        return self.threads[name]


def read(record: dict) -> Message:
    return Message(**{Inbox.FIELDS.get(key, key): value for key, value in record.items()})


def load(path: Path = Paths.INBOX) -> Store:
    return Store(read(record) for record in json.loads(path.read_text()))
