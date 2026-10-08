"""Serialized byte bounds shared by request admission and ledger persistence."""
import json

REQUEST_LIMIT_BYTES = 1_000_000
LEDGER_LIMIT_BYTES = 16 * 1024 * 1024
ANSWER_LIMIT_BYTES = 64 * 1024
# An answer adds its JSON value, the answer key, and a longer status. This
# conservative reserve exceeds that exact growth with the serialization below.
RESOLUTION_RESERVE_BYTES = ANSWER_LIMIT_BYTES + 128


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")
