# cert-aai-2026-06-0061  Sarath Chandra

import json
from datetime import datetime
from constants import Paths


def stamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def start() -> None:
    Paths.TRACE.write_text("")


def record(cap: str, event: str, **fields) -> None:
    with open(Paths.TRACE, "a") as handle:
        handle.write(json.dumps({"at": stamp(), "cap": cap, "event": event, **fields}) + "\n")


def events() -> list[dict]:
    if not Paths.TRACE.exists():
        return []
    return [json.loads(line) for line in Paths.TRACE.read_text().splitlines() if line]
