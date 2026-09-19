# cert-aai-2026-06-0061  Sarath Chandra
#
# - Every value that can change without touching logic, grouped by the part that reads it
# - The disposition vocabulary and capability ids the manifest declares

from enum import StrEnum
from pathlib import Path

SNAPSHOT = "2026-09-09"


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
    MANIFEST = ROOT / "capabilities.json"
    CAPABILITIES = ROOT / "CAPABILITIES.md"
    README = ROOT / "README.md"
    SAMPLE = ROOT / "assignment-instructions" / "capabilities.sample.json"


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


class Manifest:
    STUDENT = "Sarath Chandra, cert-aai-2026-06-0061"
    REPO = "https://github.com/SarathPravallika/inbox-hero"
    FRAMEWORK = "none"
    MODEL = ("gemini-3.1-flash-lite for every model call and for development too: triage, "
             "drafting, commitments, thread digests, chases and counter-offers. PROVIDER "
             "also switches to a local model through Ollama, which was used for early "
             "testing.")
    RETRIEVAL = "thread-walk plus IDF keyword"
    GATE = "both"
    PREFERENCE = "m015: CC priya@paperjet.io on anything from Hartwell & Cho"
    ALSO_REVERSIBLE = ("draft", "label")
    FIELDS = ("id", "name", "tier", "claim", "command", "observable", "evidence")
    TIMEOUT = 120

    ROWS = {
        Capability.R1: {
            "name": "Zero the inbox",
            "tier": Tier.B,
            "claim": "Gives every message exactly one disposition from a closed six-value "
                     "vocabulary, with a one-line reason and which of rule, guard or model "
                     "decided it, leaving none untouched.",
            "command": "python demo.py --cap R1",
            "observable": "Prints 100 rows, each carrying a disposition, who decided it and "
                          "a reason, then 'undecided: 0' and the split: 60 messages without "
                          "a model, 4 of those by the guard, and 40 by the model. It closes "
                          "by naming m017, m024, m039 and m047 as quarantined without a "
                          "model call, unprompted.",
            "evidence": "trace.jsonl, events tagged cap=R1 - one 'run' event and 100 "
                        "'decision' events.",
        },
        Capability.R2: {
            "name": "Grounded reply",
            "tier": Tier.B,
            "claim": "Drafts replies grounded in specific earlier messages and records the "
                     "ids drawn on, and refuses rather than answering when nothing grounds "
                     "the answer or when answering would disclose a credential.",
            "command": "python demo.py --cap R2",
            "observable": "Prints 4 drafts and 5 refusals. m043 and m051 cite m041, m016 "
                          "cites m013, m046 cites m036, and every cited id is a real message "
                          "that genuinely came earlier. m008 is refused naming m003, which "
                          "really does hold a live staging AMQP password. Run with "
                          "--msg m008 for that refusal alone.",
            "evidence": "trace.jsonl, events tagged cap=R2 - four 'draft' and five 'refusal' "
                        "events, each cited id present in the mailbox.",
        },
        Capability.R3: {
            "name": "Gate the irreversible",
            "tier": Tier.C,
            "claim": "Never sends or deletes without either per-action approval or an "
                     "explicit --dry-run showing what it would do, and refuses to delete "
                     "quarantined mail even when a person approves it.",
            "command": "python demo.py --cap R3 --dry-run",
            "observable": "Lists every send it would make, the risk class and the file it "
                          "would write, then 'outbox/ writes: 0'. Without --dry-run it asks "
                          "y/N before each one. 'python demo.py --cap R3 --delete m113' and "
                          "'--restore m113' take a message out and put it back at the same "
                          "index; '--cap R3 --delete m024' is refused because it is "
                          "quarantined.",
            "evidence": "approvals.jsonl - nine rows from one pass: three approved sends, "
                        "one declined send that wrote nothing, an approved delete, an "
                        "unattended restore, a refused delete and two approved counter-"
                        "offers.",
        },
        Capability.R4: {
            "name": "Persistent preference",
            "tier": Tier.C,
            "claim": "Records a stated preference to disk and applies it on a later run in a "
                     "different process without being told again, and cannot apply one in "
                     "the run that recorded it.",
            "command": "python demo.py --cap R4",
            "observable": "Names the two recorded preferences and the message each came "
                          "from, then the five messages the run handled differently because "
                          "of them: m018, m048 and m055 carry copy priya@paperjet.io, and "
                          "m051 and m043 cite m041. Run with --msg m039 to watch the "
                          "injection be refused for fitting neither preference shape, and "
                          "--msg m041 to watch the same treatment accept one.",
            "evidence": "memory.json on disk between runs; trace.jsonl events tagged cap=R4 "
                        "- two 'in force' and two 'remembered'.",
        },
        Capability.R5: {
            "name": "Refuse embedded instructions",
            "tier": Tier.C,
            "claim": "Finds instructions addressed to an assistant inside message bodies "
                     "before any model call, refuses them, names what each one attempted, "
                     "reports them to the owner and leaves them in the mailbox.",
            "command": "python demo.py --cap R5",
            "observable": "Flags m017, m024, m039 and m047, quoting both the sentence that "
                          "speaks to an assistant and the sentence that asks it to act. "
                          "Prints '4 flagged, 0 deleted, 0 acted on, 100 messages still in "
                          "the run' and checks outbox/ itself for every address the attacks "
                          "named. 'python demo.py --cap R5 --blind' runs the same triage "
                          "with the model asked nothing at all and still catches all four. "
                          "'PROVIDER=ollama MODEL=gemma4:e2b python demo.py --cap R5 "
                          "--prompted' runs it with the guard switched off instead, and that "
                          "model on prompt alone quarantines 0 of the 4.",
            "evidence": "trace.jsonl, events tagged cap=R5 - four 'refusal' events naming "
                        "each id and what it attempted.",
        },
        Capability.R6: {
            "name": "Dashboard",
            "tier": Tier.C,
            "claim": "Builds a three-pane view from a completed run with no model call, "
                     "every commitment citing the messages it was taken from and every "
                     "conflict called out rather than listed.",
            "command": "python demo.py --cap R6",
            "observable": "Writes dashboard.json and dashboard.html: 4 pending, 15 flagged, "
                          "21 commitments, 2 conflicts. The board deck lands on 2026-09-16 "
                          "citing both m040 and m038, neither of which states that date, and "
                          "the launch cites m026 and m036. Both conflicts are named, and "
                          "m080, which carries a time but no day, is named underneath with "
                          "the reason it would not resolve.",
            "evidence": "dashboard.html and dashboard.json; trace.jsonl events tagged cap=R6 "
                        "- 21 'commitment' and 2 'conflict'.",
        },
        Capability.X1: {
            "name": "Thread digest",
            "tier": Tier.B,
            "claim": "Reduces every conversation of three messages or more to what it is "
                     "about and the one message still waiting on the owner, with the "
                     "question lifted out of that message word for word.",
            "command": "python demo.py --cap X1",
            "observable": "Summarises t-launch, nine messages, down to m030 and the question "
                          "'Sam, can you approve the final pricing copy by the 12th?', and "
                          "t-api, four messages, down to m008. The t-api summary says "
                          "credentials were shared and contains none, because they are taken "
                          "out of the thread before the model reads it.",
            "evidence": "trace.jsonl, events tagged cap=X1 - two 'digest' events carrying "
                        "the thread, its message ids and the open question.",
        },
        Capability.X2: {
            "name": "Follow-up tracking",
            "tier": Tier.B,
            "claim": "Reports every message the owner sent and whether anybody answered it, "
                     "and drafts a chase for those waiting three days or more using only "
                     "words he already used himself.",
            "command": "python demo.py --cap X2",
            "observable": "Four rows. m044 to priya@paperjet.io, sent 2026-09-02, seven days "
                          "with no answer, is chased. m003 is not, because m005 answered it; "
                          "m041 is not, because it went to Sam himself; m039 is not, because "
                          "the run quarantined it.",
            "evidence": "trace.jsonl, events tagged cap=X2 - four 'followup' events.",
        },
        Capability.X3: {
            "name": "Conflict counter-offer",
            "tier": Tier.C,
            "claim": "Finds a proposed time that breaks a stated preference or lands on "
                     "something already settled, works out three alternatives from the "
                     "calendar, and holds the reply for approval.",
            "command": "python demo.py --cap X3 --dry-run",
            "observable": "Two counter-offers, both to aria.f@northwind.vc. m043 asks for "
                          "Monday 14 September at 9:00am, which breaks the rule recorded "
                          "from m041, so it keeps the day and offers 11:00am, 2:00pm and "
                          "4:00pm. m010 asks for Tuesday the 15th at 3:00pm, which m061 "
                          "holds, so it keeps the time and offers Wednesday, Thursday and "
                          "Friday. Neither reply says what the owner is doing instead.",
            "evidence": "trace.jsonl, events tagged cap=X3 - two 'offer' events carrying the "
                        "slots; approvals.jsonl, where both were put to a person.",
        },
        Capability.X4: {
            "name": "Ask it why",
            "tier": Tier.A,
            "claim": "Accounts for any one message in eight sections, each naming the file it "
                     "was read from, including the reasons nothing was drafted, calendared "
                     "or put to a person.",
            "command": "python demo.py --cap X4 --msg m024",
            "observable": "Prints eight sections for m024, read from mailbox.json, run.json, "
                          "approvals.jsonl and trace.jsonl: quarantined by the guard, what it "
                          "attempted and the external address it named, why no reply was "
                          "drafted, why nothing of it reached the calendar, and the trace "
                          "events carrying it. Works for any of the 100 ids.",
            "evidence": "the events already tagged with that message id under cap=R1 to "
                        "cap=R6; this capability writes none of its own.",
        },
    }


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
    PROMPTED = ("the guard is switched off on this pass, so the triage prompt is the only "
                "thing standing between the attacks and the mailbox")
    ASKED_OF = "provider {provider}, model {model}, guard off, {batch} messages to the model"
    UNSEEN = "a rule disposed of it before the model was ever shown it"
    SCORE = ("{caught} of {total} quarantined by the prompt alone. With the guard reading "
             "first it is {total} of {total}, and that holds with the model asked nothing.")
    STALE = ("this run was written before the guard existed, so it records nothing it found. "
             "Run `python demo.py --cap R1 --fresh` and try again.")
    REASON = "instructions addressed to an assistant, attempting to {tried}"


