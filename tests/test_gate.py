# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves nothing reaches outbox/ without a person saying yes, and that every answer is logged
# - Proves the mail the assignment shipped is never written to, whatever a run does
# - Proves a dry run shows the whole proposal and still writes nothing
# - Proves a deleted message comes back exactly as it was, and that hostile mail never goes

import hashlib
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

import actions
import gate
from constants import Action, Actions, Answer, Gate, Paths, Risk
from drafts import Draft
from store import load, mailbox
from utils import heading, rule

REPLY = "m043"
GOOD = Draft(id=REPLY, body="I cannot accept the 9:00am.", cited=("m041",))
REFUSED = Draft(id=REPLY, refused="no earlier mail bears on this")


WATCHED = ("OUTBOX", "APPROVALS", "MAILBOX", "TRASH", "RUN")
HOSTILE = "m024"
NOISE = "m113"


@contextmanager
def elsewhere(triaged=True):
    held = {name: getattr(Paths, name) for name in WATCHED}
    with tempfile.TemporaryDirectory() as room:
        Paths.OUTBOX = Path(room) / "outbox"
        Paths.APPROVALS = Path(room) / "approvals.jsonl"
        Paths.MAILBOX = Path(room) / "mailbox.json"
        Paths.TRASH = Path(room) / "trash"
        Paths.RUN = Path(room) / "run.json"
        if triaged:
            Paths.RUN.write_text(json.dumps({"decisions": [
                {"id": record["id"],
                 "disposition": "quarantine" if record["id"] == HOSTILE else "archive"}
                for record in json.loads(Paths.INBOX.read_text())]}))
        try:
            yield Path(room)
        finally:
            for name, path in held.items():
                setattr(Paths, name, path)


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


def check_protected() -> list[str]:
    problems = []
    with elsewhere():
        verdict = actions.remove(HOSTILE, "it looks like spam", ask=lambda proposal: True)
        if verdict.answer != Answer.REFUSED:
            problems.append(f"quarantined mail answered {verdict.answer} to a delete")
        if verdict.outcome != Gate.PROTECTED:
            problems.append(f"the refusal reads {verdict.outcome!r}")
        if HOSTILE not in {record["id"] for record in actions.carried()}:
            problems.append(f"{HOSTILE} left the mailbox despite the refusal")
        if actions.held():
            problems.append("a refused delete still wrote to trash/")

        gone = actions.remove("m999", "it does not exist", ask=lambda proposal: True)
        if gone.answer != Answer.REFUSED:
            problems.append("deleting a message that is not there was not refused")

    with elsewhere(triaged=False):
        verdict = actions.remove(NOISE, "clearing noise", ask=lambda proposal: True)
        if verdict.answer != Answer.REFUSED:
            problems.append("a message was deleted before anything had triaged it")
        if verdict.outcome != Gate.UNTRIAGED:
            problems.append(f"the untriaged refusal reads {verdict.outcome!r}")
    return problems


def check_deleted() -> list[str]:
    problems = []
    with elsewhere():
        before = len(actions.carried())
        if actions.remove(NOISE, "clearing noise").answer != Answer.DRY:
            problems.append("a delete with nobody to ask was not a dry run")
        if len(actions.carried()) != before or actions.held():
            problems.append("a dry run deleted something anyway")

        if actions.remove(NOISE, "clearing noise", ask=lambda p: False).answer != Answer.DECLINED:
            problems.append("a declined delete did not answer declined")
        if len(actions.carried()) != before:
            problems.append("a declined delete took the message anyway")

        verdict = actions.remove(NOISE, "clearing noise", ask=lambda proposal: True)
        if verdict.answer != Answer.APPROVED:
            problems.append(f"an approved delete answered {verdict.answer}")
        if actions.held() != (NOISE,):
            problems.append(f"trash/ holds {actions.held()}, not just {NOISE}")
        if NOISE in {record["id"] for record in actions.carried()}:
            problems.append(f"{NOISE} is still in the mailbox after being deleted")
        if len(actions.carried()) != before - 1:
            problems.append(f"the mailbox holds {len(actions.carried())}, not {before - 1}")

        saved = json.loads(actions.kept(NOISE).read_text())
        if saved["message"]["id"] != NOISE or not saved["message"].get("body"):
            problems.append("the trash record does not hold the whole message")
        if not saved.get("why") or "position" not in saved:
            problems.append("the trash record does not say why, or where it came from")
    return problems


def check_round_trip() -> list[str]:
    problems = []
    with elsewhere():
        start = actions.carried()
        actions.remove(NOISE, "clearing noise", ask=lambda proposal: True)
        verdict = actions.restore(NOISE)
        if verdict.answer != Answer.UNATTENDED:
            problems.append(f"putting a message back answered {verdict.answer}")
        if actions.carried() != start:
            problems.append("the mailbox did not come back exactly as it was")
        if actions.held():
            problems.append(f"trash/ still holds {actions.held()} after a restore")

        again = actions.restore(NOISE)
        if again.answer != Answer.REFUSED or again.outcome != Actions.HELD.format(id=NOISE):
            problems.append("restoring twice was not refused")

        answers = [record["answer"] for record in gate.records()]
        if answers.count(str(Answer.APPROVED)) != 1:
            problems.append(f"the log shows {answers.count(str(Answer.APPROVED))} approvals")
        if not any(record["action"] == str(Action.RESTORE) for record in gate.records()):
            problems.append("the restore was never logged")
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
                        ("protected", check_protected), ("deleted", check_deleted),
                        ("round trip", check_round_trip), ("fixture", check_fixture)):
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
