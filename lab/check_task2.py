"""Grade Task 2.  Usage:  python3 check_task2.py"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from task1_rules import decide
    from task2_grounding import extract, pipeline
except Exception as exc:  # noqa: BLE001
    print(f"import failed: {exc}")
    sys.exit(1)


def load():
    with open(os.path.join(HERE, "task2_inputs.jsonl"), encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> int:
    cases = load()

    # --- half 1: are the RULES correct, given perfect facts? ---------------
    rule_ok = 0
    rule_total = 0
    for c in cases:
        if c["gold_facts"] is None:
            continue
        rule_total += 1
        try:
            if decide(c["gold_facts"])["fare"] == c["gold_fare"]:
                rule_ok += 1
        except NotImplementedError:
            print("Finish Task 1 first - decide() is not implemented.")
            return 1

    # --- half 2: what does the WHOLE PIPELINE do on real text? -------------
    correct, abstained, wrong = [], [], []
    for c in cases:
        got = pipeline(c["text"])["fare"]
        if got == "abstain":
            (correct if c["gold_fare"] == "abstain" else abstained).append(c)
        elif got == c["gold_fare"]:
            correct.append(c)
        else:
            wrong.append((c, got))

    n = len(cases)
    print("\n" + "=" * 66)
    print("TASK 2  —  scoreboard")
    print("=" * 66)
    print(f"  rules, given GOLD facts        {rule_ok}/{rule_total}   <- the symbolic half")
    print(f"  end to end, given REAL text    {len(correct)}/{n}   <- the whole system")
    print("-" * 66)
    print(f"  CONFIDENTLY WRONG              {len(wrong):>2}      <- drive this to zero")
    print(f"  abstained                      {len(abstained):>2}      <- then drive this down")
    print("=" * 66)

    if wrong:
        print("\nEvery line below is a wrong fare delivered with a complete, auditable trace:\n")
        for c, got in wrong:
            facts, evidence = extract(c["text"])
            print(f"  {c['id']}  {c['text']}")
            print(f"       extracted : {json.dumps(facts, ensure_ascii=False)}")
            print(f"       evidence  : age={evidence['age']}, student={evidence['student']}")
            print(f"       gold      : {json.dumps(c['gold_facts'], ensure_ascii=False)}")
            print(f"       fare      : said {got!r}, should be {c['gold_fare']!r}")
            print(f"       why       : {c['note']}\n")

    if abstained:
        print("Abstained where a decision was available (this is the cost you are paying):")
        for c in abstained:
            print(f"  {c['id']}  {c['text']}  (should be {c['gold_fare']!r})")
        print()

    if not wrong:
        print("\n  No confidently-wrong answers. Now: how low can the abstention rate go")
        print("  before one comes back?\n")
        print("  And the question for the room: your extractor is safer. Is the SYSTEM")
        print("  trustworthy? What would you measure, on what data, before a passenger")
        print("  sees this?\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
