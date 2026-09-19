# cert-aai-2026-06-0061  Sarath Chandra
#
# - Shared formatting helpers for anything printed to the screen

from constants import WIDTH

def heading(title: str) -> None:
    print(title)
    print("=" * WIDTH)

def rule() -> None:
    print("-" * WIDTH)
