# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves capabilities.json carries exactly the field names the marking script reads
# - Proves every number in it was read out of the run artifact rather than typed beside it
# - Proves every message id named in an observable is really in the mailbox
# - Proves CAPABILITIES.md and capabilities.json say the same thing about every
#   capability, because two files listing the same ten will drift otherwise
# - Runs every command in the manifest, in the order listed, against a copy of only the
#   files git tracks, because the assignment says a command that does not run is a
#   capability that was not delivered

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import manifest
from constants import Capability, Disposition, Gate, Manifest, Paths, Risk, Tier
from router import stored
from store import load
from utils import heading, rule

LOOKS_LIKE_AN_ID = r"\bm\d{3}\b"
SKIP = ("venv/", "assignment-instructions/FN_")


def fresh(room: Path) -> Path:
    listed = subprocess.run(["git", "ls-files"], cwd=Paths.ROOT, capture_output=True,
                            text=True, check=True).stdout.split()
    for name in listed:
        if name.startswith(SKIP) or not (Paths.ROOT / name).exists():
            continue
        target = room / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((Paths.ROOT / name).read_bytes())
    return room


def check_shape() -> list[str]:
    problems = []
    made, given = manifest.build(stored()), manifest.sample()
    if set(made) != set(given):
        problems.append(f"the manifest has the keys {sorted(made)}, not {sorted(given)}")
    if set(made["system"]) != set(given["system"]):
        problems.append(f"system has {sorted(made['system'])}, "
                        f"not {sorted(given['system'])}")
    wanted = set(given["capabilities"][0])
    if wanted != set(Manifest.FIELDS):
        problems.append(f"the sample's capability fields are {sorted(wanted)}")
    for row in made["capabilities"]:
        if set(row) != wanted:
            problems.append(f"{row.get('id')} has the fields {sorted(row)}")
            break
        for field in Manifest.FIELDS:
            if not str(row[field]).strip():
                problems.append(f"{row['id']} says nothing under {field}")
    return problems


def check_rows() -> list[str]:
    problems = []
    made = manifest.build(stored())
    ids = [row["id"] for row in made["capabilities"]]
    if ids != [str(name) for name in Capability]:
        problems.append(f"the manifest lists {ids}")
    held = {row["id"]: row["tier"] for row in made["capabilities"]}
    for tier in Tier:
        if str(tier) not in held.values():
            problems.append(f"no capability is tier {tier}, and the assignment expects one")
    for name, tier in held.items():
        if tier not in tuple(Tier):
            problems.append(f"{name} is tier {tier!r}")
    return problems


def check_numbers() -> list[str]:
    problems = []
    artifact = stored()
    made = manifest.build(artifact)["system"]
    for field in ("messages_processed", "rule_handled"):
        if made[field] != artifact[field]:
            problems.append(f"the manifest says {field} is {made[field]}, "
                            f"and the run says {artifact[field]}")
    if made["dispositions"] != [str(one) for one in Disposition]:
        problems.append(f"the manifest lists the dispositions as {made['dispositions']}")
    for wanted, listed in ((Risk.IRREVERSIBLE, made["irreversible"]),
                           (Risk.REVERSIBLE, made["reversible"])):
        for action, risk in Gate.RISK.items():
            if risk is wanted and str(action) not in listed:
                problems.append(f"{action} is {wanted} in the code and not in the manifest")
            if risk is not wanted and str(action) in listed:
                problems.append(f"{action} is listed {wanted} and the code says {risk}")
    if set(made["irreversible"]) & set(made["reversible"]):
        problems.append("an action is claimed both reversible and irreversible")
    return problems


def check_truthful(store) -> list[str]:
    problems = []
    made = manifest.build(stored())
    for row in made["capabilities"]:
        said = f"{row['claim']} {row['observable']} {row['evidence']}"
        for found in sorted(set(re.findall(LOOKS_LIKE_AN_ID, said))):
            if found not in store.ids:
                problems.append(f"{row['id']} names {found}, which is not in the mailbox")
    for name in ("m017", "m024", "m039", "m047"):
        if name not in made["capabilities"][4]["observable"]:
            problems.append(f"R5 claims to flag the injections and does not name {name}")
    return problems


def check_written() -> list[str]:
    problems = []
    if not Paths.MANIFEST.exists():
        problems.append(f"{Paths.MANIFEST.name} has not been written")
        return problems
    if manifest.stored() != manifest.build(stored()):
        problems.append(f"{Paths.MANIFEST.name} is older than the run it claims to describe, "
                        f"so run `python demo.py --manifest` again")
    return problems


def tabled(said: str, name: str) -> list[str]:
    for line in said.splitlines():
        if line.startswith(f"| {name} |"):
            return [cell.strip() for cell in line.strip().strip("|").split("|")]
    return []


def check_readable() -> list[str]:
    problems = []
    if not Paths.CAPABILITIES.exists():
        problems.append(f"{Paths.CAPABILITIES.name} has not been written")
        return problems

    said = Paths.CAPABILITIES.read_text()
    made = manifest.build(stored())
    for field in ("student", "repo"):
        if made[field] not in said:
            problems.append(f"{Paths.CAPABILITIES.name} does not carry the {field}")
    for row in made["capabilities"]:
        listed = tabled(said, row["id"])
        if not listed:
            problems.append(f"{row['id']} is in the manifest and not in the table")
            continue
        for field, cell in (("name", 1), ("tier", 2)):
            if listed[cell] != row[field]:
                problems.append(f"{row['id']} is {field} {row[field]!r} in the manifest "
                                f"and {listed[cell]!r} in the table")
        if not listed[3]:
            problems.append(f"{row['id']} is in the table with no claim beside it")
    if Paths.MANIFEST.name not in said:
        problems.append(f"{Paths.CAPABILITIES.name} never points a reader at "
                        f"{Paths.MANIFEST.name}")
    for name in (str(one) for one in Disposition):
        if name not in said:
            problems.append(f"the disposition {name} is never defined for a reader")
    return problems


def check_runs() -> list[str]:
    problems = []
    with tempfile.TemporaryDirectory() as room:
        where = fresh(Path(room))
        for name, command in manifest.commands():
            parts = command.split()
            if parts[0] == "python":
                parts[0] = sys.executable
            try:
                done = subprocess.run(parts, cwd=where, capture_output=True, text=True,
                                      timeout=Manifest.TIMEOUT)
            except subprocess.TimeoutExpired:
                problems.append(f"{name}: `{command}` did not finish")
                continue
            if done.returncode != 0:
                last = (done.stderr or done.stdout).strip().splitlines()
                problems.append(f"{name}: `{command}` exited {done.returncode}: "
                                f"{last[-1] if last else 'it said nothing'}")
                continue
            if name not in done.stdout:
                problems.append(f"{name}: `{command}` ran and never says which capability "
                                f"it is demonstrating")
    return problems


def run() -> bool:
    heading("inboxHero manifest check")
    store = load()
    problems = []
    for name, found in (("field names", check_shape()),
                        ("every capability", check_rows()),
                        ("numbers from the run", check_numbers()),
                        ("ids that exist", check_truthful(store)),
                        ("written out", check_written()),
                        ("readable and in step", check_readable()),
                        ("every command runs", check_runs())):
        print(f"  {'FAIL' if found else 'pass'}  {name}")
        problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
