"""The offline web app."""
import json
import time
from collections import Counter

from . import core
from .fieldkit import App, Fail, Raw, bar_chart, card, form, h, line_chart, link, redirect, stats, table

SCHEMA = """
CREATE TABLE IF NOT EXISTS learners (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, learner INTEGER NOT NULL REFERENCES learners(id), language TEXT NOT NULL, net REAL NOT NULL, gross REAL NOT NULL, accuracy REAL NOT NULL, errors TEXT NOT NULL, seen TEXT NOT NULL, at REAL NOT NULL);
"""
SCRIPT = """
<script>
let start = null;
const box = document.getElementById('typed'), sec = document.getElementById('ms');
box.addEventListener('input', () => { if (start === null) start = performance.now(); });
document.getElementById('practice').addEventListener('submit', () => { sec.value = ((performance.now() - (start || performance.now())) / 1000).toFixed(2); });
</script>"""


def create_app(db="typing.db"):
    a = App("Typing Lab", db, SCHEMA, [("Class", "/"), ("Add learners", "/learners")])

    def totals(lid):
        errors, seen = Counter(), Counter()
        for r in a.rows("SELECT errors, seen FROM attempts WHERE learner = ? ORDER BY id DESC LIMIT 20", lid):
            errors.update(json.loads(r["errors"]))
            seen.update(json.loads(r["seen"]))
        return errors, seen

    @a.route("/")
    def home(req):
        rows = a.rows("SELECT l.id, l.name, COUNT(t.id) n, MAX(t.net) best, AVG(t.accuracy) acc FROM learners l LEFT JOIN attempts t ON t.learner = l.id GROUP BY l.id ORDER BY best DESC")
        return a.page("Class report", card("Learners", table(rows, [("Learner", lambda r: link(f"/learner/{r['id']}", r["name"])), ("Attempts", "n"), ("Best speed", lambda r: "" if r["best"] is None else f"{r['best']:.1f} wpm"), ("Accuracy", lambda r: "" if r["acc"] is None else f"{r['acc']:.0%}")], "Add learners to begin.")))

    @a.route("/learners", ("GET", "POST"))
    def learners(req):
        if req.method == "POST":
            for n in req.text("names", limit=20000).splitlines():
                if n.strip():
                    a.run("INSERT OR IGNORE INTO learners (name) VALUES (?)", n.strip())
            return redirect("/")
        return a.page("Add learners", card("One name per line", form(a, "/learners", [("names", "Names", "textarea")], "Add")))

    @a.route("/learner/<id>")
    def learner(req, id):
        l = a.row("SELECT * FROM learners WHERE id = ?", id)
        if l is None:
            raise Fail("No such learner", 404)
        rows = a.rows("SELECT * FROM attempts WHERE learner = ? ORDER BY id", id)
        errors, seen = totals(id)
        weak = core.weak_keys(errors, seen)
        last = rows[-1] if rows else None
        body = stats([("Attempts", len(rows)), ("Latest speed", f"{last['net']:.1f} wpm" if last else "n/a"), ("Level", core.level(last["net"], last["accuracy"]) if last else "n/a")])
        body += card("Practise", f'<a class="button" href="/practice/{id}?lang=en">English</a> <a class="button" href="/practice/{id}?lang=bn">বাংলা</a>')
        body += card("Weak keys", bar_chart([(k, round(errors[k] / seen[k] * 100)) for k in weak], unit="%"))
        body += card("Speed over time", line_chart([(i + 1, r["net"]) for i, r in enumerate(rows)]))
        return a.page(l["name"], body)

    @a.route("/practice/<id>")
    def practice(req, id):
        if a.row("SELECT 1 FROM learners WHERE id = ?", id) is None:
            raise Fail("No such learner", 404)
        lang = "bn" if req.get("lang") == "bn" else "en"
        errors, seen = totals(id)
        text = core.lesson(lang, core.weak_keys(errors, seen), 20, a.one("SELECT COUNT(*) FROM attempts WHERE learner = ?", id) or 0)
        body = f'<div class="card"><p style="font-size:20px">{h(text)}</p><form id="practice" method="post" action="/practice/{id}">{a.form_token()}<input type="hidden" name="target" value="{h(text)}"><input type="hidden" name="lang" value="{lang}"><input type="hidden" id="ms" name="seconds" value="1"><textarea id="typed" name="typed" rows="4" autofocus></textarea><p><button>Finish</button></p></form></div>{SCRIPT}'
        return a.page("Practice", body)

    @a.route("/practice/<id>", ("POST",))
    def submit(req, id):
        if a.row("SELECT 1 FROM learners WHERE id = ?", id) is None:
            raise Fail("No such learner", 404)
        target = req.text("target", limit=5000)
        typed = req.text("typed", limit=5000)
        s = core.score(target, typed, req.number("seconds", low=0.1, high=86400))
        seen = Counter(core.graphemes(target))
        a.run("INSERT INTO attempts (learner, language, net, gross, accuracy, errors, seen, at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", id, req.get("lang", "en"), s["net_wpm"], s["gross_wpm"], s["accuracy"], json.dumps(s["errors"], ensure_ascii=False), json.dumps(seen, ensure_ascii=False), time.time())
        return redirect(f"/learner/{id}")

    return a
