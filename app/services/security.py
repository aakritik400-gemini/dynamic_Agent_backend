import re
from typing import Any


# Generic refusal message to avoid echoing back any sensitive user content.
SENSITIVE_REFUSAL_MESSAGE = (
    "Sorry, this info can't be provided because it's confidential."
)


# Matches "password: <value>", "api key=<value>", "token: <value>", etc.
_LABELED_SECRET_RE = re.compile(
    r"(?i)\b("
    r"password|passcode|secret|api[-_ ]?key|token|credential[s]?"
    r")\b\s*[:=]\s*([^\s,.;]+)"
)


# Matches "password is <value>" / "secret is <value>" style.
_IS_SECRET_RE = re.compile(
    r"(?i)\b("
    r"password|passcode|secret|api[-_ ]?key|token|credential[s]?"
    r")\b\s+is\s+([^\s,.;]+)"
)


# Disclosure request detection: looks for verbs like reveal/show/etc around
# password/secret/credential terms.
_DISCLOSURE_VERB_RE = r"(reveal|show|share|give|expose|leak|display)"
_SECRET_TERM_RE = r"(password|passcode|secret|api[-_ ]?key|token|credential[s]?)"

_SENSITIVE_REQUEST_RE = re.compile(
    rf"(?ix)"
    rf"(?:\b{_SECRET_TERM_RE}\b\s+.*\b{_DISCLOSURE_VERB_RE}\b)"
    rf"|(?:\b{_DISCLOSURE_VERB_RE}\b\s+.*\b{_SECRET_TERM_RE}\b)"
    rf"|\b(what\s+is\s+my\s+|what\s+is\s+your\s+){_SECRET_TERM_RE}\b"
)


def redact_secrets(text: Any) -> Any:
    """
    Best-effort redaction for common secret/password patterns.
    Returns non-str inputs unchanged.
    """
    if text is None or not isinstance(text, str):
        return text

    redacted = _LABELED_SECRET_RE.sub(r"\1: [REDACTED]", text)
    redacted = _IS_SECRET_RE.sub(r"\1 is [REDACTED]", redacted)
    return redacted


def user_requests_sensitive_disclosure(text: Any) -> bool:
    """True if the user is requesting disclosure of passwords/secrets."""
    if text is None or not isinstance(text, str):
        return False
    return bool(_SENSITIVE_REQUEST_RE.search(text))

