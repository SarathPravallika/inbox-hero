# cert-aai-2026-06-0061  Sarath Chandra
#
# - The one command a grader runs to see any capability
# - Holds a completed run open so ten demonstrations cost one run of model calls
# - Refuses to start work if the model provider has not been configured
# - Asks about every irreversible action when a person is there to answer, and when nobody
#   is, shows what it would do and writes nothing

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from constants import (Actions, Answer, Capability, Dashboard, Decided, Digest,
                       Disposition, Followups, Guard, Kind, Offers, Paths, WIDTH,
                       Why)
from utils import heading, rule, wrap

def sibling(folder: str, module: str):
    path = str(ROOT / folder)

    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(module)


def keyed() -> None:
    settings = importlib.import_module("config")
    if settings.API_KEY and settings.MODEL:
        return
    print("API_KEY and MODEL both have to be set before inboxHero can put the inbox "
          "through a model.")
    raise SystemExit("Copy .env.example to .env and fill it in, then try again.")


def ensure_run(fresh: bool) -> dict:
    router = importlib.import_module("router")
    if Paths.RUN.exists() and not fresh:
        return router.stored()
    keyed()
    return router.run()


def listed() -> None:
    manifest = importlib.import_module("manifest")
    router = importlib.import_module("router")
    made = manifest.written(router.stored())

    heading(f"the manifest, written from the run of {router.stored()['at']}")
    for row in made["capabilities"]:
        print(f"  {row['id']}  {row['tier']}  {row['name']:<29}{row['command']}")
    rule()
    print(f"{len(made['capabilities'])} capabilities, "
          f"{made['system']['messages_processed']} messages processed, "
          f"{made['system']['rule_handled']} of them without a model")
    print(f"written to {Paths.MANIFEST.name}")


def cleaned() -> None:
    actions = importlib.import_module("actions")
    gate = importlib.import_module("gate")
    sent, held, logged = len(actions.sent()), len(actions.held()), len(gate.records())

    for folder, suffix in ((Paths.OUTBOX, Actions.SUFFIX), (Paths.TRASH, Actions.KEPT)):
        for path in folder.glob(f"*{suffix}") if folder.exists() else ():
            path.unlink()
    gate.start()
    print(Actions.CLEARED.format(sent=sent, held=held, logged=logged))


def zeroed(artifact: dict, args) -> None:
    only = args.msg
    heading("R1  every message carries one disposition and a reason")
    for decision in artifact["decisions"]:
        if only is not None and decision["id"] != only:
            continue
        print(f"  {decision['id']}  {decision['disposition']:<11} {decision['by']:<6} "
              f"{decision['reason'][:42]}")
    rule()
    print(f"{artifact['messages_processed']} messages, "
          f"{artifact['rule_handled']} without a model "
          f"({artifact.get('guard_handled', 0)} of them by the guard), "
          f"{artifact['model_handled']} by model")
    print(f"undecided: {artifact['messages_processed'] - len(artifact['decisions'])}")
    refusals = artifact.get("refusals") or ()
    if refusals:
        print(Guard.CARRIED.format(count=len(refusals),
                                   names=", ".join(r["id"] for r in refusals)))


def answered(artifact: dict, args) -> None:
    only = args.msg
    heading("R2  replies grounded in earlier mail, or refused")
    made = [d for d in artifact["drafts"] if only is None or d["id"] == only]

    for draft in made:
        if draft["refused"]:
            named = f" [{', '.join(draft['cited'])}]" if draft["cited"] else ""
            print(f"  {draft['id']}  refused{named}: {draft['refused']}")
            continue
        print(f"  {draft['id']}  cited: {', '.join(draft['cited'])}")
        print(wrap(draft["body"], 8))
        print()
    rule()
    drafted = [d for d in made if not d["refused"]]
    print(f"{len(drafted)} drafted, {len(made) - len(drafted)} refused, "
          f"{sum(len(d['cited']) for d in drafted)} citations, all checked against the store")


def asking(args) -> bool:
    if args.dry_run:
        return False
    return bool(args.approve) or sys.stdin.isatty()


def show(verdict, asked: bool = False) -> None:
    proposal = verdict.proposal
    gate = importlib.import_module("gate")
    if not asked or verdict.answer == Answer.REFUSED:
        print(f"  {proposal.id}  {proposal.detail}")
    print(f"        {proposal.action} / {gate.risk(proposal.action)} / "
          f"{verdict.answer}: {verdict.outcome}")


