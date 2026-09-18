# cert-aai-2026-06-0061  Sarath Chandra

import json
import classify
import rules
import tracing
from constants import Capability, Decided, Paths
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


def counted(decisions, by: Decided) -> int:
    return sum(1 for decision in decisions if decision.by is by)


def build(store, decisions, provider: str, model: str) -> dict:
    return {
        "at": tracing.stamp(),
        "provider": provider,
        "model": model,
        "messages_processed": len(store),
        "rule_handled": counted(decisions, Decided.RULE),
        "model_handled": counted(decisions, Decided.MODEL),
        "decisions": [{"id": d.id, "disposition": str(d.disposition),
                       "reason": d.reason, "by": str(d.by)} for d in decisions],
    }


def written(artifact: dict) -> dict:
    tracing.start()
    tracing.record(Capability.R1, "run", messages=artifact["messages_processed"],
                   rule_handled=artifact["rule_handled"], model=artifact["model"])
    for decision in artifact["decisions"]:
        tracing.record(Capability.R1, "decision", **decision)
    Paths.RUN.write_text(json.dumps(artifact, indent=2) + "\n")
    return artifact


def run(ask=None) -> dict:
    import config

    store = load()
    return written(build(store, sorted_out(store, ask=ask), config.PROVIDER, config.MODEL))


def stored() -> dict:
    return json.loads(Paths.RUN.read_text())
