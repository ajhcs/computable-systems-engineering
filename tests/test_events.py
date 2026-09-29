"""Exact event identity and time-bound checks."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.events import EventError, check_event_trace, parse_event_clause

TRIGGER = "Example::controller::request"
RESPONSE = "Example::controller::ack"
CLAUSE = parse_event_clause("Each unit.request shall within 2 seconds have unit.ack with matching correlationId.")


def evidence(*events, horizon="3", complete=True):
    return {"complete": complete, "observed_until": {"time": horizon, "unit": "seconds"},
            "events": [{"event": name, "time": time, "unit": "seconds", "correlationId": identity}
                       for name, time, identity in events]}


def status(value):
    return check_event_trace(CLAUSE, value, trigger_path=TRIGGER, response_path=RESPONSE)["status"]


class EventTests(unittest.TestCase):
    def test_inclusive_deadline_and_identity(self):
        self.assertEqual(status(evidence((TRIGGER, "0", "A"), (RESPONSE, "2", "A"))), "pass")
        wrong_id = evidence((TRIGGER, "0", "A"), (RESPONSE, "1", "B"))
        self.assertEqual(status(wrong_id), "fail")
        self.assertEqual(status(evidence((TRIGGER, "0", "A"), (RESPONSE, "2.001", "A"))), "fail")
        self.assertEqual(status(evidence((RESPONSE, "0", "A"), (TRIGGER, "1", "A"))), "fail")

    def test_pending_incomplete_and_overlap(self):
        self.assertEqual(status(evidence((TRIGGER, "0", "A"), horizon="1.999")), "unknown")
        self.assertEqual(status(evidence((TRIGGER, "0", "A"), horizon="3", complete=False)), "unknown")
        overlapping = evidence((TRIGGER, "0", "A"), (TRIGGER, "0.5", "B"),
                               (RESPONSE, "1", "B"), (RESPONSE, "2", "A"))
        self.assertEqual(status(overlapping), "pass")
        self.assertEqual(status(evidence(horizon="3")), "unknown")

    def test_malformed_and_budget(self):
        with self.assertRaises(EventError):
            parse_event_clause("Each unit.request shall eventually have unit.ack.")
        with self.assertRaises(EventError):
            status(evidence((TRIGGER, "0", "A"), (TRIGGER, "1", "A")))
        with self.assertRaises(EventError):
            status(evidence((TRIGGER, "2", "A"), (RESPONSE, "1", "A")))
        capped = check_event_trace(CLAUSE, evidence((TRIGGER, "0", "A"), (RESPONSE, "1", "A")),
                                   trigger_path=TRIGGER, response_path=RESPONSE, event_cap=1)
        self.assertEqual(capped["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
