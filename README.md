# Typing Lab

An offline typing tutor for computer classes, in English and Bangla. Each lesson leans on the keys a learner gets wrong, and the teacher sees the whole class on one page.

```
python -m typing_lab
```

Then open http://127.0.0.1:8027. It needs Python 3.10 or newer. On a lab network, each computer can run its own copy.

## What it does

- **Adaptive lessons:** after a few attempts, 70% of the words contain the learner's weakest keys
- **Fair measures:** words per minute with the standard word of five units, net speed that counts only correct units, and accuracy
- **Forgiving comparison:** typed text is aligned with the target, so one missed letter does not mark everything after it as wrong
- **Class report:** best speed and accuracy for each learner, with a speed chart and weak keys for each one

## Bangla done properly

A Bangla word is not a list of Unicode code points. "ক্ষ" is three code points but one written unit, and "পানি" is two units. Typing Lab counts grapheme clusters, so speed and accuracy mean the same in both languages, and errors point at the unit a learner sees.

Typing Bangla needs a keyboard layout such as Avro or Bijoy installed on the computer. This tool does not include one.

## How it is tested

Grapheme splitting, scoring and alignment are tested on English and Bangla, including conjuncts and vowel signs. App tests run the flow from practice to report. The browser timing script itself has not been tested automatically.

## Limits

A teacher could time learners more strictly, because the timer is in the browser and can be tampered with. It is a practice tool, not an exam. Each computer keeps its own file unless one is shared. The word lists are short.

## Tests

```
python -m unittest discover -s tests
```

MIT licence.
