# Neurosymbolic AI — hands-on lab

Two short tasks. Together about 35 minutes. **Pure Python 3.9+, no installs, no internet, no API key.**

```
neurosymbolic-lab/
├── README.md
├── schema.json           the typed interface — read this first
├── task1_rules.py        TASK 1: you write the reasoner
├── task1_cases.json      the cases your reasoner must get right
├── check_task1.py        run this to grade yourself
├── task2_grounding.py    TASK 2: you fix the grounding layer
├── task2_inputs.jsonl    messy free text + the gold facts
└── check_task2.py        run this to grade yourself
```

Run everything from inside this folder:

```bash
python3 check_task1.py
python3 check_task2.py
```

---

## The scenario

A transport operator wants to answer one question:

> *"Am I eligible for the reduced fare?"*

The system has two halves, and the whole point of the lab is that **they fail differently**.

```
free text  ──▶  GROUNDING  ──▶  typed facts  ──▶  RULES  ──▶  decision + trace
   (task 2)                     (schema.json)      (task 1)
```

---

## Task 1 — Schema first, rules second (~15 min)

Open `schema.json`. It is the contract: which facts exist, their types, their ranges.
Now open `task1_rules.py` and implement `decide(facts)`.

The fare policy, in order — **first match wins**:

| # | Condition | Fare |
|---|-----------|------|
| 1 | `age < 15` | `child` |
| 2 | `student` is true **and** `age < 26` | `student` |
| 3 | `age >= 65` | `senior` |
| 4 | nothing above matched | `full` |

Three things the tests check that most people forget:

1. **A trace.** Return which rule fired and which facts it used. An answer without a derivation is not a symbolic answer.
2. **A fallback.** Rule 4 is not an accident — it is the defined behaviour when nothing matches. Name it.
3. **Refusal on bad input.** If a fact is missing, of the wrong type, or outside the schema's range, `decide` must **not guess**. Return the `abstain` outcome.

> Rule 2 has a trap in it. Read the schema's description of `student` before you write the condition.

Grade yourself:

```bash
python3 check_task1.py
```

**Question to answer before you move on:** your `decide()` is a pure function.
Name two properties you now get for free that an end-to-end neural model cannot give you.

---

## Task 2 — Break the grounding (~20 min)

`task2_grounding.py` contains `extract(text)` — a naive regex extractor that turns a
sentence like *"I'm 19 and I study at Masaryk University"* into `{"age": 19, "student": true}`.
It works. Mostly.

Run it against your rule engine:

```bash
python3 check_task2.py
```

You will see something uncomfortable: the pipeline reports a **high rule accuracy and a
low end-to-end accuracy**. The rules are perfect. The answers are wrong.

### 2a — Find the confidently wrong one

At least one input produces a **wrong fare with a complete, plausible, fully traceable
derivation**. Find it. Write down, in one sentence, why the trace does not help you here.

### 2b — Make it abstain

`extract()` currently returns its best guess for everything. Implement `ground(text)` so that
it returns facts **only when it should**, and otherwise abstains:

- Validate every extracted value against `schema.json` (type, range, allowed values).
- Track a confidence. If the extractor had to guess — no age found, an ambiguous
  student signal, a negation it cannot parse — that is not confidence, that is a guess.
- Below the threshold, return `None`. The pipeline then escalates to a human instead of deciding.

Re-run `check_task2.py`. Your goal is **not** 100% coverage. Your goal is:

> **zero confidently-wrong answers, at the smallest abstention rate you can manage.**

The scoreboard prints both. Trading coverage for correctness is the whole design decision.

### 2c — The question to bring back to the room

Your extractor is now safer. Is the *system* now trustworthy?
What would you have to measure, and on what data, before you would put it in front of a passenger?

---

## What you should be able to say afterwards

- Which part of this system is learned, which part is computed, and what exactly is guaranteed.
- Why a perfectly correct rule engine can still produce a confident, fully auditable wrong answer.
- Why the schema — not the model, and not the rules — is the thing you write first.