def gated(artifact: dict, args) -> None:
    actions = importlib.import_module("actions")
    drafts = importlib.import_module("drafts")
    gate = importlib.import_module("gate")
    store = importlib.import_module("store")
    ask = gate.prompt if asking(args) else None

    heading("R3  nothing irreversible happens unless a person says so")
    if args.delete:
        why = gate.decision(args.delete).get("reason") or "no reason was given"
        show(actions.remove(args.delete, why, ask=ask), asked=bool(ask))
        rule()
        print(f"mailbox holds {len(actions.carried())}, trash holds {len(actions.held())}")
        return
    if args.restore:
        show(actions.restore(args.restore, ask=ask), asked=bool(ask))
        rule()
        print(f"mailbox holds {len(actions.carried())}, trash holds {len(actions.held())}")
        return

    box = store.load()
    written, logged = len(actions.sent()), len(gate.records())
    wanted = [record for record in artifact["drafts"] if args.msg in (None, record["id"])]
    sendable = [record for record in wanted if not record["refused"]]

    for record in wanted:
        if record["refused"]:
            print(f"  {record['id']}  not proposed: {record['refused']}")

    verdicts = []
    for record in sendable:
        verdict = actions.send(drafts.read(record), box.message(record["id"]), ask=ask)
        show(verdict, asked=bool(ask))
        verdicts.append(verdict)
    rule()
    approved = [verdict for verdict in verdicts if verdict.went_ahead]
    print(f"{len(verdicts)} proposed, {len(approved)} approved, "
          f"outbox/ writes: {len(actions.sent()) - written}")
    print(f"refused at drafting and never put to a person: {len(wanted) - len(sendable)}")
    print(f"approval records this run: {len(gate.records()) - logged}, appended to "
          f"approvals.jsonl, which is never rewritten")


def tried(store, memory, name: str) -> None:
    message = store.message(name)
    print(f"  {name} from {message.sender}")
    print(f"        {message.subject}")
    print()
    for kind in Kind:
        found = memory.remember(kind, message, store)
        if found.refused:
            print(f"        as a {kind} preference  REFUSED: {found.refused}")
        else:
            print(f"        as a {kind} preference  {memory.instruction(found)}")


def remembered(artifact: dict, args) -> None:
    memory = importlib.import_module("memory")
    store = importlib.import_module("store")

    heading("R4  standing instructions outlive the process that recorded them")
    if args.msg:
        tried(store.load(), memory, args.msg)
        rule()
        print("the shape decides, not the sender and not how politely it asks")
        return

    standing = memory.held()
    if not standing:
        print("  nothing is recorded in this checkout.")
        print()
        print(f"  the committed run of {artifact['at']} recorded these:")
        for one in artifact["recorded"]:
            print(f"        {one['source']}  {one['kind']}  {one['subject']} -> {one['value']}")
        rule()
        print("run `python demo.py --cap R1 --fresh` to record them here, then this again")
        return

    for one in standing:
        print(f"  {one.source}  first written {one.at or 'before this was recorded'}")
        print(f"        {memory.instruction(one)}")
        print(f"        it came from: {one.said}")
        print()

    if not artifact["standing"]:
        print(f"  the run of {artifact['at']} is the process that wrote them, so it acted on")
        print("  none of them. Run `python demo.py --cap R1 --fresh` again, and a later")
        print("  process will read them off disk before it decides anything.")
        rule()
        print(f"{len(standing)} recorded, 0 in force, nothing handled differently yet")
        return

    known = memory.sources(standing)
    copied = [d for d in artifact["decisions"] if d["copy"]]
    leaning = [d for d in artifact["drafts"] if set(d["cited"]) & known]
    print(f"  in force during the run of {artifact['at']}, a later process than the one "
          f"that wrote them")
    print()
    for decision in copied:
        print(f"        {decision['id']}  {decision['disposition']:<9} "
              f"copy {', '.join(decision['copy'])}")
    for made in leaning:
        print(f"        {made['id']}  reply     cites {', '.join(made['cited'])}")
    rule()
    changed = len(copied) + len(leaning)
    print(f"{len(standing)} recorded, {len(artifact['refused_preferences'])} refused in this "
          f"run, {changed} message{'' if changed == 1 else 's'} handled differently "
          f"because of them")


