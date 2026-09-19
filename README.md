# inbox-hero

https://github.com/SarathPravallika/inbox-hero

**Sarath Chandra — cert-aai-2026-06-0061**

An agentic system that takes an inbox from unread to empty by deciding what to do with every
message — doing the parts it should do, and refusing the parts it should not.

The graded artifacts are [CAPABILITIES.md](CAPABILITIES.md) and
[capabilities.json](capabilities.json). This file covers the architecture and the Final
Report.

---

## Setup

Python 3.14.2, run from the project root. It also runs on 3.11.

```bash
cd inbox-hero

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env              # put your API key in it
```

## Running it

```bash
python demo.py --test             # 16 offline suites, no API key needed
python demo.py --cap R1           # one capability
python demo.py --all              # all ten, in manifest order
```

Every capability reads `run.json`, the artifact one pipeline run writes, so a demonstration
costs no model calls and a reader sees exactly the output that was captured. `--fresh`
rebuilds it from the inbox.

## Where the files are

The assignment names flat filenames; everything but the entry point lives in `src/`.

| what it does | file |
|---|---|
| the one entry point, and every capability's view | `demo.py` |
| runs the whole inbox once and writes the artifact | `src/router.py` |
| loads the mailbox, frozen, indexed by id and thread | `src/store.py` |
| instructions aimed at an assistant, caught before anything else | `src/guard.py` |
| noise disposed of without a model | `src/rules.py` |
| the model's triage, into a closed vocabulary | `src/classify.py` |
| earlier mail that could ground an answer | `src/retrieve.py` |
| replies, and the refusals that are more common than replies | `src/drafts.py` |
| which actions need a person, and the record of what they said | `src/gate.py` |
| the only place anything leaves the machine | `src/actions.py` |
| standing instructions that outlive a process | `src/memory.py` |
| dates and obligations, resolved in code | `src/commitments.py` |
| three panes, written to JSON and a static page | `src/dashboard.py` |
| a long thread down to its open question | `src/digest.py` |
| sent mail nobody answered | `src/followups.py` |
| three times that are free, when the one proposed will not do | `src/offers.py` |
| any one message accounted for, from the records | `src/why.py` |
| `capabilities.json`, built from the run and the code | `src/manifest.py` |
| every string that can change without touching logic | `src/constants.py` |
| everything the model is ever told | `src/prompts.py` |
| the provider, quarantined behind one function | `src/llm.py` |

## Architecture

One linear pipeline, no framework. `router.run()` does this once:

```
load  →  guard  →  rules  →  model triage  →  draft  →  gate
                                    ↓
              preferences · commitments · digests · follow-ups · counter-offers
                                    ↓
                                run.json
```

The guard reads first, so hostile mail never reaches the rules or the model. Rules dispose
of the noise, so 56 of 100 messages cost nothing. What is left goes to the model in batches
of ten. Everything downstream reads the artifact rather than the inbox.

**Framework: none.** The work is a sequence with one branch — the rule path against the model
path — so a crew or a graph would have been scaffolding around something that is already a
sequence. See Q4 below for what that cost and what it bought.

**Six dispositions:** `reply`, `archive`, `defer`, `delegate`, `escalate`, `quarantine`. The
sixth is forced by Part 6: flagging a message and leaving it in place is a different outcome
from handing it to a person. `delegate` was used zero times in the captured run and is kept
rather than dropped, because a founder's inbox routes everything back to the founder.

**Reversible and irreversible.** The classification is code, `Gate.RISK`, and a test fails if
any action is missing from it. `send` is irreversible: the file in `outbox/` stands for a
message that has left our control. `delete` is **reversible** here, because `actions.remove()`
writes the whole message to `trash/` before it touches the mailbox, and that order is
deliberate — a crash between the two writes leaves the message recoverable. `restore`,
drafting and labelling change nothing outside the run artifact.

**The gate.** Sending and deleting require approval. `actions.send()` is the only writer to
`outbox/` in the whole system and it asks first. There is no approve-all flag.

