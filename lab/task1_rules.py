"""
TASK 1 - the symbolic half.

You implement `decide()`. It is a pure function: same facts in, same decision out,
every time, with no model, no sampling and no network call.

Run `python3 check_task1.py` to grade yourself.
"""

from __future__ import annotations

import json
import os

SCHEMA = json.load(open(os.path.join(os.path.dirname(__file__), "schema.json")))
PROPS = SCHEMA["properties"]


# --------------------------------------------------------------------------
# Provided: a minimal schema validator. You do not need to change this.
# --------------------------------------------------------------------------
def validate(facts: dict) -> list[str]:
    """Return a list of violations. Empty list means the facts are well-formed."""
    problems: list[str] = []

    if not isinstance(facts, dict):
        return ["facts is not an object"]

    for name in SCHEMA["required"]:
        if name not in facts or facts[name] is None:
            problems.append(f"missing required fact: {name}")

    for name, value in facts.items():
        spec = PROPS.get(name)
        if spec is None:
            problems.append(f"unknown fact not in schema: {name}")
            continue
        if spec["type"] == "integer":
            # bool is a subclass of int in Python - a classic silent type bug.
            if isinstance(value, bool) or not isinstance(value, int):
                problems.append(f"{name} must be an integer, got {type(value).__name__}")
                continue
            if "minimum" in spec and value < spec["minimum"]:
                problems.append(f"{name}={value} below minimum {spec['minimum']}")
            if "maximum" in spec and value > spec["maximum"]:
                problems.append(f"{name}={value} above maximum {spec['maximum']}")
        elif spec["type"] == "boolean":
            if not isinstance(value, bool):
                problems.append(f"{name} must be a boolean, got {type(value).__name__}")

    return problems


# --------------------------------------------------------------------------
# TASK 1: implement this.
# --------------------------------------------------------------------------
def decide(facts: dict) -> dict:
    """
    Apply the fare policy to a set of typed facts.

    Policy, in order - FIRST MATCH WINS:
        R1  age < 15                    -> "child"
        R2  student is true AND age<26  -> "student"
        R3  age >= 65                   -> "senior"
        R4  otherwise                   -> "full"          (the defined fallback)

    Before any rule fires, the facts must validate. If they do not, the system
    does NOT improvise - it abstains:
        R0  invalid or missing facts    -> "abstain"

    Return a dict matching $defs.Decision in schema.json:
        {
          "fare":       one of child | student | senior | full | abstain,
          "rule":       "R1" | "R2" | "R3" | "R4-fallback" | "R0-invalid-input",
          "facts_used": the names of the facts the firing rule actually read,
          "reason":     optional string
        }

    Notes that the tests care about:
      * facts_used is the derivation. R2 reads TWO facts. R4 reads none.
      * On abstain, put the validator's complaints in "reason".
      * Do not raise. A reasoner that crashes on bad input has no fallback.
    """
    # ---- your code below -------------------------------------------------
    raise NotImplementedError("implement decide()")
    # ----------------------------------------------------------------------


# --------------------------------------------------------------------------
# Provided: the rendering step. Neural in a real system, a template here.
# The point is that it reads the decision and cannot change it.
# --------------------------------------------------------------------------
FARE_TEXT = {
    "child": "You qualify for the child fare.",
    "student": "You qualify for the student fare.",
    "senior": "You qualify for the senior fare.",
    "full": "You pay the full fare.",
    "abstain": "We could not determine your fare automatically. Please see a member of staff.",
}


def render(decision: dict) -> str:
    body = FARE_TEXT[decision["fare"]]
    if decision["fare"] == "abstain":
        return body
    return f"{body} (decided by {decision['rule']} using: {', '.join(decision['facts_used']) or 'no facts'})"


if __name__ == "__main__":
    for f in ({"age": 19, "student": True}, {"age": 70, "student": False}, {"age": 300, "student": False}):
        print(f, "->", decide(f))