def unreached(artifact: dict) -> list[str]:
    actions = importlib.import_module("actions")
    targets = {where for refusal in artifact.get("refusals") or ()
               for where in refusal["where"]}
    reached = []
    for name in actions.sent():
        written = actions.where(name).read_text().lower()
        for where in sorted(targets):
            if where in written:
                reached.append(Guard.REACHED.format(name=name, where=where))
    return reached


def blind(artifact: dict) -> None:
    guard = importlib.import_module("guard")
    router = importlib.import_module("router")
    store = importlib.import_module("store")

    decisions = router.sorted_out(store.load(), ask=lambda system, text, shape: None)
    caught = [d for d in decisions if d.by == Decided.GUARD]
    print(f"  {Guard.BLIND}.")
    print()
    for decision in caught:
        print(f"        {decision.id}  {decision.disposition}")
        print(wrap(decision.reason, 14))
    rule()
    silent = [d for d in decisions if d.by == Decided.MODEL]
    print(f"{len(caught)} still quarantined with no model in the loop, "
          f"{len(decisions)} messages still decided")
    print(f"the {len(silent)} the model would have judged are escalated to Sam instead")


def unguarded(artifact: dict) -> None:
    config = importlib.import_module("config")
    guard = importlib.import_module("guard")
    router = importlib.import_module("router")
    store = importlib.import_module("store")

    box = store.load()
    hostile = [found.id for found in guard.sweep(box)]
    decisions = {made.id: made for made in router.sorted_out(box, guarded=False)}
    reached = sum(1 for made in decisions.values() if made.by is Decided.MODEL)

    print(wrap(Guard.PROMPTED, 2))
    print(f"        {Guard.ASKED_OF.format(provider=config.PROVIDER, model=config.MODEL, batch=reached)}")
    print()
    caught = 0
    for name in hostile:
        made = decisions[name]
        if made.disposition is Disposition.QUARANTINE:
            caught += 1
        print(f"        {name}  {made.disposition}, by {made.by}")
        print(wrap(Guard.UNSEEN if made.by is not Decided.MODEL else made.reason, 14))
    rule()
    print(wrap(Guard.SCORE.format(caught=caught, total=len(hostile)), 0))


def refused(artifact: dict, args) -> None:
    heading("R5  mail that talks to the assistant is refused, flagged and left in place")
    if args.blind:
        blind(artifact)
        return
    if args.prompted:
        unguarded(artifact)
        return
    if "refusals" not in artifact:
        print(wrap(Guard.STALE, 2))
        return

    guard = importlib.import_module("guard")
    store = importlib.import_module("store")
    box = store.load()
    disposed = {d["id"]: d for d in artifact["decisions"]}

    for refusal in artifact["refusals"]:
        if args.msg not in (None, refusal["id"]):
            continue
        made = disposed[refusal["id"]]
        print(wrap(refusal["flagged"], 2))
        print(wrap(f"it speaks to an assistant: {refusal['said']}", 8))
        asked = guard.asking(guard.spoken(box.message(refusal["id"])))
        if asked and asked != refusal["said"]:
            print(wrap(f"and asks it to act: {asked}", 8))
        print(f"        {made['disposition']}, decided by {made['by']}, still in the mailbox")
        print()
    rule()
    reached = unreached(artifact)
    print(f"{len(artifact['refusals'])} flagged, 0 deleted, 0 acted on, "
          f"{len(artifact['decisions'])} messages still in the run")
    for line in reached:
        print(f"  BREACH  {line}")
    if not reached:
        print(Guard.CLEAN)


def shown(artifact: dict, args) -> None:
    dashboard = importlib.import_module("dashboard")
    store = importlib.import_module("store")
    made = dashboard.write(dashboard.view(artifact, store.load()))

    heading(f"R6  three panes from the run of {made['at']}")
    print(f"  {Dashboard.PANES[0]} — what it wants to do and may not do alone")
    for row in made["pending"]:
        print(f"        {row['id']}  {row['action']}")
        print(f"              {row['why']}")
    print()
    print(f"  {Dashboard.PANES[1]} — what it would not act on")
    for row in made["flagged"]:
        print(f"        {row['id']}  {row['attempted'][:62]}")
        print(f"              -> {row['instead']}")
    print()
    print(f"  {Dashboard.PANES[2]} — the calendar")
    for clash in made["conflicts"]:
        print(f"        {clash['called']}")
    if made["conflicts"]:
        print()
    for when, group in sorted(dashboard.days(made["commitments"]).items()):
        for row in group:
            print(f"        {when} {row['at'] or '     ':<6} {row['standing']:<14}"
                  f"{row['what'][:34]:<36}{', '.join(row['cited'])}")
    if made["unplaced"]:
        print()
        print(f"        {dashboard.unplaced_line(made)}")
        for row in made["unplaced"]:
            print(f"        {', '.join(row['cited'])}  {row['what'][:26]:<28}"
                  f"{row['unresolved']}")
    rule()
    print(f"{len(made['pending'])} pending, {len(made['flagged'])} flagged, "
          f"{len(made['commitments'])} commitments, {len(made['conflicts'])} conflicts")
    print(f"written to {Paths.DASHBOARD.name} and {Paths.PAGE.name}")


