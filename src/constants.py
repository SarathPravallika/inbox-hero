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
    DASHBOARD = ROOT / "dashboard.json"
    PAGE = ROOT / "dashboard.html"


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


class Settled(StrEnum):
    SETTLED = "settled"
    PROPOSED = "proposed"
    OWED = "owed"


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
    CARRIED = ("{count} messages carried instructions for an assistant and were quarantined "
               "without a model call: {names}")
    CLEAN = "outbox/ holds nothing addressed to any of them"
    REACHED = "outbox/{name} is addressed to {where}"
    BLIND = "the model was asked nothing at all on this pass"
    STALE = ("this run was written before the guard existed, so it records nothing it found. "
             "Run `python demo.py --cap R1 --fresh` and try again.")
    REASON = "instructions addressed to an assistant, attempting to {tried}"


class Commitments:
    TODAY = "2026-09-09"
    BATCH = 15
    DATED = (r"\b(?:\d{1,2}(?:st|nd|rd|th)\b|mon|tues|wednes|thurs|fri|satur|sun|january"
             r"|february|march|april|may|june|july|august|september|october|november"
             r"|december|today|tomorrow|month[- ]end|end of (?:the )?(?:month|week|day)"
             r"|deadline|due\b|\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm)\b"
             r"|(?:days?|weeks?)\s+(?:before|after)|ahead of|by the \d|before the \d)")
    ORDINAL = r"\b(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)\b"
    NAMED = (r"\b(january|february|march|april|may|june|july|august|september|october"
             r"|november|december)\s+(\d{1,2})\b")
    WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    CLOCK = r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b"
    MONTH_END = r"\bmonth[- ]end\b|\bend of (?:the )?month\b"
    TODAY_WORDS = r"\btoday\b|\btonight\b|\bend of (?:the )?day\b|\bthis evening\b"
    TOMORROW = r"\btomorrow\b"
    COUNTS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
              "a": 1, "an": 1}
    RELATIVE = r"\b(\w+)\s+(days?|weeks?)\s+(before|after)\s+(.{3,60})"
    SHORTEST = 4
    ANCHORED = "{days} days {way} {anchor}"
    CLASH = "CONFLICT: {what} at {when}"
    NOTHING = "no date could be resolved from {said!r}"
    SAME = "{what}"


