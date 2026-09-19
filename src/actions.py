# cert-aai-2026-06-0061  Sarath Chandra
#
# - The only place in the system that changes anything outside a run artifact
# - Every function here asks the gate first, so there is one door and it is watched
# - Sending writes one file to outbox/ and writes nowhere else
# - Deleting keeps the whole message in trash/ before it touches the mailbox, so the mail is
#   recoverable even if the machine dies between the two writes


from pathlib import Path

import json
from datetime import datetime

import gate
import store
from constants import Action, Actions, Inbox, Paths
from drafts import Draft
from store import Message


def subject(message: Message) -> str:
    if message.subject.lower().startswith("re:"):
        return message.subject
    return f"Re: {message.subject}"


def letter(draft: Draft, message: Message) -> str:
    values = (message.sender, Inbox.OWNER, subject(message), message.id,
              ", ".join(draft.cited) or "nothing, the sender's own words only")
    headers = "\n".join(f"{name}: {value}"
                        for name, value in zip(Actions.HEADERS, values))
    return f"{headers}\n\n{draft.body}\n"


def where(name: str) -> Path:
    return Paths.OUTBOX / f"{name}{Actions.SUFFIX}"


def named(path: Path) -> str:
    try:
        return str(path.relative_to(Paths.ROOT))
    except ValueError:
        return f"{path.parent.name}/{path.name}"


def send(draft: Draft, message: Message, ask=None) -> gate.Verdict:
    target = where(message.id)
    proposal = gate.Proposal(action=Action.SEND, id=message.id,
                             detail=f"reply to {message.sender} about {message.subject!r}",
                             target=named(target), preview=draft.body.strip())
    if draft.refused or not draft.body.strip():
        return gate.refuse(proposal, Actions.UNSENDABLE)

    verdict = gate.asked(proposal, ask)
    if not verdict.went_ahead:
        return gate.written(verdict)

    Paths.OUTBOX.mkdir(parents=True, exist_ok=True)
    target.write_text(letter(draft, message))
    return gate.settled(verdict, f"wrote {named(target)}")


def sent() -> tuple[str, ...]:
    if not Paths.OUTBOX.exists():
        return ()
    return tuple(sorted(path.stem for path in Paths.OUTBOX.glob(f"*{Actions.SUFFIX}")))


def carried() -> list[dict]:
    return json.loads(store.mailbox().read_text())


def keep(records: list[dict]) -> None:
    Paths.MAILBOX.write_text(json.dumps(records, indent=2) + "\n")


def kept(name: str) -> Path:
    return Paths.TRASH / f"{name}{Actions.KEPT}"


def held() -> tuple[str, ...]:
    if not Paths.TRASH.exists():
        return ()
    return tuple(sorted(path.stem for path in Paths.TRASH.glob(f"*{Actions.KEPT}")))


def remove(name: str, why: str, ask=None) -> gate.Verdict:
    proposal = gate.Proposal(action=Action.DELETE, id=name,
                             detail=f"take {name} out of the mailbox because {why}",
                             target=named(kept(name)))
    records = carried()
    standing = [record for record in records if record["id"] == name]
    if not standing:
        return gate.refuse(proposal, Actions.ABSENT.format(id=name))

    guarding = gate.protects(name)
    if guarding:
        return gate.refuse(proposal, guarding)

    verdict = gate.asked(proposal, ask)
    if not verdict.went_ahead:
        return gate.written(verdict)

    Paths.TRASH.mkdir(parents=True, exist_ok=True)
    kept(name).write_text(json.dumps({"at": datetime.now().isoformat(timespec="seconds"),
                                      "why": why,
                                      "position": records.index(standing[0]),
                                      "message": standing[0]}, indent=2) + "\n")
    keep([record for record in records if record["id"] != name])
    return gate.settled(verdict, f"moved to {named(kept(name))}, mailbox now holds "
                                f"{len(records) - 1}")


def restore(name: str, ask=None) -> gate.Verdict:
    proposal = gate.Proposal(action=Action.RESTORE, id=name,
                             detail=f"put {name} back into the mailbox",
                             target=named(Paths.MAILBOX))
    if not kept(name).exists():
        return gate.refuse(proposal, Actions.HELD.format(id=name))

    records = carried()
    if any(record["id"] == name for record in records):
        return gate.refuse(proposal, Actions.ALREADY.format(id=name))

    verdict = gate.asked(proposal, ask)
    if not verdict.went_ahead:
        return gate.written(verdict)

    saved = json.loads(kept(name).read_text())
    records.insert(min(saved["position"], len(records)), saved["message"])
    keep(records)
    kept(name).unlink()
    return gate.settled(verdict, f"back in the mailbox, which now holds {len(records)}")
