"""Grade Task 1.  Usage:  python3 check_task1.py"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from task1_rules import decide
except Exception as exc:  # noqa: BLE001
    print(f"could not import task1_rules.decide: {exc}")
    sys.exit(1)

VALID_FARES = {"child", "student", "senior", "full", "abstain"}


def main() -> int:
    cases = json.load(open(os.path.join(HERE, "task1_cases.json")))
    passed, failures = 0, []

    for case in cases:
        want = case["expect"]
        try:
            got = decide(case["facts"])
        except NotImplementedError:
            print("decide() is not implemented yet. Open task1_rules.py.")
            return 1
        except Exception as exc:  # noqa: BLE001
            failures.append((case, f"raised {type(exc).__name__}: {exc}"))
            continue

        problems = []
        if not isinstance(got, dict):
            problems.append(f"returned {type(got).__name__}, expected dict")
        else:
            if got.get("fare") not in VALID_FARES:
                problems.append(f"fare={got.get('fare')!r} is not one of {sorted(VALID_FARES)}")
            elif got["fare"] != want["fare"]:
                problems.append(f"fare: expected {want['fare']!r}, got {got['fare']!r}")
            if got.get("rule") != want["rule"]:
                problems.append(f"rule: expected {want['rule']!r}, got {got.get('rule')!r}")
            used = got.get("facts_used")
            if not isinstance(used, list):
                problems.append("facts_used missing or not a list - that list is your derivation")
            elif set(used) != set(want["facts_used"]):
                problems.append(
                    f"facts_used: expected {sorted(want['facts_used'])}, got {sorted(map(str, used))}"
                )

        if problems:
            failures.append((case, "; ".join(problems)))
        else:
            passed += 1

    print(f"\nTASK 1  —  {passed}/{len(cases)} cases pass\n")
    for case, why in failures:
        print(f"  FAIL {case['id']}  {case['note']}")
        print(f"       facts: {json.dumps(case['facts'])}")
        print(f"       {why}\n")

    if not failures:
        print("  All cases pass. Your reasoner is total: every input reaches a defined outcome.\n")
        print("  Before Task 2, answer this: your decide() is a pure function.")
        print("  Name two properties you get for free that an end-to-end model cannot give you.\n")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
