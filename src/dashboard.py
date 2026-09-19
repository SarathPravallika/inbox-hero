# cert-aai-2026-06-0061  Sarath Chandra
#
# - Turns one completed run into three panes, and nothing here asks a model anything
# - Pending actions is the gate's queue: what the system wants to do and may not do alone
# - Flagged is everything it would not act on, with what was attempted beside what it did
# - Commitments is a month grid, and every entry on it carries the message ids it came from
#   on its own line, because a citation in a hover tooltip is no citation on a printed page
# - Anything dated that could not be placed is named underneath with what the message said
#   and why it would not resolve, so a count never stands in for the thing it counted
# - An obligation taken from mail the system escalated is shown as claimed, not accepted,
#   because a demand for a wire transfer should never read like a bill that is due

import html
import json
from calendar import monthcalendar as monthdays
from datetime import date
from constants import Commitments, Dashboard, Disposition, Paths


def sendable(artifact: dict) -> list[dict]:
    return [made for made in artifact["drafts"] if not made["refused"]]


def pending(artifact: dict, store) -> list[dict]:
    rows = []
    for made in sendable(artifact):
        rows.append({"id": made["id"],
                     "action": Dashboard.PROPOSED.format(
                         to=store.message(made["id"]).sender),
                     "why": Dashboard.WHY,
                     "cited": made["cited"],
                     "body": made["body"]})
    return rows


def held(artifact: dict) -> dict:
    return {decision["id"]: decision for decision in artifact["decisions"]}


def flagged(artifact: dict) -> list[dict]:
    disposed = held(artifact)
    refused = {one["id"]: one for one in artifact["refusals"]}
    rows = []

    for name, decision in disposed.items():
        if decision["disposition"] == Disposition.QUARANTINE:
            attempt = refused[name]["flagged"] if name in refused else decision["reason"]
            rows.append({"id": name, "attempted": attempt, "instead": Dashboard.LEFT})
        elif decision["disposition"] == Disposition.ESCALATE:
            rows.append({"id": name, "attempted": decision["reason"],
                         "instead": Dashboard.RAISED})

    for made in artifact["drafts"]:
        if made["refused"]:
            rows.append({"id": made["id"], "attempted": made["refused"],
                         "instead": Dashboard.NOTHING})
    return sorted(rows, key=lambda row: row["id"])


def calendar(artifact: dict) -> list[dict]:
    disposed = held(artifact)
    rows = []
    for one in artifact["commitments"]:
        if not one["when"]:
            continue
        raised = disposed.get(one["id"], {}).get("disposition") == Disposition.ESCALATE
        rows.append({**one, "standing": Dashboard.UNACCEPTED if raised else one["settled"]})
    return rows


def unplaced(artifact: dict) -> list[dict]:
    return [one for one in artifact["commitments"] if not one["when"]]


def view(artifact: dict, store) -> dict:
    return {
        "at": artifact["at"],
        "pending": pending(artifact, store),
        "flagged": flagged(artifact),
        "commitments": calendar(artifact),
        "conflicts": artifact["conflicts"],
        "unplaced": unplaced(artifact),
    }


def days(rows: list[dict]) -> dict:
    grouped = {}
    for row in rows:
        grouped.setdefault(row["when"], []).append(row)
    return grouped


def write(made: dict) -> dict:
    Paths.DASHBOARD.write_text(json.dumps(made, indent=2) + "\n")
    Paths.PAGE.write_text(page(made))
    return made


def cell(text) -> str:
    return html.escape(str(text))


def unplaced_line(made: dict) -> str:
    count = len(made["unplaced"])
    return Dashboard.UNPLACED.format(count=count, s="" if count == 1 else "s")


def named(when: str) -> str:
    made = date.fromisoformat(when)
    return made.strftime("%A %-d %B").replace(" 0", " ")


def pane(number: int, title: str, lede: str, body: str) -> str:
    return (f"<section class='p{number}'><div class='head'><h2>"
            f"<span class='num'>{number}</span>{cell(title)}</h2>"
            f"<p class='lede'>{cell(lede)}</p></div>{body}</section>")


def waiting_pane(made: dict) -> str:
    out = ["<table><tr><th>message</th><th>proposed action</th>"
           "<th>why it needs a person</th></tr>"]
    for row in made["pending"]:
        out.append(f"<tr><td class='id'>{cell(row['id'])}</td>"
                   f"<td>{cell(row['action'])}</td><td>{cell(row['why'])}</td></tr>")
    out.append("</table>")
    return pane(1, Dashboard.PANES[0], Dashboard.SAYS[0], "".join(out))


