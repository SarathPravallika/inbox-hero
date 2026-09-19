# cert-aai-2026-06-0061  Sarath Chandra
#
# - Writes capabilities.json, which is the file the marking script reads
# - Every number in it is read out of the run artifact and every classification out of the
#   code, so the manifest cannot claim something the commands do not print
# - The reversibility lists are built from Gate.RISK rather than typed beside it, the same
#   way the tier of each capability is built from Manifest.ROWS

import json
from constants import Capability, Disposition, Gate, Manifest, Paths, Risk


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


def capabilities() -> list[dict]:
    return [{"id": str(name), "name": row["name"], "tier": str(row["tier"]),
             "claim": row["claim"], "command": row["command"],
             "observable": row["observable"], "evidence": row["evidence"]}
            for name, row in Manifest.ROWS.items()]


def build(artifact: dict) -> dict:
    return {"student": Manifest.STUDENT,
            "repo": Manifest.REPO,
            "system": system(artifact),
            "capabilities": capabilities()}


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
