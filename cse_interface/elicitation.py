"""Persistent, revision-bound domain questions; never approval or model mutation."""
from hashlib import sha256
import json
import secrets
from pathlib import Path

from .contracts import InterfaceError, TEXT, PATHS, obj, validate

OP = {"enum": ["inspect", "validate", "explain", "edit", "decompose", "migrate", "compare"]}
QUESTION = obj({"key": {"type": "string", "minLength": 1, "maxLength": 80, "pattern": r"[a-z][a-z0-9_]*"},
                "question": TEXT, "reason": TEXT, "needed_for": OP,
                "type": {"enum": ["text", "choice", "number", "boolean"]},
                "choices": {"type": "array", "items": TEXT, "minItems": 2, "maxItems": 6, "uniqueItems": True}},
               ("key", "question", "reason", "needed_for", "type"))


def revision(context):
    # Known facts are caller-declared; this contract does not authenticate their authority.
    if not isinstance(context, dict) or set(context) != {"operation", "models", "known"}:
        raise InterfaceError("invalid_context", "Expected operation, models and known facts", "Supply the current operation and source paths.")
    validate(context["operation"], OP)
    validate(context["models"], PATHS)
    if not isinstance(context["known"], dict):
        raise InterfaceError("invalid_context", "Known facts must be an object", "Use field names mapped to already supplied values.")
    paths = [Path(x).resolve() for x in context["models"]]
    if len(paths) != len(set(paths)):
        raise InterfaceError("duplicate_input", "Repeated model path", "Supply each source once.")
    sources = []
    total = 0
    for path in sorted(paths):
        if not path.is_file():
            raise InterfaceError("missing_file", f"Missing context source: {path}", "Restore the source before eliciting.")
        total += path.stat().st_size
        if total > 5000000:
            raise InterfaceError("context_limit", "Question context exceeds 5 MB", "Select the relevant source bundle explicitly.")
        sources.append([str(path), sha256(path.read_bytes()).hexdigest()])
    raw = json.dumps([context["operation"], context["known"], sources], sort_keys=True, allow_nan=False)
    return sha256(raw.encode()).hexdigest()


def transition(state, request):
    """Pure transition. CLI persists this ledger under a lock; no source is edited."""
    if not isinstance(request, dict) or request.get("action") not in ("prepare", "answer"):
        raise InterfaceError("invalid_action", "Expected prepare or answer", "Use elicit-help for the two request schemas.")
    state = json.loads(json.dumps(state))
    action = request["action"]
    if action == "prepare":
        if set(request) != {"action", "context", "question"}:
            raise InterfaceError("invalid_fields", "Prepare expects context and question", "Use elicit-help.")
        context, question = request["context"], request["question"]
        rev = revision(context)
        validate(question, QUESTION, "question")
        if (question["type"] == "choice") != ("choices" in question):
            raise InterfaceError("invalid_choices", "Only choice questions require choices", "Supply 2–6 distinct choices, or use a different type.")
        for item in state.get("questions", []):
            if item["status"] == "pending" and item["revision"] != rev:
                item["status"] = "stale"
        if context["operation"] in ("inspect", "validate", "explain") or question["key"] in context["known"] or question["needed_for"] != context["operation"]:
            return state, {"status": "not_needed", "reason": "Read-only work, already known answer, or unrelated decision", "questions": []}
        fingerprint = sha256(json.dumps([rev, question], sort_keys=True).encode()).hexdigest()
        for item in state.get("questions", []):
            if item["revision"] == rev and item["question"]["key"] == question["key"]:
                if item["status"] == "pending":
                    return state, {"status": "pending", "id": item["id"], "revision": rev, "question": item["question"]}
                return state, {"status": "not_needed", "reason": "Already answered or cancelled for this revision", "questions": []}
        # One current pending question. Changed context invalidates earlier answers.
        for item in state.get("questions", []):
            if item["status"] == "pending":
                if item["revision"] == rev:
                    raise InterfaceError("question_pending", "A question already awaits a response", "Resolve or cancel it before asking another.")
                item["status"] = "stale"
        if len(state.get("questions", [])) >= 128:
            raise InterfaceError("ledger_limit", "Question ledger reached its bound", "Start a new explicitly scoped ledger; retain this one as evidence.")
        item = {"id": secrets.token_hex(12), "revision": rev, "fingerprint": fingerprint,
                "status": "pending", "question": question, "context": context}
        state.setdefault("questions", []).append(item)
        return state, {"status": "pending", "id": item["id"], "revision": rev, "question": question,
                       "authority": "domain_clarification_only"}
    validate(request, obj({"action": {"enum": ["answer"]}, "id": TEXT, "revision": TEXT,
                           "outcome": {"enum": ["accept", "cancel", "decline"]},
                           "content": {}}, ("action", "id", "revision", "outcome")), "reply")
    matches = [x for x in state.get("questions", []) if x["id"] == request["id"]]
    if len(matches) != 1 or matches[0]["status"] != "pending":
        raise InterfaceError("inactive_question", "Question is unknown, resolved or stale", "Prepare only the still-missing current decision.")
    item = matches[0]
    if request["revision"] != item["revision"] or revision(item["context"]) != item["revision"]:
        raise InterfaceError("stale_question", "The question's source revision has changed", "Prepare a fresh question against current source bytes and facts.")
    if request["outcome"] != "accept":
        if "content" in request:
            raise InterfaceError("unexpected_content", "Cancelled/declined responses cannot carry an answer", "Omit content; no answer will be inferred.")
        item["status"] = request["outcome"]
        return state, {"status": request["outcome"], "applied": False}
    if "content" not in request:
        raise InterfaceError("missing_answer", "Accept requires an explicit answer", "Provide content; a displayed default is not a response.")
    question = item["question"]
    schema = {"text": TEXT, "choice": {"enum": question.get("choices", [])},
              "number": {"type": "number"}, "boolean": {"type": "boolean"}}[question["type"]]
    validate(request["content"], schema, "reply.content")
    item["status"], item["answer"] = "answered", request["content"]
    return state, {"status": "answered", "key": question["key"], "value": request["content"],
                   "revision": item["revision"], "applied": False, "authority": "domain_clarification_only"}
