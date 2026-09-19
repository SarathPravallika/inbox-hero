# cert-aai-2026-06-0061  Sarath Chandra
#
# - Shared formatting helpers for anything printed to the screen

from constants import WIDTH

def heading(title: str) -> None:
    print(title)
    print("=" * WIDTH)

def wrap(text: str, indent: int) -> str:
    room = WIDTH - indent
    pad = " " * indent
    lines = []
    line = ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > room:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return pad + f"\n{pad}".join(lines)


def rule() -> None:
    print("-" * WIDTH)