def titled(told) -> str:
    return f"  {told.label:<{WIDTH - 2 - len(told.source)}}{told.source}"


def accounted(artifact: dict, args) -> None:
    why = importlib.import_module("why")
    store = importlib.import_module("store")
    box = store.load()

    if not args.msg:
        heading(Why.HEADLESS)
        print(f"  {Why.ASK}")
        wanted = why.suggestions(artifact)
        print(f"  {Why.TRY.format(id=wanted[0])}")
        print(f"  {Why.OTHERS.format(ids=', '.join(wanted[1:]))}")
        return

    if not why.known(args.msg, artifact, box):
        heading(Why.HEADLESS)
        print(f"  {Why.MISSING.format(id=args.msg)}")
        return

    heading(Why.HEAD.format(id=args.msg))
    told = why.account(args.msg, artifact, box)
    for one in told:
        print(titled(one))
        for line in one.lines:
            print(wrap(line, 8))
        print()
    rule()
    print(Why.CLOSE.format(sections=len(told), files=len(why.files(told))))


def summarised(artifact: dict, args) -> None:
    heading("X1  the long conversations, each down to what is still open")
    if "digests" not in artifact:
        print(wrap(Digest.STALE, 2))
        return

    made = [one for one in artifact["digests"]
            if args.msg is None or args.msg == one["thread"] or args.msg in one["ids"]]
    for one in made:
        print(f"  {one['thread']}  "
              f"{Digest.SPAN.format(count=len(one['ids']), first=one['ids'][0], last=one['ids'][-1])}")
        if one["dropped"]:
            print(wrap(one["dropped"], 8))
            print()
            continue
        print(wrap(one["summary"], 8))
        print()
        if one["needs"]:
            print(f"        {Digest.NEEDS.format(id=one['needs'])}")
            print(wrap(f'"{one["asked"]}"', 8))
        else:
            print(f"        {Digest.NOTHING}")
        if one["settled"]:
            print(wrap(Digest.CLOSED.format(ids=", ".join(one["settled"])), 8))
        print()
    rule()
    waiting = [one for one in made if one["needs"]]
    covered = sum(len(one["ids"]) for one in made)
    print(f"{len(made)} conversations of {Digest.SHORTEST} messages or more, "
          f"{covered} messages read, {len(waiting)} still waiting on Sam")


def chased(artifact: dict, args) -> None:
    heading("X2  mail Sam sent that nobody has answered")
    if "followups" not in artifact:
        print(wrap(Followups.STALE, 2))
        return

    made = [one for one in artifact["followups"] if args.msg in (None, one["id"])]
    waiting = [one for one in made if one["chased"]]
    for one in waiting:
        print(f"  {one['id']}  to {one['to']}, sent {one['sent'][:10]}, "
              f"{Followups.WAITED.format(days=one['waiting'])}")
        print(f"        {one['subject']}")
        print(wrap(one["refused"] or one["body"], 8))
        print()

    left = [one for one in made if not one["chased"]]
    if left:
        print("  left alone")
        for one in left:
            print(f"        {one['id']}  {one['why']}")
        print()
    rule()
    if not waiting:
        print(Followups.NONE)
    print(f"{len(made)} messages Sam sent, {len(waiting)} still waiting, "
          f"{len(left)} left alone")
    print(wrap(Followups.GATED, 0))


