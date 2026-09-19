# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves nothing reaches outbox/ without a person saying yes, and that every answer is logged
# - Proves the mail the assignment shipped is never written to, whatever a run does
# - Proves a dry run shows the whole proposal and still writes nothing

import hashlib
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import actions
import gate
from constants import Action, Answer, Gate, Paths, Risk
from drafts import Draft
from store import load, mailbox
from utils import heading, rule

REPLY = "m043"
GOOD = Draft(id=REPLY, body="I cannot accept the 9:00am.", cited=("m041",))
REFUSED = Draft(id=REPLY, refused="no earlier mail bears on this")


@contextmanager
def elsewhere():
    outbox, approvals = Paths.OUTBOX, Paths.APPROVALS
    with tempfile.TemporaryDirectory() as room:
        Paths.OUTBOX = Path(room) / "outbox"
        Paths.APPROVALS = Path(room) / "approvals.jsonl"
        try:
            yield Path(room)
        finally:
            Paths.OUTBOX, Paths.APPROVALS = outbox, approvals


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_vocabulary() -> list[str]:
    problems = []
    if len(Risk) != 2:
        problems.append(f"there are {len(Risk)} risk classes, not 2")
    missing = [name for name in Action if name not in Gate.RISK]
    if missing:
        problems.append(f"{', '.join(missing)} carry no reversibility classification")
    if gate.risk(Action.SEND) != Risk.IRREVERSIBLE:
        problems.append("sending is not classified as irreversible")
    if gate.risk(Action.DELETE) != Risk.REVERSIBLE:
        problems.append("deleting is not classified as reversible")
    for name in (Action.SEND, Action.DELETE):
        if not gate.guarded(name):
            problems.append(f"{name} can happen without anybody approving it")
    if gate.guarded(Action.RESTORE):
        problems.append("putting a message back needs approval, which nobody would read")
    return problems


def check_dry_run() -> list[str]:
    problems = []
    with elsewhere():
        store = load()
        verdict = actions.send(GOOD, store.message(REPLY))
        if verdict.answer != Answer.DRY:
            problems.append(f"a run with nobody to ask answered {verdict.answer}")
        if verdict.went_ahead:
            problems.append("a dry run went ahead")
        if actions.sent():
            problems.append(f"a dry run wrote {', '.join(actions.sent())} to outbox/")
        if f"outbox/{REPLY}" not in verdict.outcome:
            problems.append(f"a dry run did not name what it would write: {verdict.outcome!r}")
        if len(gate.records()) != 1:
            problems.append(f"a dry run logged {len(gate.records())} records, not 1")
    return problems


def check_declined() -> list[str]:
    problems = []
    with elsewhere():
        store = load()
        verdict = actions.send(GOOD, store.message(REPLY), ask=lambda proposal: False)
        if verdict.answer != Answer.DECLINED:
            problems.append(f"a refused proposal answered {verdict.answer}")
        if actions.sent():
            problems.append("a declined send still wrote to outbox/")
        if gate.records()[-1]["answer"] != str(Answer.DECLINED):
            problems.append("the log does not say the person declined")
    return problems


def check_approved() -> list[str]:
    problems = []
    with elsewhere():
        store = load()
        message = store.message(REPLY)
        verdict = actions.send(GOOD, message, ask=lambda proposal: True)
        if verdict.answer != Answer.APPROVED:
            problems.append(f"an approved proposal answered {verdict.answer}")
        if actions.sent() != (REPLY,):
            problems.append(f"outbox/ holds {actions.sent()}, not just {REPLY}")

        written = actions.where(REPLY).read_text()
        for wanted in (message.sender, GOOD.body, "m041"):
            if wanted not in written:
                problems.append(f"the sent file does not carry {wanted!r}")
        if written.count(GOOD.body) != 1:
            problems.append("the sent file repeats the body")

        record = gate.records()[-1]
        for field in ("proposed", "answer", "outcome"):
            if not record.get(field):
                problems.append(f"the approval record has no {field}")
        if record["risk"] != str(Risk.IRREVERSIBLE):
            problems.append("the approval record does not call sending irreversible")
    return problems


def check_unsendable() -> list[str]:
    problems = []
    with elsewhere():
        store = load()
        verdict = actions.send(REFUSED, store.message(REPLY), ask=lambda proposal: True)
        if verdict.answer != Answer.REFUSED:
            problems.append(f"a refused draft answered {verdict.answer}, not refused")
        if actions.sent():
            problems.append("a refused draft was sent anyway")
        if gate.records()[-1]["answer"] != str(Answer.REFUSED):
            problems.append("the gate did not log its own refusal")
    return problems


def check_reconciles() -> list[str]:
    problems = []
    with elsewhere():
        store = load()
        actions.send(GOOD, store.message(REPLY), ask=lambda proposal: True)
        actions.send(GOOD, store.message("m016"), ask=lambda proposal: False)
        approved = {record["id"] for record in gate.records()
                    if record["answer"] == str(Answer.APPROVED)}
        for name in actions.sent():
            if name not in approved:
                problems.append(f"outbox/ holds {name} with no approval behind it")
        if "m016" in actions.sent():
            problems.append("a declined send reached outbox/ anyway")
    return problems


def check_fixture() -> list[str]:
    problems = []
    before = digest(Paths.INBOX)
    with elsewhere():
        store = load()
        actions.send(GOOD, store.message(REPLY), ask=lambda proposal: True)
    if digest(Paths.INBOX) != before:
        problems.append("the inbox the assignment shipped was written to")

    shipped = {record["id"] for record in json.loads(Paths.INBOX.read_text())}
    working = {record["id"] for record in json.loads(mailbox().read_text())}
    for name in sorted(shipped - working):
        problems.append(f"{name} is missing from the working mailbox and nothing deleted it")
    for name in sorted(working - shipped):
        problems.append(f"{name} is in the working mailbox but was never shipped")
    return problems


def run() -> bool:
    heading("inboxHero gate check")
    problems = []
    for name, check in (("vocabulary", check_vocabulary), ("dry run", check_dry_run),
                        ("declined", check_declined), ("approved", check_approved),
                        ("unsendable", check_unsendable), ("reconciles", check_reconciles),
                        ("fixture", check_fixture)):
        found = check()
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
