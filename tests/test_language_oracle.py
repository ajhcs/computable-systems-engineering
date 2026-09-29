"""Independent small-trace oracle for optimized temporal evaluation."""

from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.language import _evaluate

TRIGGER = {"name": "trigger", "op": "=", "value": True}
RESPONSE = {"name": "response", "op": "=", "value": True}
RELEASE = {"name": "release", "op": "=", "value": True}


def rows(responses, releases=None):
    return [{"trigger": index == 0,
             **({"response": value} if value is not None else {}),
             **({"release": releases[index]} if releases is not None and releases[index] is not None else {})}
            for index, value in enumerate(responses)]


def within_oracle(responses, deadline):
    observed = responses[:deadline + 1]
    if True in observed:
        return "pass"
    if None in observed or len(responses) <= deadline:
        return "unknown"
    return "fail"


def until_oracle(responses, releases):
    stop = next((index for index in range(1, len(releases)) if releases[index] is True), len(releases))
    pending = stop == len(releases)
    for index in range(stop):
        if responses[index] is False:
            if None in releases[1:index + 1]:
                pending = True
            else:
                return "fail"
        elif responses[index] is None:
            pending = True
    return "unknown" if pending else "pass"


class OracleTests(unittest.TestCase):
    def test_all_short_within_traces(self):
        parsed = {"scope": None, "trigger": TRIGGER, "response": RESPONSE,
                  "condition": "upon", "timing": "within", "deadline_ticks": 2}
        for values in product((False, True, None), repeat=5):
            result = _evaluate(parsed, rows(values))
            self.assertEqual(result["status"], within_oracle(values, 2), values)

    def test_all_short_until_traces(self):
        parsed = {"scope": None, "trigger": TRIGGER, "response": RESPONSE,
                  "condition": "upon", "timing": "until", "release": RELEASE}
        for values in product((False, True, None), repeat=4):
            for releases in product((False, True, None), repeat=4):
                result = _evaluate(parsed, rows(values, releases))
                self.assertEqual(result["status"], until_oracle(values, releases), (values, releases))


if __name__ == "__main__":
    unittest.main()
