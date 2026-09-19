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

from constants import Answer, Capability, Kind, Paths
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
          f"{artifact['rule_handled']} by rule, {artifact['model_handled']} by model")
    print(f"undecided: {artifact['messages_processed'] - len(artifact['decisions'])}")


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


VIEWS = {Capability.R1: zeroed, Capability.R2: answered, Capability.R3: gated,
         Capability.R4: remembered}


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
        "--forget",
        action="store_true",
        help="throw away every recorded preference, so the next run starts with none",
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
