"""Regenerate the eval results table in the root README from evals/results/ (DoD A8).

Never hand-edit the table; run `python evals/report.py`.
"""

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
README = Path(__file__).resolve().parents[2] / "README.md"
START, END = "<!-- evals:start -->", "<!-- evals:end -->"


def table() -> str:
    files = sorted(RESULTS_DIR.glob("*.json"))
    if not files:
        return "No runs yet."
    rows = [
        "| Run | Model | Prompt | Pass | Legal | Repaired | Weakest category | Failing cases |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f in files:
        d = json.loads(f.read_text())
        s = d["summary"]
        weakest = (
            min(s["by_category"].items(), key=lambda kv: kv[1]["pass_rate"])
            if s["by_category"]
            else ("-", {"pass_rate": 0})
        )
        failing = ", ".join(s["failing"][:6]) + (" …" if len(s["failing"]) > 6 else "")
        rows.append(
            f"| {d['run_at'][:10]} | {d['model']} | `{d['prompt_sha']}` "
            f"| {s['pass_rate']:.0%} ({s['passed']}/{s['total']}) "
            f"| {s['legality_rate']:.0%} | {s['repair_rate']:.0%} "
            f"| {weakest[0]} ({weakest[1]['pass_rate']:.0%}) | {failing or '-'} |"
        )
    return "\n".join(rows)


def main() -> None:
    text = README.read_text()
    if START not in text:
        raise SystemExit(f"{README} has no {START} marker")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    README.write_text(f"{before}{START}\n{table()}\n{END}{after}")
    print(f"updated {README}")


if __name__ == "__main__":
    main()
