import random
import unittest

from runtime.dice import DiceEngine


class DiceTests(unittest.TestCase):
    def test_seeded_roll_is_reproducible(self):
        a = DiceEngine(random.Random(123)).roll("2d6+2")
        b = DiceEngine(random.Random(123)).roll("2d6+2")
        self.assertEqual(a, b)
        self.assertEqual(a.modifier, 2)
        self.assertEqual(len(a.individual_rolls), 2)

    def test_target_is_structured(self):
        result = DiceEngine(random.Random(1)).roll("1d20", target=10)
        self.assertIsNotNone(result.success)
        self.assertEqual(result.target, 10)
