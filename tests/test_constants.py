# cert-aai-2026-06-0061  Sarath Chandra

from constants import Capability, Disposition, Tier
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


def run() -> bool:
    heading("inboxHero setup check")
    problems = check_vocabulary()
    print(f"  {'FAIL' if problems else 'pass'}  vocabulary")
    if problems:
        print()
        for problem in problems:
            print(f"  PROBLEM  {problem}")
    rule()
    print(f"{len(problems)} problems")
    return not problems
