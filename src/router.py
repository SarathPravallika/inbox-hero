# cert-aai-2026-06-0061  Sarath Chandra
#
# - Runs the whole inbox once and records the outcome
# - The run it writes is what every capability reads, so a demonstration never repeats the cost
# - Keeps the meaning-based index current even though the run does not use it, so the
#   comparison that ruled it out stays reproducible from a clean checkout

import json
import classify
import drafts
import retrieve
import rules
import tracing
from constants import Capability, Decided, Disposition, Paths
from store import load


def sorted_out(store, ask=None) -> list:
    decided, waiting = {}, []

    for message in store.messages:
        decision = rules.decide(message)
        if decision is None:
            waiting.append(message)
        else:
            decided[message.id] = decision

    for decision in classify.classify(waiting, ask=ask):
        decided[decision.id] = decision
    return [decided[message.id] for message in store.messages]


def replies(store, decisions, ask=None) -> list:
    return [drafts.draft(store, store.message(decision.id), ask=ask)
            for decision in decisions if decision.disposition is Disposition.REPLY]


def counted(decisions, by: Decided) -> int:
    return sum(1 for decision in decisions if decision.by is by)


def build(store, decisions, written_drafts, provider: str, model: str) -> dict:
    return {
        "at": tracing.stamp(),
        "provider": provider,
        "model": model,
        "messages_processed": len(store),
        "rule_handled": counted(decisions, Decided.RULE),
        "model_handled": counted(decisions, Decided.MODEL),
        "decisions": [{"id": d.id, "disposition": str(d.disposition),
                       "reason": d.reason, "by": str(d.by)} for d in decisions],
        "drafts": [{"id": d.id, "body": d.body, "cited": list(d.cited),
                    "refused": d.refused, "dropped": list(d.dropped)}
                   for d in written_drafts],
    }


def written(artifact: dict) -> dict:
    tracing.start()
    tracing.record(Capability.R1, "run", messages=artifact["messages_processed"],
                   rule_handled=artifact["rule_handled"], model=artifact["model"])
    for decision in artifact["decisions"]:
        tracing.record(Capability.R1, "decision", **decision)
    for made in artifact["drafts"]:
        tracing.record(Capability.R2, "refusal" if made["refused"] else "draft", **made)
    Paths.RUN.write_text(json.dumps(artifact, indent=2) + "\n")
    return artifact


def run(ask=None) -> dict:
    import config

    store = load()
    if not Paths.VECTORS.exists():
        retrieve.written(store)
    decisions = sorted_out(store, ask=ask)
    return written(build(store, decisions, replies(store, decisions, ask=ask),
                         config.PROVIDER, config.MODEL))


def stored() -> dict:
    return json.loads(Paths.RUN.read_text())