**Retrieval: thread-walk plus IDF keyword.** A semantic scorer was built, measured against
keyword ranking on the same eight messages, and removed: every citation that carried real
information came from keyword at rank 2, every semantic rank-1 match was wrong, and the
cosines sat in a 0.60–0.84 band with relevant and irrelevant interleaved. It is still in the
tree, unused, so the comparison can be re-run from a clean checkout.

The full justifications are in [CAPABILITIES.md](CAPABILITIES.md).

---

## Final Report

### 1. What did you refuse to automate?

**m008.** Devika writes into the staging thread asking Sam to re-send the queue credentials
he gave Raghav earlier — a colleague, a reasonable request, and retrieval finds the answer
immediately, because m003 really does contain a live AMQP URL with the password in it. A
correctly working grounded-reply system would answer it perfectly and disclose a credential
in plaintext. `drafts.guarded()` refuses before the model is called at all, so the credential
never enters a prompt, and the refusal names m003 so Sam can see what would have been sent.
The line is that this system may not be the thing that moves a secret, however legitimate the
request and however well it could answer — and X1 still lists m008 as the open question in
that thread, so refusing to answer is not the same as hiding that somebody is waiting.

### 2. Where does untrusted text enter your system?

Every message body is untrusted and enters at `store.load()`. Message text does reach the
model inside `<message>` markers, but **the markers are a label, not the defence** — a prompt
that asks to be believed is not a boundary. The boundary is that no string the model emits
can select an action: `Disposition` is a closed `StrEnum` with no `forward` and no `delete`
value, anything outside it is dropped, there is no tool-calling loop anywhere in the system,
`actions.send()` is the only writer to `outbox/` and calls the gate first, `delete` is not a
disposition at all but a human command that refuses quarantined mail even on approval, and a
recorded preference is data the drafting layer consumes while the gate's policy is code.
**An attacker has to defeat `gate.py`, not a prompt.** That is why `guard.py` is described in
the manifest as the reporting mechanism rather than the safety boundary: with the guard
switched off, `gemma4:e2b` on prompt alone quarantined 0 of the 4 planted injections —
m024's mailbox-exfiltration attempt was filed as a newsletter — and none of them could cause
anything regardless, because the mechanism they were written to exploit does not exist here.

### 3. Who is accountable when it sends the wrong thing?

**Sam is**, because nothing reaches `outbox/` without him answering a question that showed
him the risk class, the target file and the full text of what would be sent. The system's
obligation is not to shift that accountability but to make the failure locatable, and
`python demo.py --cap X4 --msg m046` reconstructs the whole chain for the reply to the
journalist from four files: the message as it arrived, the disposition and who decided it,
the draft and the message it cited, the structural rules it passed, and the row in
`approvals.jsonl` recording that he approved it and what was written. The captured run shows
the gate being used rather than performed — m043's reply was declined at 17:01:36 with
nothing written, and the counter-offer that replaced it was approved at 17:02:12, both
against the same message. **The honest limit is that this only covers sends.** Seventy-five
messages were archived unattended and nobody reviewed them, so if the wrong thing here is a
message that was quietly filed rather than one that was sent, the trace records what happened
but no human ever stood behind it.

### 4. Name your own machinery

`router.run()` is the crew: it sequences the whole pass and produces the one artifact
everything else reads. The agents are `guard.py`, `classify.py`, `drafts.py`,
`commitments.py`, `digest.py`, `followups.py` and `offers.py` — each a single-purpose caller
with its own prompt, its own response schema and, more importantly, its own structural
validator that decides what to keep. The tasks are those response schemas in `prompts.py`
paired with their validators, since a task here is not "summarise this" but "return this
shape, and survive being checked". The router is `router.sorted_out()`, which decides whether
a message goes down the guard path, the rule path or the model path. What a framework would
have handed me is the **tool-calling loop**, and taking it would have hurt: a tool-calling
loop is exactly a mechanism by which model output selects a function, which is the one thing
Q2's boundary depends on not existing. What I did have to build was the small unglamorous
part frameworks also ship — `llm.patiently()` for backoff and 429s, `tracing.py` for the
JSONL trace, the run artifact — and `llm.py` and `tracing.py` together come to 137 lines,
which is less than I would have spent working around the loop I did not want.