def offered(artifact: dict, args) -> None:
    actions = importlib.import_module("actions")
    drafts = importlib.import_module("drafts")
    gate = importlib.import_module("gate")
    offers = importlib.import_module("offers")
    store = importlib.import_module("store")
    ask = gate.prompt if asking(args) else None

    heading("X3  a time that will not do, answered with three that will")
    if "offers" not in artifact:
        print(wrap(Offers.STALE, 2))
        return

    box = store.load()
    written = len(actions.sent())
    made = [one for one in artifact["offers"] if args.msg in (None, one["id"])]
    verdicts = []

    for one in made:
        asked = offers.spoken(f"{one['when']} {one['at']}")
        print(f"  {one['id']}  to {one['to']}")
        print(wrap(Offers.WHY.format(slot=asked, because=one["because"]), 8))
        if one["blocked"]:
            print(wrap(Offers.BLOCKED.format(ids=", ".join(one["blocked"])), 8))
        for slot in one["slots"]:
            print(f"        {Offers.INSTEAD.format(slot=offers.spoken(slot))}")
        print()
        if one["refused"]:
            print(wrap(one["refused"], 8))
            print()
            continue
        print(wrap(one["body"], 8))
        print()
        verdict = actions.send(drafts.read(one), box.message(one["id"]), ask=ask)
        show(verdict, asked=bool(ask))
        verdicts.append(verdict)
        print()

    rule()
    if not made:
        print(Offers.NONE)
    approved = [verdict for verdict in verdicts if verdict.went_ahead]
    print(f"{len(made)} proposed times answered, "
          f"{sum(len(one['slots']) for one in made)} alternatives worked out here and none "
          f"by the model")
    print(f"{len(verdicts)} put to a person, {len(approved)} approved, "
          f"outbox/ writes: {len(actions.sent()) - written}")
    print(wrap(Offers.QUIET, 0))


VIEWS = {Capability.R1: zeroed, Capability.R2: answered, Capability.R3: gated,
         Capability.R4: remembered, Capability.R5: refused, Capability.R6: shown,
         Capability.X1: summarised, Capability.X2: chased, Capability.X3: offered,
         Capability.X4: accounted}


def capability(name: str, args) -> None:
    if name not in tuple(Capability):
        print(f"There is no capability called {name}")
        raise SystemExit(f"Capabilities: {', '.join(Capability)}")

    artifact = ensure_run(args.fresh)
    view = VIEWS.get(Capability(name))
    if view is None:
        print(f"{name} is not built yet.")
        return
    view(artifact, args)


def main() -> None:
    parser = argparse.ArgumentParser(prog="inboxhero")
    parser.add_argument("--cap", metavar="ID", help="demonstrate one capability by id")
    parser.add_argument(
        "--all",
        action="store_true",
        help="demonstrate every capability, in the order the manifest lists them",
    )
    parser.add_argument(
        "--msg",
        metavar="ID",
        help="narrow a capability to one message, where it works on more than one",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="rebuild the run from the inbox instead of reading the artifact on disk",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show every irreversible action and write nothing, without asking anybody",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="ask about each irreversible action even when nothing is reading the keyboard; "
             "at a terminal this happens anyway",
    )
    parser.add_argument(
        "--delete",
        metavar="ID",
        help="take one message out of the mailbox, keeping the whole of it in trash/",
    )
    parser.add_argument(
        "--restore",
        metavar="ID",
        help="put a message from trash/ back where it came from",
    )
    parser.add_argument(
        "--blind",
        action="store_true",
        help="run the triage without asking the model anything, to show what still holds",
    )
    parser.add_argument(
        "--forget",
        action="store_true",
        help="throw away every recorded preference, so the next run starts with none",
    )
    parser.add_argument(
        "--prompted",
        action="store_true",
        help="run the triage with the guard switched off, to measure what the prompt alone "
             "catches; set PROVIDER and MODEL to choose which model is asked",
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="write capabilities.json from the run artifact and the code",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="empty outbox/ and trash/ and truncate approvals.jsonl, so the evidence "
             "committed for a run is only ever from that run",
    )
    parser.add_argument(
        "--test",
        nargs="?",
        const="all",
        metavar="SUITE",
        help="run one suite by name, or every suite when no name is given",
    )

    args = parser.parse_args()

    if args.test:
        raise SystemExit(0 if sibling("tests", "runner").run(args.test) else 1)

    if args.manifest:
        listed()
        return

    if args.clean:
        cleaned()
        if not args.cap:
            return

    if args.forget:
        importlib.import_module("memory").forget()
        print("every recorded preference has been thrown away")
        if not args.cap:
            return

    if args.cap:
        capability(args.cap, args)
        return

    if args.all:
        for name in Capability:
            capability(name, args)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
