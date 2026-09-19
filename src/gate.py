# cert-aai-2026-06-0061  Sarath Chandra
#
# - Decides which actions a person has to approve before they happen
# - Classifies every action as reversible or not, and that classification is code, not prose
# - Writes the approval record: what was proposed, what the person said, what happened
# - No message text can widen what this permits, because the policy is not data

import json
from dataclasses import dataclass, replace
from datetime import datetime
from constants import Action, Answer, Gate, Paths, Risk


@dataclass(frozen=True, slots=True)
class Proposal:
    action: Action
    id: str
    detail: str
    target: str = ""


@dataclass(frozen=True, slots=True)
class Verdict:
    proposal: Proposal
    answer: Answer
    outcome: str

    @property
    def went_ahead(self) -> bool:
        return self.answer in (Answer.APPROVED, Answer.UNATTENDED)


def risk(action: Action) -> Risk:
    return Gate.RISK[Action(action)]


def guarded(action: Action) -> bool:
    return Action(action) in Gate.APPROVAL


def prompt(proposal: Proposal) -> bool:
    print(f"  {proposal.action} {proposal.id}: {proposal.detail}")
    return input(Gate.ASKED.format(action=proposal.action)).strip().lower() in ("y", "yes")


def refuse(proposal: Proposal, why: str) -> Verdict:
    return written(Verdict(proposal=proposal, answer=Answer.REFUSED, outcome=why))


def asked(proposal: Proposal, ask=None) -> Verdict:
    if not guarded(proposal.action):
        return Verdict(proposal=proposal, answer=Answer.UNATTENDED, outcome="")
    if ask is None:
        return Verdict(proposal=proposal, answer=Answer.DRY,
                       outcome=Gate.SHOWN.format(target=proposal.target or Gate.NOTHING))
    if not ask(proposal):
        return Verdict(proposal=proposal, answer=Answer.DECLINED, outcome=Gate.DECLINED)
    return Verdict(proposal=proposal, answer=Answer.APPROVED, outcome="")


def written(verdict: Verdict) -> Verdict:
    Paths.APPROVALS.parent.mkdir(parents=True, exist_ok=True)
    with open(Paths.APPROVALS, "a") as handle:
        handle.write(json.dumps({
            "at": datetime.now().isoformat(timespec="seconds"),
            "action": str(verdict.proposal.action),
            "id": verdict.proposal.id,
            "risk": str(risk(verdict.proposal.action)),
            "approval": "required" if guarded(verdict.proposal.action) else "not required",
            "proposed": verdict.proposal.detail,
            "answer": str(verdict.answer),
            "outcome": verdict.outcome,
        }) + "\n")
    return verdict


def settled(verdict: Verdict, outcome: str) -> Verdict:
    return written(replace(verdict, outcome=outcome))


def records() -> list[dict]:
    if not Paths.APPROVALS.exists():
        return []
    return [json.loads(line) for line in Paths.APPROVALS.read_text().splitlines() if line]


def start() -> None:
    Paths.APPROVALS.write_text("")
