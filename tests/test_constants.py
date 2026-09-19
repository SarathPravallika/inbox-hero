# cert-aai-2026-06-0061  Sarath Chandra
#
# - Proves the disposition vocabulary and capability ids are exactly what the manifest claims
# - Proves every capability carries a tier and that all three tiers are used, because the
#   assignment requires the spread and a claim kept beside the code drifts from it

from constants import Capability, Disposition, Manifest, Tier
from utils import heading, rule

ORDER = ("R1", "R2", "R3", "R4", "R5", "R6", "X1", "X2", "X3", "X4")

def check_vocabulary() -> list[str]:
    problems = []
    if len(Disposition) != 6:
        problems.append(f"there are {len(Disposition)} dispositions, not 6")
    for value in Disposition:
        if value != value.lower():
            problems.append(f"disposition {value!r} is not lower case")
    if Disposition.ESCALATE == Disposition.QUARANTINE:
        problems.append("escalate and quarantine are the same value")
    if len(Tier) != 3:
        problems.append(f"there are {len(Tier)} tiers, not 3")
    if tuple(Capability) != ORDER:
        problems.append(f"the capability ids are {', '.join(Capability)}, not {', '.join(ORDER)}")
    for vocabulary, stranger in ((Disposition, "nonsense"), (Tier, "D"), (Capability, "R9")):
        try:
            vocabulary(stranger)
            problems.append(f"{vocabulary.__name__} accepted {stranger!r}")
        except ValueError:
            pass
    return problems


def check_tiers() -> list[str]:
    problems = []
    for name in Capability:
        if name not in Manifest.TIER:
            problems.append(f"{name} is a capability the manifest lists with no tier")
    for name, tier in Manifest.TIER.items():
        if name not in tuple(Capability):
            problems.append(f"{name} carries a tier and is not a capability")
        if tier not in tuple(Tier):
            problems.append(f"{name} is tier {tier!r}, which is not a tier")
    for tier in Tier:
        if tier not in Manifest.TIER.values():
            problems.append(f"no capability is tier {tier}, and the assignment expects one")
    return problems


def run() -> bool:
    heading("inboxHero setup check")
    problems = check_vocabulary()
    print(f"  {'FAIL' if problems else 'pass'}  vocabulary")
    found = check_tiers()
    print(f"  {'FAIL' if found else 'pass'}  tiers")
    problems.extend(found)
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