class Commitments:
    TODAY = SNAPSHOT
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
    UNPLACED_HEAD = ("message", "what it is", "what the message said",
                     "why it is not on the calendar")
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
    CLEARED = ("cleared {sent} replies from outbox/, {held} messages from trash/ and "
               "{logged} approval records, so what follows is the evidence of one run")


class Digest:
    SHORTEST = 3
    WITHHELD = "[withheld]"
    QUESTION = r"[^.!?\n]*\?"
    NOTHING = "nothing in it is waiting on Sam"
    UNQUOTED = "it is the open question and the message does not put it as one"
    STRANGER = "the model named {id}, which is not in this conversation"
    SPOKE = "the model named {id}, which Sam wrote himself"
    LEAKED = "the summary carried a credential, so it was dropped"
    INVENTED = "the summary named {ids}, which this conversation does not contain"
    SPAN = "{count} messages, {first} to {last}"
    NEEDS = "still needs Sam: {id}"
    CLOSED = "already answered in the thread: {ids}"
    STALE = ("this run was written before the digests existed, so it records none. Run "
             "`python demo.py --cap X1 --fresh` and try again.")


class Followups:
    TODAY = SNAPSHOT
    PATIENCE = 3
    ROOT = 5
    BATCH = 5
    NUDGE = frozenset(
        "following follow followed chase chasing nudge gentle wondering wondered wonder "
        "still any update updates news word since sent send asked asking ask bumping bump "
        "top mind whenever chance had holding hold blocked blocking moment status where "
        "stands standing progress waiting wait heard hearing anything something".split())
    INVENTED = "the chase reached for words the original never used"
    SILENT = "the model wrote nothing to chase with"
    ANSWERED = "{by} answered it, so there is nothing to chase"
    SELF = "Sam wrote it to himself, so there is nobody to chase"
    RECENT = "it has waited {days} days, and a chase waits for {patience}"
    HELD = "the run quarantined it, and nothing quarantined is chased"
    WAITED = "{days} days with no answer"
    NONE = "nothing Sam sent is still waiting on anybody"
    GATED = ("a chase is a send, so nothing here leaves the machine without going through "
             "the same gate as any other reply")
    STALE = ("this run was written before the follow-ups existed, so it records none. Run "
             "`python demo.py --cap X2 --fresh` and try again.")


