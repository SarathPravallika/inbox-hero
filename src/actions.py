# cert-aai-2026-06-0061  Sarath Chandra
#
# - The only place in the system that changes anything outside a run artifact
# - Every function here asks the gate first, so there is one door and it is watched
# - Sending writes one file to outbox/ and writes nowhere else


from pathlib import Path

import gate
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
                             target=named(target))
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
