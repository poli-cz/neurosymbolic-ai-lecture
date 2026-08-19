"""
TASK 2 - the neural half.

In a real system `extract()` is a language model with a structured-output constraint.
Here it is thirty lines of regex, so that the lab runs offline in under a second.
Substituting an LLM would change the error *rate*. It would not change the error *kind*,
and the error kind is what this task is about.

You implement `ground()`. Run `python3 check_task2.py` to grade yourself.
"""

from __future__ import annotations

import re

from task1_rules import validate

# ---------------------------------------------------------------------------
# PROVIDED - the naive extractor. Read it carefully. Do not fix it in place;
# `check_task2.py` compares your ground() against this baseline.
# ---------------------------------------------------------------------------

DEFAULT_AGE = 30  # "a sensible prior for an adult passenger". This line is the whole lesson.

STUDENT_TOKENS = ("student", "studying", "study", "university", "college")


def extract(text: str) -> tuple[dict, dict]:
    """
    Turn free text into candidate facts.

    Returns (facts, evidence).

    `evidence` records, for every field, what the extractor actually saw -
    or None when it had to invent the value. You will need it.
    """
    facts: dict = {}
    evidence: dict = {}

    # --- age: take the first number that appears ---------------------------
    numbers = re.findall(r"\d+", text)
    if numbers:
        facts["age"] = int(numbers[0])
        evidence["age"] = f"matched the token {numbers[0]!r}"
        if len(numbers) > 1:
            evidence["age"] += f" (but {len(numbers)} numbers were present: {numbers})"
    else:
        facts["age"] = DEFAULT_AGE
        evidence["age"] = None  # no evidence at all. It made this up.

    # --- student: does any student-ish word occur anywhere? ----------------
    hit = next((t for t in STUDENT_TOKENS if t in text.lower()), None)
    facts["student"] = hit is not None
    evidence["student"] = f"matched the token {hit!r}" if hit else None

    return facts, evidence


# ---------------------------------------------------------------------------
# TASK 2: implement this.
# ---------------------------------------------------------------------------
def ground(text: str) -> dict | None:
    """
    Return typed facts that are safe to hand to the reasoner, or None to abstain.

    You have three tools, and you need all three:

      1. SCHEMA VALIDATION. `validate(facts)` is imported above and returns a list
         of violations. Anything it flags is a LOUD failure - the value is
         impossible, so you know it is wrong. Refuse it.

      2. EVIDENCE. `evidence[field] is None` means the extractor produced that
         value out of thin air. An invented fact carries no information, and the
         reasoner cannot tell the difference between an invented fact and an
         observed one. That is exactly why it must not receive it.

      3. AMBIGUITY. Some text is well-formed and still not safely readable:
         several numbers where one age was expected, a negated student claim
         ("not a student any more"), an expired card, a language your extractor
         was never built for. These are QUIET failures. Nothing flags them.
         You have to decide what your extractor is entitled to be confident about.

    Guidance, not a spec - the design decision is yours:

        facts, evidence = extract(text)
        # ... build a confidence in [0, 1] from the evidence and the text ...
        # ... run validate(facts) ...
        # return facts if you are confident and it validates, else None

    Target: ZERO confidently-wrong answers, at the lowest abstention rate you
    can manage. Abstaining on everything scores zero wrong answers and is worth
    nothing. Both numbers are printed. Optimise the pair, not one of them.
    """
    # ---- your code below --------------------------------------------------
    facts, evidence = extract(text)
    return facts  # <- the naive baseline: trusts everything. Replace this.
    # -----------------------------------------------------------------------


# ---------------------------------------------------------------------------
# PROVIDED - the full pipeline, wired end to end.
# ---------------------------------------------------------------------------
def pipeline(text: str) -> dict:
    """free text -> grounding -> rules -> decision + trace"""
    from task1_rules import decide

    facts = ground(text)
    if facts is None:
        return {
            "fare": "abstain",
            "rule": "G0-low-confidence",
            "facts_used": [],
            "reason": "grounding declined to produce facts",
        }
    return decide(facts)


if __name__ == "__main__":
    for t in ("I have 2 kids and I'm 34.", "I'm not a student any more. Age 24."):
        print(f"{t!r}\n  extract -> {extract(t)[0]}\n  pipeline -> {pipeline(t)}\n")