class Dashboard:
    PANES = ("Pending actions", "Flagged", "Commitments")
    WHY = "sending is irreversible, the message leaves the machine and cannot be recalled"
    PROPOSED = "send the drafted reply to {to}"
    LEFT = "quarantined, left in the mailbox"
    RAISED = "escalated, nothing done without Sam"
    NOTHING = "no reply written"
    UNACCEPTED = "claimed"
    UNPLACED = "{count} dated thing{s} could not be placed on the calendar"
    NONE = "nothing"
    TITLE = "inboxHero"
    LEDE = "Three panes from one run. Nothing here was written by hand."
    SAYS = ("What the system wants to do and may not do alone.",
            "Everything it would not act on, and what it did instead.",
            "Dates and obligations, each carrying the mail it was taken from.")
    FOOT = ("Built by demo.py --cap R6 from run.json. Re-run it and this page is rebuilt "
            "exactly, from the same artifact.")
    STYLE = """
:root{--bg:#fbfbfd;--card:#fff;--ink:#17171c;--soft:#6b6b78;--line:#e7e7ee;
--blue:#2563eb;--rose:#e11d48;--teal:#0d9488;--amber:#b45309;
--blue-bg:#eef3ff;--rose-bg:#fff1f4;--teal-bg:#edfbf8;--amber-bg:#fff8ec}
@media (prefers-color-scheme:dark){:root{--bg:#131317;--card:#1c1c23;--ink:#ececf2;
--soft:#9797a6;--line:#2b2b35;--blue:#7ea2ff;--rose:#ff8098;--teal:#4fd0bd;--amber:#e8b45c;
--blue-bg:#182036;--rose-bg:#2b1720;--teal-bg:#102623;--amber-bg:#2a2115}}
*{box-sizing:border-box}
body{margin:0;padding:2.5rem 1.25rem 3rem;background:var(--bg);color:var(--ink);
font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:74rem;margin:0 auto}
h1{font-size:1.7rem;margin:0 0 .3rem;letter-spacing:-.02em}
.sub{margin:0;color:var(--soft)}
.tally{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.3rem 0 0;padding:0;list-style:none}
.tally li{background:var(--card);border:1px solid var(--line);border-radius:999px;
padding:.3rem .9rem;font-size:.85rem;color:var(--soft)}
.tally b{color:var(--ink);font-variant-numeric:tabular-nums}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;
margin:1.8rem 0 0;overflow:hidden}
.head{padding:1rem 1.25rem .85rem;border-bottom:1px solid var(--line)}
h2{font-size:1.05rem;margin:0;display:flex;align-items:center;gap:.65rem}
.num{display:grid;place-items:center;width:1.6rem;height:1.6rem;border-radius:9px;
font-size:.82rem;color:#fff;flex:none}
.lede{margin:.4rem 0 0;color:var(--soft);font-size:.9rem}
.p1 .num{background:var(--blue)}.p1 .head{background:var(--blue-bg)}
.p2 .num{background:var(--rose)}.p2 .head{background:var(--rose-bg)}
.p3 .num{background:var(--teal)}.p3 .head{background:var(--teal-bg)}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th{text-align:left;font-weight:600;color:var(--soft);font-size:.72rem;
text-transform:uppercase;letter-spacing:.07em;padding:.75rem 1.25rem .45rem}
td{padding:.6rem 1.25rem;border-top:1px solid var(--line);vertical-align:top}
.id{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85rem;color:var(--soft)}
.at{font-variant-numeric:tabular-nums;white-space:nowrap}
.clash{margin:0;padding:.8rem 1.25rem;background:var(--amber-bg);color:var(--amber);
border-bottom:1px solid var(--line);font-weight:600;font-size:.9rem}
.day td{background:var(--bg);font-weight:600;font-size:.8rem;letter-spacing:.04em;
color:var(--soft);text-transform:uppercase}
.pill{display:inline-block;padding:.1rem .6rem;border-radius:999px;font-size:.76rem;
font-weight:600;border:1px solid currentColor;white-space:nowrap}
.settled{background:var(--teal-bg);color:var(--teal)}
.proposed{background:var(--blue-bg);color:var(--blue)}
.owed{background:var(--amber-bg);color:var(--amber)}
.claimed{background:var(--rose-bg);color:var(--rose)}
.note{margin:0;padding:.75rem 1.25rem;color:var(--soft);font-size:.85rem;
border-top:1px solid var(--line)}
.cal{padding:1.1rem 1.25rem .4rem}
.cal h3{margin:0 0 .65rem;font-size:.95rem;letter-spacing:.01em}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}
.dow{font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;color:var(--soft);
font-weight:600;padding:.15rem .3rem}
.cell{min-height:5rem;border:1px solid var(--line);border-radius:9px;padding:.3rem;
background:var(--bg);display:flex;flex-direction:column;gap:3px}
.cell.empty{background:transparent;border-color:transparent;min-height:0}
.cell.now{border-color:var(--blue);box-shadow:inset 0 0 0 1px var(--blue)}
.cell.clashday{background:var(--amber-bg);border-color:var(--amber)}
.dnum{font-size:.72rem;font-weight:700;color:var(--soft);font-variant-numeric:tabular-nums}
.chip{font-size:.67rem;line-height:1.3;border-radius:5px;padding:.16rem .34rem;
border:1px solid currentColor;display:flex;flex-direction:column;gap:1px;min-width:0}
.cw{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}
.ci{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.6rem;opacity:.8;
overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.key{display:flex;flex-wrap:wrap;gap:.45rem;padding:.9rem 1.25rem 0;font-size:.74rem;
color:var(--soft);align-items:center}
@media(max-width:46rem){.cell{min-height:3.6rem;padding:.18rem}.chip{font-size:.58rem}
.grid{gap:2px}}
footer{margin:1.8rem 0 0;color:var(--soft);font-size:.83rem}
@media(max-width:40rem){td,th{padding-left:.9rem;padding-right:.9rem}}
"""


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
