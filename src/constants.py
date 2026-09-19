# cert-aai-2026-06-0061  Sarath Chandra
#
# - Every value that can change without touching logic, grouped by the part that reads it
# - The disposition vocabulary and capability ids the manifest declares

from enum import StrEnum
from pathlib import Path


class Paths:
    ROOT = Path(__file__).resolve().parent.parent

    INBOX = ROOT / "assignment-instructions" / "inbox.json"
    MAILBOX = ROOT / "mailbox.json"
    RUN = ROOT / "run.json"
    VECTORS = ROOT / "vectors.json"
    TRACE = ROOT / "trace.jsonl"
    MEMORY = ROOT / "memory.json"
    OUTBOX = ROOT / "outbox"
    TRASH = ROOT / "trash"
    APPROVALS = ROOT / "approvals.jsonl"


class Inbox:
    FIELDS = {"from": "sender"}
    OWNER = "sam@paperjet.io"
    DOMAIN = "paperjet.io"


class Disposition(StrEnum):
    REPLY = "reply"
    ARCHIVE = "archive"
    DEFER = "defer"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    QUARANTINE = "quarantine"


class Action(StrEnum):
    SEND = "send"
    DELETE = "delete"
    RESTORE = "restore"


class Kind(StrEnum):
    SCHEDULING = "scheduling"
    COPYING = "copying"


class Risk(StrEnum):
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"


