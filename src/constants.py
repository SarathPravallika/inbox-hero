# cert-aai-2026-06-0061  Sarath Chandra

from enum import StrEnum
from pathlib import Path


class Paths:
    ROOT = Path(__file__).resolve().parent.parent

    INBOX = ROOT / "assignment-instructions" / "inbox.json"


class Disposition(StrEnum):
    REPLY = "reply"
    ARCHIVE = "archive"
    DEFER = "defer"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    QUARANTINE = "quarantine"


class Decided(StrEnum):
    RULE = "rule"
    MODEL = "model"


class Tier(StrEnum):
    A = "A"
    B = "B"
    C = "C"


class Capability(StrEnum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"
    X1 = "X1"
    X2 = "X2"
    X3 = "X3"
    X4 = "X4"


class Rules:
    AUTOMATED = frozenset({
        "no-reply", "noreply", "no_reply", "notifications", "notify", "receipts", "alerts",
        "newsletter", "digest", "updates", "insights", "feedback", "mailer-daemon",
        "ship-confirm", "orders", "invoice+statements", "billing", "info", "hello",
        "support", "success", "help", "checkin", "security", "status",
    })

    RECEIPT = ("receipt", "invoice", "bill", "statement", "payout", "order", "renew")
    DIGEST = ("digest", "newsletter", "weekly", "daily", "report", "recommendation",
              "subscription", "top")

    BOILERPLATE_LIMIT = 150


class Model:
    TEMPERATURE = 0.0
    BATCH_SIZE = 10
    GAP_SECONDS = 4
    RETRIES = 3
    BACKOFF_SECONDS = 20
    TIMEOUT_SECONDS = 180


WIDTH = 78
