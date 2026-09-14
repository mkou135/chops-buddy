import argparse
import sys
from pathlib import Path

CASES_DIR = Path(__file__).parent / "cases"


def count_cases() -> dict[str, int]:
    return {
        category.name: len(list(category.glob("*.json")))
        for category in sorted(CASES_DIR.iterdir())
        if category.is_dir()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evals")
    parser.add_argument("--count", action="store_true", help="print case counts per category")
    args = parser.parse_args(argv)
    if args.count:
        counts = count_cases()
        for category, n in counts.items():
            print(f"{category}: {n}")
        print(f"total: {sum(counts.values())}")
        return 0
    print("eval runner not implemented yet (milestone M3)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
