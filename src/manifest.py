# cert-aai-2026-06-0061  Sarath Chandra
#
# - Writes capabilities.json, the machine-readable half of the manifest
# - Every number in it is read out of the run artifact and every classification out of the
#   code, so the manifest cannot claim something the commands do not print
# - The reversibility lists are built from Gate.RISK rather than typed beside it, the same
#   way the tier of each capability is built from Manifest.ROWS
# - Counts inside an observable are filled in from the run too, so a manifest can never
#   claim a number the command it names does not print

import json
from constants import Disposition, Gate, Manifest, Paths, Risk


def risked(wanted: Risk) -> list[str]:
    return [str(action) for action, risk in Gate.RISK.items() if risk is wanted]


def system(artifact: dict) -> dict:
    return {
        "framework": Manifest.FRAMEWORK,
        "model": Manifest.MODEL,
        "messages_processed": artifact["messages_processed"],
        "rule_handled": artifact["rule_handled"],
        "dispositions": [str(one) for one in Disposition],
        "retrieval": Manifest.RETRIEVAL,
        "irreversible": risked(Risk.IRREVERSIBLE),
        "reversible": risked(Risk.REVERSIBLE) + list(Manifest.ALSO_REVERSIBLE),
        "gate": Manifest.GATE,
        "preference_demo": Manifest.PREFERENCE,
    }


def counted(artifact: dict) -> dict:
    disposed = [one["disposition"] for one in artifact["decisions"]]
    refused = [one for one in artifact["drafts"] if one["refused"]]
    return {
        "messages": artifact["messages_processed"],
        "unmodelled": artifact["rule_handled"],
        "guarded": artifact["guard_handled"],
        "modelled": artifact["model_handled"],
        "drafted": len(artifact["drafts"]) - len(refused),
        "refused": len(refused),
        "caught": len(artifact["refusals"]),
        "flagged": sum(1 for one in disposed
                       if one in (Disposition.QUARANTINE, Disposition.ESCALATE))
        + len(refused),
        "extracted": len(artifact["commitments"]),
        "placed": sum(1 for one in artifact["commitments"] if one["when"]),
        "unplaced": sum(1 for one in artifact["commitments"] if not one["when"]),
        "conflicts": len(artifact["conflicts"]),
        "hostile": ", ".join(one["id"] for one in artifact["refusals"]),
    }


def capabilities(artifact: dict) -> list[dict]:
    numbers = counted(artifact)
    return [{"id": str(name), "name": row["name"], "tier": str(row["tier"]),
             "claim": row["claim"], "command": row["command"],
             "observable": row["observable"].format(**numbers),
             "evidence": row["evidence"]}
            for name, row in Manifest.ROWS.items()]


def build(artifact: dict) -> dict:
    return {"student": Manifest.STUDENT,
            "repo": Manifest.REPO,
            "system": system(artifact),
            "capabilities": capabilities(artifact)}


def written(artifact: dict) -> dict:
    made = build(artifact)
    Paths.MANIFEST.write_text(json.dumps(made, indent=2) + "\n")
    return made


def stored() -> dict:
    return json.loads(Paths.MANIFEST.read_text())


def sample() -> dict:
    return json.loads(Paths.SAMPLE.read_text())


def commands() -> list[tuple[str, str]]:
    return [(str(name), row["command"]) for name, row in Manifest.ROWS.items()]
