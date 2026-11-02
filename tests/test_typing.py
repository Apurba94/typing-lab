import unittest
from collections import Counter

from typing_lab import core, create_app
from typing_lab.core import align, graphemes, lesson, level, score, weak_keys


class TestGraphemes(unittest.TestCase):
    def test_english(self):
        self.assertEqual(graphemes("cat"), ["c", "a", "t"])

    def test_bangla_vowel_signs_stay_with_their_consonant(self):
        self.assertEqual(graphemes("পানি"), ["পা", "নি"])

    def test_bangla_conjuncts_are_one_unit(self):
        self.assertEqual(graphemes("ক্ষ"), ["ক্ষ"])
        self.assertEqual(len(graphemes("কম্পিউটার")), len(["ক", "ম্পি", "উ", "টা", "র"]))

    def test_nothing_is_lost(self):
        for t in ("বাংলা ভাষা", "a b", "স্কুলে যাব"):
            self.assertEqual("".join(graphemes(t)), t)


class TestScore(unittest.TestCase):
    def test_perfect_minute(self):
        s = score("a" * 50, "a" * 50, 60)
        self.assertEqual((s["gross_wpm"], s["net_wpm"], s["accuracy"]), (10, 10, 1))

    def test_errors_reduce_net_speed(self):
        s = score("abcde", "abXde", 60)
        self.assertEqual(s["correct"], 4)
        self.assertEqual(s["errors"], Counter({"c": 1}))
        self.assertLess(s["net_wpm"], s["gross_wpm"])

    def test_missing_and_extra_letters(self):
        self.assertEqual(align("abcd", "abd")[1], Counter({"c": 1}))
        self.assertEqual(align("abd", "abcd")[0], 3)

    def test_one_slip_does_not_ruin_the_rest(self):
        self.assertEqual(align("the quick brown fox", "the quik brown fox")[0], 18)

    def test_nothing_typed(self):
        self.assertEqual(score("abc", "", 10)["accuracy"], 0)

    def test_time_must_be_positive(self):
        with self.assertRaises(ValueError):
            score("a", "a", 0)

    def test_bangla_speed_counts_written_units(self):
        self.assertEqual(score("পানি", "পানি", 60)["typed"], 2)


class TestAdapting(unittest.TestCase):
    def test_weak_keys_need_evidence(self):
        self.assertEqual(weak_keys(Counter(a=3, b=1), Counter(a=10, b=2), minimum=3), ["a"])

    def test_order_by_error_rate(self):
        self.assertEqual(weak_keys(Counter(a=2, b=8), Counter(a=10, b=10)), ["b", "a"])

    def test_lessons_favour_weak_keys(self):
        plain = lesson("en", (), 400, 1)
        drilled = lesson("en", ("z", "w"), 400, 1)
        self.assertGreater(drilled.count("w"), plain.count("w") * 1.5)

    def test_bangla_lessons(self):
        self.assertTrue(any("ঀ" <= c <= "৿" for c in lesson("bn", (), 5)))

    def test_lessons_repeat_with_a_seed(self):
        self.assertEqual(lesson("en", (), 10, 3), lesson("en", (), 10, 3))

    def test_levels(self):
        self.assertEqual(level(70, 0.5), "Slow down: accuracy first")
        self.assertEqual(level(70, 0.99), "Expert")
        self.assertEqual(level(5, 0.99), "Beginner")


class TestApp(unittest.TestCase):
    def setUp(self):
        self.a = create_app(":memory:")
        self.a.post("/learners", names="Rahima\nKarim")

    def test_flow(self):
        page = self.a.get("/practice/1?lang=en").body.decode()
        self.assertIn("textarea", page)
        r = self.a.post("/practice/1", target="the cat", typed="the cat", seconds=6, lang="en")
        self.assertEqual(r.status, 303)
        self.assertIn("14.0 wpm", self.a.get("/learner/1").body.decode())
        self.assertIn("14.0 wpm", self.a.get("/").body.decode())

    def test_weak_keys_shape_the_next_lesson(self):
        for _ in range(3):
            self.a.post("/practice/1", target="zzzz aaaa", typed="xxxx aaaa", seconds=9)
        self.assertIn("z", self.a.get("/learner/1").body.decode())

    def test_bangla_is_kept(self):
        self.assertIn("া", self.a.get("/practice/1?lang=bn").body.decode())

    def test_refusals(self):
        self.assertEqual(self.a.post("/practice/1", target="a", typed="a", seconds=0).status, 400)
        self.assertEqual(self.a.post("/practice/9", target="a", typed="a", seconds=1).status, 404)
        self.assertEqual(self.a.get("/learner/9").status, 404)

    def test_names_are_escaped(self):
        self.a.post("/learners", names="<b>x")
        self.assertNotIn("<b>x", self.a.get("/").body.decode())


if __name__ == "__main__":
    unittest.main()
