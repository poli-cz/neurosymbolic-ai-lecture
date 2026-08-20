# Reference solution

This branch is the answer key for the two lab tasks. It exists so that a student who
got stuck, or who wants to compare, has something to read afterwards.

**It must not be merged into `main`.** `main` is what people download, and the lab only
works if the two functions in it are still empty.

Everything is in two functions. `extract()` is byte-identical to `main`: the naive
baseline has to stay naive, or the scoreboard has nothing to compare against.

```bash
git diff main..solution -- lab/          # the whole solution, both tasks
cd lab && python3 check_task1.py && python3 check_task2.py
```

## Scoreboard

|                 | rules, on gold facts | end to end | confidently wrong | abstained |
|-----------------|---------------------:|-----------:|------------------:|----------:|
| baseline (`main`) | 10/10 | 5/12 | **7** | 0 |
| this branch       | 10/10 | 10/12 | **0** | 2 |

It abstains on four of the twelve. On two of them (`g04`, no age stated anywhere, and
`g05`, a year of birth where an age belongs) abstaining *is* the correct answer, which is
why they count as correct above. The other two are the price paid: `g08` (Czech) and `g10`
(conflicting student signals). The "abstained" line in the checker counts only those two.

One number the checker does not print, and the one that actually matters: on all eight
cases where this branch produces facts at all, those facts are **identical to the gold
facts**.
It is not only the fares that are right, it is the derivations. `g10` and `g12` are in
the input set precisely to reward a solution that gets the right fare from a false fact,
and this one declines the reward.

---

## Task 1 - the reasoner

Three things carry the whole task:

1. **Validation is a gate, not a formality.** It runs before any rule. That is what makes
   `decide()` total: every input, including garbage, reaches a defined outcome instead of
   an exception.
2. **The order of the four blocks is the policy.** Swap R1 and R2 and a 14-year-old with a
   card silently becomes a student fare. The code still runs. Only the tests notice.
3. **R4 read no fact, so its derivation is empty**, and `R0-invalid-input` is an outcome
   rather than an error. Both of those are refusals to improvise.

The `student` flag means "holds a valid student card", not "is enrolled". The rule reads
the flag and nothing else. Keeping that distinction true is task 2's job, and `g06` is
where it gets tested.

### The question: two properties a pure function gives you for free

**Determinism.** Same facts in, same decision out, today and after the next deploy. A case
that passes now passes forever, a bug is reproducible from its inputs alone, and nothing
about the answer depends on a sampling temperature or on which model version answered.

**Totality with a checkable derivation.** Every input reaches a defined outcome, and the
outcome carries the list of facts the firing rule actually read. You can audit the
reasoning without re-running it and without trusting the thing that produced it.

There is a third one, cheap and worth showing on a slide. The valid input domain is
121 ages x 2 booleans = **242 points**. You can enumerate every one of them in a
millisecond, and confirm the policy partitions the domain exactly:

```
R1 30    R2 11    R3 112    R4-fallback 89          (30 + 11 + 112 + 89 = 242)
```

That is not a test set sampled from a distribution. It is the entire domain, proved by
exhaustion. It is also a sentence nobody can say about an end-to-end model.

---

## Task 2a - the confidently wrong one

```
g02  "I have 2 kids travelling with me and I'm 34."
     -> facts {"age": 2, "student": false}
     -> "You qualify for the child fare. (decided by R1 using: age)"
```

Complete, plausible, fully traceable, and wrong. In one sentence:

> **The trace is faithful to the facts, and the fault is in the facts, so the derivation
> certifies the wrong thing: that the conclusion follows from what the reasoner was told,
> never that what it was told was true of the passenger.**

The audit trail audits the reasoning, not the world. `g03` and `g06` are the same defect in
different clothes, and `g06` is the sharpest of the three: "still studying, but my card
expired" is enrolment without a card, so the lie is hiding in the schema's fine print.

---

## Task 2b - the grounding

Four gates, in this order. The order matters as much as it did in task 1.

| gate | question | catches |
|------|----------|---------|
| 0. competence | is this text something the extractor can read at all? | `g08` |
| 1. coverage | did the extractor see a value, or invent one? | `g04` |
| 2. schema | is the value possible? (`validate`, the loud failures) | `g05` |
| 3. confidence | is the value more than a guess? (the quiet failures) | `g10` |

Three decisions inside that are worth defending out loud:

