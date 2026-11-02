"""Typing practice logic: speed, accuracy, weak keys and lessons that adapt.

Bangla text must be counted in grapheme clusters, not code points. The word "ক্ষ" is three
code points but one written unit, so speed in code points would flatter Bangla typists.
"""
import random
import unicodedata
from collections import Counter

VIRAMA = "্"
COMMON_EN = """the of and to in is you that it he was for on are as with his they at be this have from or one had by word but not what all were we when your can said there use an each which she do how their if will up other about out many then them these so some her would make like him into time has look two more write go see number no way could people my than first water been call who oil its now find long down day did get come made may part""".split()
COMMON_BN = """আমি তুমি সে আমরা তোমরা তারা এই সেই কী কেন কখন কোথায় কেমন ভালো মন্দ বড় ছোট নতুন পুরনো মানুষ দেশ ভাষা বাংলা স্কুল বই খাতা কলম শিক্ষক ছাত্র পড়া লেখা খেলা কাজ বাড়ি পানি ভাত মাছ দিন রাত সকাল বিকাল আজ কাল মা বাবা ভাই বোন বন্ধু কম্পিউটার ইন্টারনেট""".split()


def graphemes(text):
    """Split text into written units. Combining marks join their base, and a virama joins the next consonant."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        unit = text[i]
        i += 1
        while i < n:
            c = text[i]
            if unicodedata.category(c) in ("Mn", "Mc") or c in ("‌", "‍"):
                unit += c
                i += 1
                if c == VIRAMA and i < n and unicodedata.category(text[i]) == "Lo":
                    unit += text[i]
                    i += 1
            else:
                break
        out.append(unit)
    return out


def align(target, typed):
    """Compare typed text with the target by edit distance. Returns (right, errors by expected unit, typed units)."""
    a, b = graphemes(target), graphemes(typed)
    n, m = len(a), len(b)
    if n * m > 4_000_000:
        raise ValueError("text is too long to compare")
    prev = list(range(m + 1))
    table = [prev]
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cur[j] = min(prev[j - 1] + (a[i - 1] != b[j - 1]), prev[j] + 1, cur[j - 1] + 1)
        table.append(cur)
        prev = cur
    i, j, right = n, m, 0
    errors = Counter()
    while i > 0 or j > 0:
        if i > 0 and j > 0 and table[i][j] == table[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            if a[i - 1] == b[j - 1]:
                right += 1
            else:
                errors[a[i - 1]] += 1
            i, j = i - 1, j - 1
        elif i > 0 and table[i][j] == table[i - 1][j] + 1:
            errors[a[i - 1]] += 1
            i -= 1
        else:
            j -= 1
    return right, errors, m


def score(target, typed, seconds):
    """Words per minute use the standard word of five units. Net speed subtracts errors."""
    if seconds <= 0:
        raise ValueError("time must be above zero")
    right, errors, count = align(target, typed)
    minutes = seconds / 60
    return {"gross_wpm": count / 5 / minutes, "net_wpm": right / 5 / minutes, "accuracy": right / count if count else 0.0, "errors": errors, "typed": count, "correct": right}


def weak_keys(attempts, seen, minimum=3, limit=8):
    """Units with the highest error rate. attempts: Counter of errors. seen: Counter of times shown."""
    rates = [(attempts[k] / seen[k], k) for k in attempts if seen.get(k, 0) >= minimum and k.strip()]
    return [k for _, k in sorted(rates, key=lambda t: (-t[0], t[1]))[:limit]]


def lesson(language="en", weak=(), words=20, seed=0):
    """Build a practice line that favours words with your weak keys."""
    rng = random.Random(seed)
    bank = COMMON_BN if language == "bn" else COMMON_EN
    if not weak:
        return " ".join(rng.choice(bank) for _ in range(words))
    scored = [(sum(u in weak for u in graphemes(w)), w) for w in bank]
    good = [w for s, w in scored if s > 0]
    out = []
    for i in range(words):
        out.append(rng.choice(good) if good and rng.random() < 0.7 else rng.choice(bank))
    return " ".join(out)


def level(net_wpm, accuracy):
    if accuracy < 0.85:
        return "Slow down: accuracy first"
    for cut, name in ((60, "Expert"), (40, "Strong"), (25, "Steady"), (12, "Growing")):
        if net_wpm >= cut:
            return name
    return "Beginner"
