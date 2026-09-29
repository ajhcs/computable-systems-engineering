"""Small attributed derivatives of public systems-engineering examples.

All observations are synthetic. Passing them never validates the source's intent
or the performance of an actual FHWA/NASA system.
"""

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.language import LanguageError, check_document, parse_requirement


def fhwa_response(*, response_at=601, length=602):
    """Candidate from FHWA-HOP-13-047 §3.6.2; 100 ms sampled event pulses."""
    model = {
        "language_version": 1,
        "clock": {"period": "100", "unit": "milliseconds"},
        "actors": {"OwnerCenter": {}},
        "properties": {
            "request_complete": {"type": "bool", "owner": "input"},
            "response_started": {"type": "bool", "owner": "controlled"},
        },
        "requirements": {"FHWA_3_6_2":
            "Upon request_complete = true, OwnerCenter shall within 1 minute satisfy response_started = true."},
        "observations": [
            {"request_complete": i == 1, "response_started": i == response_at}
            for i in range(length)
        ],
        "complete": True,
    }
    return model


def asct_alarm(*, alarm_at=3, length=4):
    """Hypothetical two-minute completion of FHWA-HOP-11-027 §13.2-3."""
    return {
        "language_version": 1,
        "clock": {"period": "1", "unit": "minutes"},
        "actors": {"ASCT": {}},
        "properties": {
            "failure_detected": {"type": "bool", "owner": "input"},
            "alarm_issued": {"type": "bool", "owner": "controlled"},
        },
        "requirements": {"ASCT_13_2_3_HYPOTHETICAL":
            "Upon failure_detected = true, ASCT shall within 2 minutes satisfy alarm_issued = true."},
        "observations": [
            {"failure_detected": i == 1, "alarm_issued": i == alarm_at}
            for i in range(length)
        ],
        "complete": True,
    }


NASA = json.loads((ROOT / "examples/language/public/nasa_low_power_candidate.json").read_text())


class PublicCaseTests(unittest.TestCase):
    def test_fhwa_measured_response_deadline(self):
        on_deadline = check_document(fhwa_response(), review=True)
        self.assertEqual(on_deadline["status"], "pass")
        self.assertEqual(on_deadline["claim_scope"], "candidate_sampled_trace")
        self.assertEqual(on_deadline["results"]["FHWA_3_6_2"]["deadline_ticks"], 600)
        late = check_document(fhwa_response(response_at=602, length=603), review=True)
        self.assertEqual(late["status"], "fail")
        self.assertEqual(late["results"]["FHWA_3_6_2"]["counterexample"]["deadline_index"], 601)
        prefix = check_document(fhwa_response(response_at=602, length=601), review=True)
        self.assertEqual(prefix["status"], "unknown")

    def test_fhwa_request_identity_is_not_represented(self):
        model = fhwa_response(response_at=4, length=605)
        model["observations"][3]["request_complete"] = True
        # One response pulse can satisfy both overlapping Boolean obligations.
        # FHWA's request/response relationship needs identifiers or a stated
        # single-outstanding-request assumption before this becomes faithful.
        self.assertEqual(check_document(model, review=True)["status"], "pass")

    def test_asct_placeholder_rejected_and_hypothetical_bound_checked(self):
        model = asct_alarm()
        placeholder = model["requirements"]["ASCT_13_2_3_HYPOTHETICAL"].replace("2 minutes", "XX minutes")
        with self.assertRaises(LanguageError) as caught:
            parse_requirement(placeholder, model["actors"], model["properties"], model["clock"])
        self.assertEqual(caught.exception.code, "grammar")
        unresolved = copy.deepcopy(model)
        unresolved["requirements"]["ASCT_13_2_3_HYPOTHETICAL"] = placeholder
        self.assertEqual(check_document(unresolved, review=True)["status"], "error")
        self.assertEqual(check_document(model, review=True)["status"], "pass")
        self.assertEqual(check_document(asct_alarm(alarm_at=4, length=5), review=True)["status"], "fail")
        self.assertEqual(check_document(asct_alarm(alarm_at=4, length=3), review=True)["status"], "unknown")

    def test_nasa_hold_past_tli_until_supplementary_power(self):
        self.assertEqual(check_document(NASA, review=True)["status"], "pass")
        early_exit = copy.deepcopy(NASA)
        early_exit["observations"][2]["low_power"] = False
        failure = check_document(early_exit, review=True)
        self.assertEqual(failure["status"], "fail")
        self.assertEqual(failure["results"]["N_low_power"]["counterexample"]["index"], 2)
        no_docking = copy.deepcopy(NASA)
        no_docking["observations"] = no_docking["observations"][:-1]
        self.assertEqual(check_document(no_docking, review=True)["status"], "unknown")

    def test_nasa_tli_order_is_not_represented(self):
        before_tli = copy.deepcopy(NASA)
        before_tli["observations"][2]["supplementary_power_available"] = True
        before_tli["observations"][2]["tli_complete"] = False
        before_tli["observations"][2]["low_power"] = False
        # The clause checks a hold-until boundary, not the mission event order.
        self.assertEqual(check_document(before_tli, review=True)["status"], "pass")


if __name__ == "__main__":
    unittest.main()