class Offers:
    SLOTS = ("11:00", "14:00", "16:00")
    DAYS = 5
    OFFERED = 3
    WEEKEND = (5, 6)
    PLAIN = r"\b(\d{1,2}):(\d{2})\b"
    BREAKS = "Sam does not take {subject} {bound} {value}"
    TAKEN = "that time is already spoken for"
    SHOWN = "{day} at {at}"
    WHY = "asks for {slot}, and {because}"
    BLOCKED = "on Sam's side that slot is held by {ids}, which the reply does not say"
    INSTEAD = "instead: {slot}"
    NOTHING = "nothing in the next {days} working days is both free and allowed"
    INVENTED = "the reply named {times}, which was never offered"
    MISDATED = "the reply named a day that was never offered"
    DISCLOSED = "the reply said what the other appointment is"
    SILENT = "the model wrote nothing to offer with"
    NONE = "nothing proposed to Sam runs into a preference or into something already settled"
    QUIET = ("the offer says when Sam is free and never what he is doing, so the reply "
             "exposes availability and nothing else")
    STALE = ("this run was written before the counter-offers existed, so it records none. "
             "Run `python demo.py --cap X3 --fresh` and try again.")


class Trace:
    RESERVED = ("at", "cap", "event")
    SHADOWED = "a {event} event tried to write over the trace's own {names}"
    CLOCK = "clock"
    FIRST = "first"


