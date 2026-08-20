"""
TASK 2 - the neural half.  *** REFERENCE SOLUTION (branch `solution`) ***

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
# SOLUTION - the machinery ground() needs in order to know when to shut up.
# `extract()` above is untouched: the baseline has to stay the baseline, so
# everything new lives down here.
# ---------------------------------------------------------------------------

# One knob. Every reader below returns its best value AND a confidence in
# [0, 1]; under this line the value is a guess and the system says nothing.
# Raise it and the abstention rate climbs. Lower it and the system starts
# answering from guesses - and on these twelve inputs that briefly looks like
# an improvement, which is the trap: the point you win back at 0.25 is g10,
# where the fare is right and the fact behind it is false. The scoreboard
# cannot tell those apart. You can, by diffing facts against gold.
CONFIDENCE_THRESHOLD = 0.70

# The vocabulary this extractor was actually built on. It exists to answer a
# question the baseline never asks: can I read this text at all?
ENGLISH_CUES = {
    "i", "im", "me", "my", "am", "is", "are", "was", "were", "a", "an", "the",
    "and", "but", "or", "not", "no", "dont", "have", "has", "had", "still",
    "year", "years", "old", "in", "on", "of", "to", "at", "with", "from",
    "today", "tomorrow", "last", "next", "any", "more", "so", "travelling",
    "traveling", "card", "student", "age", "aged", "kids",
}

# A number that some phrase actually binds to an age. The baseline takes the
# first number in the string, and that one line is two of its seven wrong
# answers (g02, g11) - exactly the same score as the notorious DEFAULT_AGE.
AGE_ANCHORS = (
    r"\bages?\s*[:=]?\s*(\d{1,3})\b",
    r"\baged\s+(\d{1,3})\b",
    r"\bi\s*'?\s*m\s+(?:only\s+|just\s+|still\s+|now\s+)?(\d{1,3})\b",
    r"\bi\s+am\s+(?:only\s+|just\s+|still\s+|now\s+)?(\d{1,3})\b",
    r"\b(\d{1,3})\s*(?:years?|yrs?)\s*old\b",
    r"\b(\d{1,3})\s*y\.?o\.?\b",
)

# The schema says the discount needs the CARD, not the enrolment, so the card
# is what these patterns are about.
STUDENT_NEGATED = (
    r"\bnot\s+(?:a\s+)?(?:full[-\s]?time\s+)?student\b",
    r"\bno\s+longer\s+(?:a\s+)?student\b",
    r"\bex[-\s]?student\b",
    r"\bnever\s+(?:was|been)\b",
    r"\b(?:finished|graduated|dropped\s+out|stopped\s+studying)\b",
)
CARD_INVALID = (
    r"\bcard\s+(?:has\s+)?expired\b",
    r"\bexpired\s+(?:student\s+)?card\b",
    r"\bcard\s+(?:is\s+)?(?:at\s+home|invalid|out\s+of\s+date)\b",
    r"\b(?:don'?t|do\s+not|didn'?t)\s+have\s+(?:my|a|the)\s+card\b",
    r"\bwithout\s+(?:my|a|the)\s+card\b",
)
CARD_PRESENT = (
    r"\b(?:valid\s+)?student\s+card\b",
    r"\bcard\s+in\s+my\s+(?:wallet|bag|pocket|purse)\b",
    r"\bhave\s+my\s+(?:student\s+)?card\b",
)
# Being near a university is not being enrolled at one.
ROLE_CONFLICT = (
    r"\bi\s+(?:still\s+)?teach\b",
    r"\bi\s+(?:still\s+)?lecture\b",
    r"\b(?:professor|lecturer|faculty\s+member)\b",
    r"\bi\s+work\s+(?:at|for)\b",
    r"\b(?:retired|pensioner)\b",
)

_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}


def _word_numbers(lowered: str) -> list[int]:
    """Ages written out in words. Number words are a closed class, so this is
    cheap to cover properly - and the honest way to cut the abstention rate is
    to make the extractor competent, never to lower the threshold."""
    tokens = re.findall(r"[a-z]+", lowered)
    values: list[int] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in _TENS:
            value = _TENS[token]
            if i + 1 < len(tokens) and 1 <= _ONES.get(tokens[i + 1], 0) <= 9:
                value += _ONES[tokens[i + 1]]
                i += 1
            values.append(value)
        elif token in _ONES:
            values.append(_ONES[token])
        i += 1
    return values


def _looks_like_english(text: str) -> bool:
    """Gate 0. Crude on purpose - a real system calls a language identifier -
    but the point it makes is not crude: every heuristic below assumes the
    extractor can read the text, and none of them fails loudly when it cannot.
    """
    words = re.findall(r"[a-z]+", text.lower())
    if len(words) < 5:
        return True  # too short to judge; the later gates still have to hold
    return sum(w in ENGLISH_CUES for w in words) / len(words) >= 0.20


def _read_age(text: str, facts: dict, evidence: dict) -> tuple[int | None, float, str]:
    """Return (best value or None, confidence, why).

    A low confidence still comes with a value. That is deliberate: it keeps
    the threshold the one place where "answer or abstain" is decided, instead
    of scattering that decision across the readers.
    """
    lowered = text.lower()

    if evidence["age"] is None:
        # The baseline matched nothing and fell back on DEFAULT_AGE. An
        # invented value is not a weak value, it is no value - so this is the
        # one branch that really does return None. Before giving up, though:
        # the age may simply be spelled out.
        words = sorted(set(_word_numbers(lowered)))
        if len(words) == 1:
            return words[0], 0.80, f"no digits, but the age is written out: {words[0]}"
        if words:
            return words[0], 0.30, f"number words with nothing to choose between: {words}"
        return None, 0.00, "no age in the text at all; the baseline supplied DEFAULT_AGE"

    anchored = sorted({int(m) for p in AGE_ANCHORS for m in re.findall(p, lowered)})
    if len(anchored) == 1:
        return anchored[0], 0.95, f"a phrase binds {anchored[0]} to an age"
    if len(anchored) > 1:
        return anchored[0], 0.30, f"more than one number claims to be the age: {anchored}"

    digits = sorted({int(n) for n in re.findall(r"\d+", text)})
    if len(digits) == 1:
        # Unanchored, so weaker: this is only the absence of a competitor.
        return digits[0], 0.75, f"a single number, {digits[0]}, and nothing competing for the slot"
    # Several numbers and not one of them tied to an age. facts["age"] is the
    # baseline's answer here - the first number in the string - kept so the
    # threshold can reject it rather than the reader hiding it.
    return facts["age"], 0.30, f"{len(digits)} numbers, none of them bound to an age: {digits}"


def _read_student(text: str) -> tuple[bool, float, str]:
    """Return (student, confidence, why).

    Unlike the age reader this one always has a value: there is always a
    reading, and a bare guess is returned labelled as one for the threshold
    to throw out.
    """
    lowered = text.lower()

    def fired(patterns) -> bool:
        return any(re.search(p, lowered) for p in patterns)

    if fired(STUDENT_NEGATED):
        return False, 0.95, "the student claim is explicitly withdrawn"
    if fired(CARD_INVALID):
        return False, 0.95, "enrolment perhaps, but not the valid card the schema asks for"

    if any(t in lowered for t in STUDENT_TOKENS):
        if fired(CARD_PRESENT):
            return True, 0.90, "a student claim backed by a card"
        if fired(ROLE_CONFLICT):
            return True, 0.25, "student words and a not-a-student role in the same sentence"
        return True, 0.50, "studies, but says nothing about the card the schema requires"

    # No student word anywhere. The baseline reads that as False, and here it
    # is allowed to - but only because gate 0 established that the text is
    # readable. Absence of evidence is evidence of absence exactly when you
    # know your detector would have fired had the thing been true. That is the
    # entire justification, and it is why the Czech sentence has to be stopped
    # at gate 0 and not here.
    return False, 0.75, "no student claim in text this extractor can read"


def explain(text: str) -> dict:
    """Same decision as ground(), with the reasoning kept. Useful at the front
    of a room; ground() itself returns facts or nothing, as the contract says."""
    facts, evidence = extract(text)
    if not _looks_like_english(text):
        return {"facts": None, "age": None, "student": None,
                "why": "gate 0: this is not a language the extractor was built for"}
    age, age_conf, age_why = _read_age(text, facts, evidence)
    student, student_conf, student_why = _read_student(text)
    return {
        "facts": ground(text),
        "age": (age, age_conf, age_why),
        "student": (student, student_conf, student_why),
    }


# ---------------------------------------------------------------------------
# TASK 2: implement this.
# ---------------------------------------------------------------------------
def ground(text: str, threshold: float = CONFIDENCE_THRESHOLD) -> dict | None:
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
    # ---- reference solution -----------------------------------------------
    facts, evidence = extract(text)

    # Gate 0 - competence. Everything after this line assumes the extractor
    # can read the text. When it cannot, its silence means nothing, and a
    # default read off that silence is not a default, it is a fabrication.
    if not _looks_like_english(text):
        return None

    age, age_confidence, _ = _read_age(text, facts, evidence)
    student, student_confidence, _ = _read_student(text)

    # Gate 1 - coverage. A field with no value at all stays unread. No priors,
    # no "sensible value for an adult passenger". Only age can fail here: the
    # student reader always has a reading, and gate 3 is what throws out the
    # ones that are only a guess.
    if age is None:
        return None

    candidate = {"age": age, "student": student}

    # Gate 2 - the schema. The loud failures: impossible types, impossible
    # ranges, fields nobody declared. Free, and it costs one line.
    if validate(candidate):
        return None

    # Gate 3 - confidence. The quiet failures, the ones nothing flags. A set
    # of facts is only as trustworthy as its weakest field, so the pipeline
    # gets the minimum and not an average that would hide it.
    if min(age_confidence, student_confidence) < threshold:
        return None

    return candidate
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
