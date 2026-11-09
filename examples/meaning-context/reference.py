"""Trusted synthetic unit fixtures, including two deliberately faulty variants.

These functions are ordinary test code, not code interpreted from model text.
No network, clinical service, or operational observation is involved.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Acknowledgement:
    referral_id: str
    clinic_id: str


@dataclass
class Handoff:
    referral_id: str
    clinic_id: str
    sent: bool = False
    acknowledged: bool = False
    received: list = field(default_factory=list)

    def send_referral(self):
        self.sent = True

    def receive_acknowledgement(self, acknowledgement):
        self.received.append(acknowledgement)
        if (acknowledgement.referral_id == self.referral_id
                and acknowledgement.clinic_id == self.clinic_id):
            self.acknowledged = True

    @property
    def complete(self):
        return self.acknowledged


class CompletesOnSend(Handoff):
    """Negative control: sending incorrectly establishes completion."""
    @property
    def complete(self):
        return self.sent or self.acknowledged


class AcceptsAnyAcknowledgement(Handoff):
    """Negative control: an unrelated acknowledgement incorrectly completes."""
    def receive_acknowledgement(self, acknowledgement):
        self.received.append(acknowledgement)
        self.acknowledged = True
