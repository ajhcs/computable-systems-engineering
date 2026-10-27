"""Process-local parser reuse slot; unset outside an explicitly checked batch."""
from contextvars import ContextVar

PARSE_SESSION = ContextVar('cse_sysml_parse_session', default=None)