class Answer(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    REFUSED = "refused"
    DRY = "dry-run"
    UNATTENDED = "unattended"


class Decided(StrEnum):
    RULE = "rule"
    GUARD = "guard"
    MODEL = "model"


class Attempt(StrEnum):
    FORWARD = "forward"
    BROADCAST = "broadcast"
    DELETE = "delete"
    CONCEAL = "conceal"
    RECONFIGURE = "reconfigure"


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


class Classify:
    BATCH_SIZE = 10
    SILENT = "the model returned no usable disposition, so a person has to look"


class Drafts:
    UNGROUNDED = "no earlier mail was found that could bear on this at all"
    INVENTED = "the draft cited nothing it was actually given"
    UNANSWERED = "the earlier mail does not answer this one"

    PUBLIC = ("quote", "one line", "a line", "on the record", "for publication",
              "short piece", "our piece", "our story", "coverage", "press")
    PUBLISHED = "no part of this draft may describe the company or the product"

    DESCRIBES = r"\b(?:paperjet|our product|the product|our platform|we)\s+(?:is|are|does|" \
                r"do|helps?|offers?|provides?|streamlines?|lets?|makes?)\b"

    DEFERRAL = frozenset(
        "yes true correct cannot unable afraid sorry apologies confirm confirmed confirming "
        "commit promise answer reply respond response revert return follow separately "
        "shortly soon later time date slot calendar schedule check checking look looking "
        "know let once able still yet more further details detail update touch back come "
        "coming regarding about sure good well great glad hear hearing see seeing sounds "
        "timing catch nice tell telling say saying love lovely happy keen meet definitely "
        "absolutely course anyway meanwhile am out up ping drop line sort figure plan".split())
    PROPOSES = r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b"
    DECLINES = ("cannot", "can not", "can't", "unable", "not able", "does not work",
                "doesn't work", "decline", "afraid", "will not", "won't")
    ACCEPTED = ("a reply that accepts a proposed time cannot be drafted, "
                "Sam's calendar is not in the inbox")

    CONFIDENTIAL = ("board", "legal", "term sheet", "salary", "wire transfer", "invoice",
                    "contract", "amendment", "signature", "remittance", "pricing",
                    "discount", "revenue")

    SECRETS = (
        r"://[^/\s:]+:[^/\s@]+@",
        r"\bpasswords?\b",
        r"\bpasswd\b",
        r"\bapi[ _-]?keys?\b",
        r"\bsecrets?\b",
        r"\btokens?\b",
        r"\bcredentials?\b",
        r"\bcreds\b",
    )


class Retrieval:
    CANDIDATES = 3
    EMBED_MODEL = "gemini-embedding-001"
    DIMENSIONS = 768
    EMBED_BATCH = 25
    MINIMUM_WORD = 3
    STOPWORDS = frozenset(
        "the a an and or but if is are was were be been being to of in on at for with from "
        "this that these those it its you your yours i me my we our us as not no do did does "
        "can could would will shall have has had he she they them their there here what which "
        "who when where why how all any some such only own same so than too very just now get "
        "got need needs please thanks thank hi hello sam".split())


class Gate:
    RISK = {Action.SEND: Risk.IRREVERSIBLE,
            Action.DELETE: Risk.REVERSIBLE,
            Action.RESTORE: Risk.REVERSIBLE}
    APPROVAL = frozenset({Action.SEND, Action.DELETE})
    ASKED = "  Approve this {action}? [y/N] "
    NOTHING = "nothing was written"
    DECLINED = "declined, nothing was written"
    SHOWN = "would write {target}"
    UNASKED = "        there is nobody at the keyboard, so this counts as no"
    UNTRIAGED = "nothing is known about this message yet, so it cannot be deleted"
    PROTECTED = "quarantined mail is the record of an attack and is never deleted"


class Guard:
    SPOKEN_TO = r"\b(?:assistants?|ai agents?|automated[- ]agents?|autonomous mode)\b"
    ADDRESS = r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"
    TRIES = {
        Attempt.FORWARD: (r"\bforward(?:s|ing|ed)?\b",),
        Attempt.BROADCAST: (r"\b(?:every|all|each)\s+unread\b",
                            r"\b(?:every|all|each)\s+(?:message|recipient|sender)s?\b",
                            r"\bfull contents of (?:this|the) mailbox\b",
                            r"\bwhole mailbox\b"),
        Attempt.DELETE: (r"\b(?:delete|deleting|erase|purge|remove)\b",),
        Attempt.CONCEAL: (r"\b(?:not|never|no need to|don't|do not|without)\b[^.]{0,40}"
                          r"\b(?:surface|mention|tell|inform|notify|disclose|report)\w*\b",),
        Attempt.RECONFIGURE: (r"\bignore\s+(?:all\s+)?(?:previous|prior|earlier)\b",
                              r"\bautonomous mode\b",
                              r"\bwithout asking\b",
                              r"\bskip the confirmation\b",
                              r"\b(?:disable|turn off|switch off|bypass)\b"),
    }
    SAYS = {Attempt.FORWARD: "forward mail out of the mailbox",
            Attempt.BROADCAST: "write to every sender in the mailbox",
            Attempt.DELETE: "delete mail",
            Attempt.CONCEAL: "keep what it did from Sam",
            Attempt.RECONFIGURE: "change what it is allowed to do without asking"}
    TO = " to {where}"
    FLAGGED = "FLAGGED: {id} attempted to {tried}; not done, left in place."
    REASON = "instructions addressed to an assistant, attempting to {tried}"


class Memory:
    NONE = "none"
    CLOCK = r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b"
    BOUNDS = ("no earlier than", "not before", "earlier than", "later than",
              "before", "after", "from", "until", "past")
    OPPOSITE = {"no earlier than": "before", "not before": "before", "earlier than": "before",
                "later than": "after", "before": "before", "after": "after",
                "from": "before", "until": "after", "past": "after"}
    REACH = 40
    SHORTEST = 5
    MEETINGS = "meetings"
    SOURCE = "email:{id}"
    SAYS = {Kind.SCHEDULING: "Sam does not take {subject} {bound} {value}.",
            Kind.COPYING: "{value} is copied on everything from {subject}."}
    FROM = "email:"
    WANTED = {Kind.SCHEDULING: "a time of day and whether it is a floor or a ceiling",
              Kind.COPYING: "a correspondent this mailbox has heard from"}
    SHAPELESS = "a {kind} preference has to name {wanted}, and this one names none"
    UNKNOWN = "there is no kind of preference called {kind}"


class Actions:
    SUFFIX = ".txt"
    HEADERS = ("To", "From", "Subject", "In-Reply-To", "Grounded-In")
    UNSENDABLE = "a refused draft has no body to send"
    KEPT = ".json"
    ABSENT = "there is no message {id} in the mailbox"
    HELD = "the trash holds nothing for {id}"
    ALREADY = "{id} is in the mailbox already"


class Model:
    TEMPERATURE = 0.0
    GAP_SECONDS = 4
    RETRIES = 3
    WAIT_SECONDS = 65
    TIMEOUT_SECONDS = 180


WIDTH = 78