**The closed-world assumption on `student`.** No student word anywhere is read as
`student = false`, exactly as the baseline does. That is only legitimate because gate 0
already ran: *absence of evidence is evidence of absence precisely when you know your
detector would have fired had the thing been true.* `g08` is the counter-example that
forces gate 0 to exist and to come first. The Czech sentence says the person studies, the
detector has no Czech, and its silence therefore means nothing at all. Take gate 0 out and
this assumption turns into a fabrication that the reasoner cannot see and the trace will
happily certify.

**Anchoring instead of "the first number".** `DEFAULT_AGE = 30` gets all the attention, but
`numbers[0]` is the more expensive line: it is `g02` and `g11`. The fix is not a better
number regex, it is requiring that some phrase *binds* the number to an age
("I'm 34", "Age: 24", "14 years old"). Two candidates and no binding is not a hard case,
it is a case with no answer, and the honest output for it is nothing.

**Buy coverage with competence, not with a lower threshold.** `g09` spells its age out.
Number words are a closed class, so covering them is thirty lines and no risk, and it wins
the case outright. Compare that with the other way of getting a point back, below.

### The knob

`CONFIDENCE_THRESHOLD` is the one place where "answer or abstain" is decided. Every reader
returns its best value *and* a confidence, so the trade is visible in a single sweep:

| threshold | fares correct | confidently wrong | abstained | facts equal to gold |
|-----------|---------------|-------------------|-----------|---------------------|
| 0.25 | 11/12 | 0 | 1 | 10 |
| **0.70 (shipped)** | **10/12** | **0** | **2** | **10** |
| 0.80 | 7/12 | 0 | 5 | 7 |
| 0.90 | 6/12 | 0 | 6 | 6 |

Read the top row carefully, because it is the trap. Dropping to 0.25 makes the scoreboard
*better*: one more correct fare, still nothing wrong. The extra point is `g10`, where the
system decides `student = true` about a 70-year-old lecturer and gets "senior" anyway,
because R2 cannot fire at that age. Right fare, false fact, and a trace that reads like an
explanation while being a lie. The fare-level scoreboard cannot see the difference. The
fact-level column can, and it does not move.

Above 0.75 the closed-world assumption on `student` stops clearing the bar and `g02`,
`g07` and `g11` fall out with it. That is the cost of refusing to default at all.

---

## Task 2c - is the system trustworthy now?

No. Safer is not trustworthy, and none of the following has been measured:

- **Held-out data, from the actual stations.** These twelve sentences were written to make
  a point, and the patterns above were then tuned against them. That is not evidence, it
  is a circle. The number I would want is the abstention and error rate on real passenger
  utterances nobody tuned on, in the languages and phrasings that actually turn up.
- **The `g10` class specifically: right fare, wrong facts.** Invisible to every fare-level
  metric. Measuring it needs human-labelled facts, not just labelled decisions.
- **Error asymmetry.** Overcharging a 14-year-old and undercharging a 30-year-old are one
  number on this scoreboard and two very different things in the world. Weight them, then
  set the threshold from the weights instead of from a sweep table.
- **The cost of abstention, on whoever absorbs it.** Two in twelve is a staffing question at
  the counter, and staff who are swamped start waving people through, which quietly turns
  the abstention rate back into an error rate.
- **Drift.** Passengers change, phones autocorrect, the fare policy changes. The rules change
  in one commit with a test that proves the new partition. The grounding does not, and that
  asymmetry is the argument for the split in the first place.
- **Calibration.** The confidences here are ordered, not calibrated. 0.9 does not mean nine
  times out of ten. Ordering needs an argument, calibration needs labelled data.

---

## What this solution deliberately does not do

- **It does not generalise.** The patterns were written against twelve sentences and will
  not survive the thirteenth. What transfers is the structure: a competence check before
  any default, an explicit confidence per field, the minimum and not the average handed to
  the pipeline, and abstain as a first-class outcome. Not the regexes.
- **`_looks_like_english` is a word-ratio heuristic.** It would call a short English SMS
  foreign and a long Czech sentence English. Real systems use a language identifier and
  treat its score as one more confidence.
- **It does not exploit relevance.** A grounding layer that knew R2 cannot fire above 25
  would notice that `student` is irrelevant when age is 70, and would answer `g10` instead
  of abstaining. That is a real technique, and it couples the two halves that this lab
  spent three hours separating, so it is left out on purpose. It is a good question for the
  room.
- **It does not touch `extract()`.** Every improvement lives in `ground()`, so the diff
  between naive and careful is readable in one place.
