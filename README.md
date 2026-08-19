# Neurosymbolic AI – lecture

Slides and lab from the three-hour neurosymbolic AI session at Brno University of
Technology, Faculty of Information Technology. Three blocks, two breaks.

**[Slides (PDF)](slides/Neurosymbolic_AI_lecture.pdf)** – the whole argument is in the deck.
The lab below is an optional extension for anyone who wants to feel that argument in code
instead of watching it, so if you never get to it you have not missed the point of the day.

## ➜ [Download the lab (ZIP)](https://github.com/poli-cz/neurosymbolic-ai-lecture/archive/refs/heads/main.zip)

Python 3.9+. No installs, no internet, no API key.

Unzip it, open a terminal **inside the `lab/` folder** and run:

```bash
python3 check_task1.py
python3 check_task2.py
```

The two tasks are described in **[lab/README.md](lab/README.md)**. Read that next.

## What the lab is about

One question: *"Am I eligible for the reduced fare?"* The system that answers it has two
halves. A neural half turns messy free text into typed facts, and a symbolic half turns
those facts into a decision plus the derivation behind it. You write the rules first, then
run them on real sentences. The rules will be perfect and the system will still be wrong
more than half the time. Finding out why is the exercise.

Brno University of Technology, Faculty of Information Technology.
Questions: ipolisensky@fit.vut.cz

## Licence

The code in `lab/` is MIT, see [LICENSE](LICENSE). The slides are shared for educational
use, and the BUT/FIT marks in them are not covered by the MIT licence.
