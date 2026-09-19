# cert-aai-2026-06-0061  Sarath Chandra
#
# - Runs the whole inbox once and records the outcome
# - The guard reads every message first, so hostile mail never reaches the rules or the model
# - The run it writes is what every capability reads, so a demonstration never repeats the cost
# - Keeps the meaning-based index current even though the run does not use it, so the
#   comparison that ruled it out stays reproducible from a clean checkout
# - Applies the standing instructions an earlier process left behind, then records the ones
#   this run found, so a preference only ever takes effect on a later run

import json
from dataclasses import asdict

import classify
import commitments
import drafts
import guard
import memory
import retrieve
import rules
import tracing
from constants import Capability, Decided, Disposition, Paths, Trace
from store import load


def sorted_out(store, ask=None) -> list:
    decided, waiting = {}, []

    for message in store.messages:
        decision = guard.decide(message) or rules.decide(message)
        if decision is None:
            waiting.append(message)
        else:
            decided[message.id] = decision

    for decision in classify.classify(waiting, ask=ask):
        decided[decision.id] = decision
    return [decided[message.id] for message in store.messages]


def claimed(store, decisions) -> tuple:
    return tuple(memory.remember(decision.preference, store.message(decision.id), store)
                 for decision in decisions if decision.preference)


def replies(store, decisions, standing, ask=None) -> list:
    return [drafts.draft(store, store.message(decision.id), ask=ask, standing=standing)
            for decision in decisions if decision.disposition is Disposition.REPLY]


def counted(decisions, by: Decided) -> int:
    return sum(1 for decision in decisions if decision.by is by)


def build(store, decisions, written_drafts, standing, recorded, diary, provider: str,
          model: str) -> dict:
    return {
        "at": tracing.stamp(),
        "provider": provider,
        "model": model,
        "messages_processed": len(store),
        "rule_handled": len(decisions) - counted(decisions, Decided.MODEL),
        "guard_handled": counted(decisions, Decided.GUARD),
        "model_handled": counted(decisions, Decided.MODEL),
        "refusals": [{"id": t.id, "attempted": list(t.attempts), "where": list(t.where),
                      "said": t.said, "flagged": guard.flagged(t)}
                     for t in guard.sweep(store)],
        "standing": [asdict(one) for one in standing],
        "recorded": [asdict(one) for one in recorded if not one.refused],
        "refused_preferences": [asdict(one) for one in recorded if one.refused],
        "decisions": [{"id": d.id, "disposition": str(d.disposition),
                       "reason": d.reason, "by": str(d.by),
                       "copy": list(memory.copies(store.message(d.id), standing))}
                      for d in decisions],
        "drafts": [{"id": d.id, "body": d.body, "cited": list(d.cited),
                    "refused": d.refused, "dropped": list(d.dropped)}
                   for d in written_drafts],
        "commitments": [{"id": c.id, "what": c.what, "said": c.said, "when": c.when,
                         "at": c.at, "settled": c.settled, "cited": list(c.cited),
                         "unresolved": c.unresolved} for c in diary],
        "conflicts": [{"ids": [one.id, other.id], "when": one.when, "at": one.at,
                       "called": commitments.clash((one, other))}
                      for one, other in commitments.clashes(diary)],
    }


def renamed(one: dict, name: str) -> dict:
    carried = dict(one)
    carried[name] = carried.pop("at")
    return carried


def written(artifact: dict) -> dict:
    tracing.start()
    tracing.record(Capability.R1, "run", messages=artifact["messages_processed"],
                   rule_handled=artifact["rule_handled"], model=artifact["model"])
    for decision in artifact["decisions"]:
        tracing.record(Capability.R1, "decision", **decision)
    for made in artifact["drafts"]:
        tracing.record(Capability.R2, "refusal" if made["refused"] else "draft", **made)
    for one in artifact["refusals"]:
        tracing.record(Capability.R5, "refusal", **one)
    for one in artifact["commitments"]:
        tracing.record(Capability.R6, "commitment", **renamed(one, Trace.CLOCK))
    for one in artifact["conflicts"]:
        tracing.record(Capability.R6, "conflict", **renamed(one, Trace.CLOCK))
    for one in artifact["standing"]:
        tracing.record(Capability.R4, "in force", **renamed(one, Trace.FIRST))
    for one in artifact["recorded"]:
        tracing.record(Capability.R4, "remembered", **renamed(one, Trace.FIRST))
    for one in artifact["refused_preferences"]:
        tracing.record(Capability.R4, "refusal", **renamed(one, Trace.FIRST))
    Paths.RUN.write_text(json.dumps(artifact, indent=2) + "\n")
    return artifact


def run(ask=None) -> dict:
    import config

    store = load()
    if not Paths.VECTORS.exists():
        retrieve.written(store)
    standing = memory.held()
    decisions = sorted_out(store, ask=ask)
    written_drafts = replies(store, decisions, standing, ask=ask)
    recorded = claimed(store, decisions)
    memory.keep(recorded)
    diary = commitments.gather(store, decisions, ask=ask)
    return written(build(store, decisions, written_drafts, standing, recorded, diary,
                         config.PROVIDER, config.MODEL))


def stored() -> dict:
    return json.loads(Paths.RUN.read_text())