def flagged_pane(made: dict) -> str:
    out = ["<table><tr><th>message</th><th>what was attempted</th>"
           "<th>what it did instead</th></tr>"]
    for row in made["flagged"]:
        out.append(f"<tr><td class='id'>{cell(row['id'])}</td>"
                   f"<td>{cell(row['attempted'])}</td><td>{cell(row['instead'])}</td></tr>")
    out.append("</table>")
    return pane(2, Dashboard.PANES[1], Dashboard.SAYS[1], "".join(out))


def months(rows: list[dict]) -> list[tuple[int, int]]:
    seen = {(int(row["when"][:4]), int(row["when"][5:7])) for row in rows}
    return sorted(seen)


def clashing(made: dict) -> set[str]:
    return {one["when"] for one in made["conflicts"] if one.get("when")}


def chip(row: dict) -> str:
    said = f"{row['at']} {row['what']}" if row["at"] else row["what"]
    told = f"{row['what']} — {row['standing']}, from {', '.join(row['cited'])}"
    return (f"<span class='chip {cell(row['standing'])}' title='{cell(told)}'>"
            f"<span class='cw'>{cell(said)}</span>"
            f"<span class='ci'>{cell(', '.join(row['cited']))}</span></span>")


def cells(year: int, month: int, made: dict) -> str:
    byday = days(made["commitments"])
    hot = clashing(made)
    out = [f"<div class='dow'>{name}</div>"
           for name in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")]
    for week in monthdays(year, month):
        for day in week:
            if not day:
                out.append("<div class='cell empty'></div>")
                continue
            when = f"{year:04d}-{month:02d}-{day:02d}"
            marks = " now" if when == Commitments.TODAY else ""
            marks += " clashday" if when in hot else ""
            chips = "".join(chip(row) for row in byday.get(when, ()))
            out.append(f"<div class='cell{marks}'><span class='dnum'>{day}</span>"
                       f"{chips}</div>")
    return "".join(out)


def grids(made: dict) -> str:
    out = []
    for year, month in months(made["commitments"]):
        shown = date(year, month, 1).strftime("%B %Y")
        out.append(f"<div class='cal'><h3>{cell(shown)}</h3>"
                   f"<div class='grid'>{cells(year, month, made)}</div></div>")
    keys = "".join(f"<span class='pill {name}'>{name}</span>"
                   for name in ("settled", "proposed", "owed", Dashboard.UNACCEPTED))
    out.append(f"<div class='key'>{keys}<span>today is outlined, a clash is amber</span></div>")
    return "".join(out)


def missing(made: dict) -> str:
    if not made["unplaced"]:
        return ""
    head = "".join(f"<th>{cell(name)}</th>" for name in Dashboard.UNPLACED_HEAD)
    out = [f"<p class='note'>{cell(unplaced_line(made))}</p>", f"<table><tr>{head}</tr>"]
    for row in made["unplaced"]:
        out.append(f"<tr><td class='id'>{cell(', '.join(row['cited']))}</td>"
                   f"<td>{cell(row['what'])}</td><td>{cell(row['said'])}</td>"
                   f"<td>{cell(row['unresolved'])}</td></tr>")
    out.append("</table>")
    return "".join(out)


def calendar_pane(made: dict) -> str:
    out = [f"<p class='clash'>{cell(one['called'])}</p>" for one in made["conflicts"]]
    out.append(grids(made))
    out.append(missing(made))
    return pane(3, Dashboard.PANES[2], Dashboard.SAYS[2], "".join(out))


def tally(made: dict) -> str:
    counted = ((len(made["pending"]), "pending"), (len(made["flagged"]), "flagged"),
               (len(made["commitments"]), "commitments"), (len(made["conflicts"]), "conflicts"))
    shown = "".join(f"<li><b>{number}</b> {word}</li>" for number, word in counted)
    return f"<ul class='tally'>{shown}</ul>"


def page(made: dict) -> str:
    return (f"<!doctype html>\n<html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{cell(Dashboard.TITLE)}</title>"
            f"<style>{Dashboard.STYLE}</style></head><body><div class='wrap'>\n"
            f"<h1>{cell(Dashboard.TITLE)}</h1>\n"
            f"<p class='sub'>{cell(Dashboard.LEDE)} "
            f"From the run of {cell(made['at'])}.</p>\n"
            f"{tally(made)}\n"
            f"{waiting_pane(made)}\n{flagged_pane(made)}\n{calendar_pane(made)}\n"
            f"<footer>{cell(Dashboard.FOOT)}</footer>\n"
            f"</div></body></html>\n")


def stored() -> dict:
    return json.loads(Paths.DASHBOARD.read_text())
