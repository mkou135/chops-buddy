"""CLI: `python -m evals [--count] [--sample N] [--model M] [--write]`.

Exit codes: 0 ok, 1 regression gate failed, 2 usage, 3 no API key.
"""

import argparse
import asyncio
import os
import sys

from evals.runner import (
    CASES_DIR,
    RESULTS_DIR,
    load_cases,
    regression_gate,
    run,
    summarise,
    write_results,
)


def count_cases() -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in load_cases(CASES_DIR):
        counts[case.category] = counts.get(case.category, 0) + 1
    return dict(sorted(counts.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evals")
    parser.add_argument(
        "--count", action="store_true", help="print case counts per category and exit"
    )
    parser.add_argument("--sample", type=int, default=None, help="run only the first N cases")
    parser.add_argument(
        "--model", default=None, help="model id (default: CB_LLM_MODEL or claude-opus-5)"
    )
    parser.add_argument(
        "--write", action="store_true", help="append a results file (default: print only)"
    )
    args = parser.parse_args(argv)

    if args.count:
        counts = count_cases()
        for category, n in counts.items():
            print(f"{category}: {n}")
        print(f"total: {sum(counts.values())}")
        return 0

    api_key = os.environ.get("CB_LLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("no API key: set CB_LLM_API_KEY or ANTHROPIC_API_KEY", file=sys.stderr)
        return 3

    from chops_buddy.llm.proposer import DEFAULT_MODEL, PROMPT_VERSION, AnthropicProposer

    model = args.model or os.environ.get("CB_LLM_MODEL") or DEFAULT_MODEL
    cases = load_cases(CASES_DIR)
    if args.sample:
        cases = cases[: args.sample]
    results = asyncio.run(
        run(cases, AnthropicProposer(api_key, model), model=model, prompt_sha=PROMPT_VERSION)
    )
    summary = summarise(results)
    print(
        f"model={model} prompt={PROMPT_VERSION} cases={summary['total']} "
        f"pass_rate={summary['pass_rate']:.2%} legality={summary['legality_rate']:.2%} "
        f"repaired={summary['repair_rate']:.2%}"
    )
    for slug in summary["failing"]:
        print(f"  FAIL {slug}")
    ok = regression_gate(RESULTS_DIR, summary["pass_rate"])
    if args.write and not args.sample:
        path = write_results(RESULTS_DIR, results, summary, model=model, prompt_sha=PROMPT_VERSION)
        print(f"wrote {path.relative_to(RESULTS_DIR.parent.parent)}")
    if not ok:
        print("regression gate: pass rate dropped more than 5 points vs last run", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