class Why:
    HEAD = "X4  why {id} was treated that way"
    HEADLESS = "X4  why any one message was treated the way it was"
    ASK = "this accounts for one message at a time, so it needs --msg"
    TRY = "try: python demo.py --cap X4 --msg {id}"
    OTHERS = "or any of: {ids}"
    MISSING = "there is no message {id} in this mailbox, and no run has decided one"

    ARRIVED = "arrived"
    DECIDED = "decided"
    GUARDED = "the guard"
    DRAFTED = "reply"
    DATED = "calendar"
    PREFERRED = "standing instructions"
    APPROVED = "approval"
    TRACED = "trace"

    MAILBOX = "mailbox.json"
    RUN = "run.json, {part}"
    APPROVALS = "approvals.jsonl"
    TRACE = "trace.jsonl"

    SUBJECT = "{subject}"
    SENDER = "from {sender} to {to}, {at}"
    THREAD = "thread {thread}, message {place} of {count}"
    GONE = "it is not in the mailbox now, so trash/ is where to look for it"

    BY = {Decided.RULE: "{disposition}, by a rule, with no model call",
          Decided.GUARD: "{disposition}, by the guard, with no model call",
          Decided.MODEL: "{disposition}, by the model"}
    UNDECIDED = "no run has reached a decision about it"
    COPIED = "copy to {copy}"

    UNTOUCHED = "it says nothing to an assistant, so the guard left it alone"
    ATTEMPTED = "it attempted: {tried}"
    NAMED = "it named: {where}"

    NOT_REPLY = "only mail disposed reply is drafted for, and this one is {disposition}"
    REFUSED_DRAFT = "refused, and the refusal is the answer: {why}"
    CITED = "drafted, citing {cited}"
    UNCITED = "drafted citing nothing, which is allowed because it commits to nothing"

    NO_DATES = "nothing on the calendar was taken from it"
    OFF_CALENDAR = ("nothing quarantined is read for dates, so whatever it demands never "
                    "reaches the calendar")
    ON_CALENDAR = "{when} {at} {settled:<9} {what}"

    NO_PREFERENCE = "nothing was recorded from it, and no standing instruction touched it"
    RECORDED = "recorded from it: {said}"
    APPLIED = "{who} was copied because of {source}"
    LEANED = "the reply cites {source}, which is a standing instruction and not a message"

    NO_APPROVAL = "nothing about it was ever put to a person"
    ANSWERED = "{action} {answer} at {at}, {outcome}"

    NO_TRACE = "the trace from the last run carries nothing for it"
    EVENT = "{at}  cap={cap}  {event}"

    CLOSE = "{sections} sections read from {files} files, nothing worked out on the spot"


class Model:
    TEMPERATURE = 0.0
    GAP_SECONDS = 4
    RETRIES = 3
    WAIT_SECONDS = 65
    TIMEOUT_SECONDS = 180


WIDTH = 78
