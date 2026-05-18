"""
intent_parser.py — Hybrid intent parser for Project RAY.

Fuzzy matching runs first (near-instant).  If confidence is below
``FUZZY_THRESHOLD``, falls back to Ollama llama3.2:3b for natural-
language understanding.

Every public function returns a consistent dict::

    {"intent": str, "entity": str, "source": str}

Intent categories:  open_app | file_search | web_search | exit | unknown
Source values:       "fuzzy"  | "llm"       | "llm_error"
"""

import json

# pyrefly: ignore [missing-import]
from rapidfuzz import fuzz, process
# pyrefly: ignore [missing-import]
import ollama

from config import (
    APP_COMMANDS,
    ALIASES,
    EXIT_PHRASES,
    FUZZY_THRESHOLD,
    OLLAMA_MODEL,
    LLM_TIMEOUT_SECONDS,
)


# ── Fuzzy match pool ──────────────────────────────────────────────
# Each entry maps a candidate phrase → (intent, resolved_entity)
_MATCH_POOL: dict[str, tuple[str, str]] = {}

# APP_COMMANDS keys → open_app  (entity = the key itself)
for _key in APP_COMMANDS:
    _MATCH_POOL[_key] = ("open_app", _key)

# ALIASES keys → open_app  (entity = the resolved canonical command)
for _alias, _canonical in ALIASES.items():
    _MATCH_POOL[_alias] = ("open_app", _canonical)

# EXIT_PHRASES → exit  (no entity)
for _phrase in EXIT_PHRASES:
    _MATCH_POOL[_phrase] = ("exit", "")

# Static file-search patterns
_FILE_SEARCH_PATTERNS = ["find file", "find", "open file", "where is"]
for _pat in _FILE_SEARCH_PATTERNS:
    _MATCH_POOL[_pat] = ("file_search", _pat)

# Static web-search patterns
_WEB_SEARCH_PATTERNS = ["search for", "look up", "google", "search"]
for _pat in _WEB_SEARCH_PATTERNS:
    _MATCH_POOL[_pat] = ("web_search", _pat)

# Pre-compute the list of candidate strings for rapidfuzz
_CANDIDATES = list(_MATCH_POOL.keys())


# ── LLM system prompt ────────────────────────────────────────────
_LLM_SYSTEM_PROMPT = (
    "You are an intent classifier for a voice assistant. "
    "Respond ONLY with valid JSON, no explanation.\n"
    "Classify the user input into one of these intents: "
    "open_app, file_search, web_search, exit, unknown.\n"
    "Extract the relevant entity (app name, filename, or search query). "
    "If no entity, use empty string.\n"
    'Format: {"intent": "...", "entity": "..."}'
)


# ── Public API ────────────────────────────────────────────────────

def parse_intent(text: str) -> dict[str, str]:
    """Parse *text* into an intent dict using fuzzy match → LLM fallback.

    Returns
    -------
    dict
        ``{"intent": ..., "entity": ..., "source": ...}``
    """
    text_lower = text.lower().strip()

    # --- Fuzzy layer ---
    result = _fuzzy_match(text_lower)
    if result is not None:
        return result

    # --- LLM fallback ---
    return _llm_classify(text_lower)


def _fuzzy_match(text: str) -> dict[str, str] | None:
    """Attempt fuzzy match against the candidate pool.

    Returns a result dict if confidence >= FUZZY_THRESHOLD, else None.
    """
    match = process.extractOne(text, _CANDIDATES, scorer=fuzz.ratio)
    if match is None:
        return None

    matched_phrase, score, _idx = match
    if score < FUZZY_THRESHOLD:
        return None

    intent, raw_entity = _MATCH_POOL[matched_phrase]

    # --- Entity extraction per intent type ---
    if intent == "open_app":
        entity = raw_entity  # key or resolved alias

    elif intent in ("file_search", "web_search"):
        # Strip the matched pattern prefix; remainder is the entity
        prefix = raw_entity  # the static pattern that was matched
        if text.startswith(prefix):
            entity = text[len(prefix):].strip()
        else:
            # Fuzzy hit — best effort: try to strip the pattern from input
            entity = text
            for pat in (_FILE_SEARCH_PATTERNS if intent == "file_search"
                        else _WEB_SEARCH_PATTERNS):
                if text.startswith(pat):
                    entity = text[len(pat):].strip()
                    break

    elif intent == "exit":
        entity = ""

    else:
        entity = text

    return {"intent": intent, "entity": entity, "source": "fuzzy"}


def _llm_classify(text: str) -> dict[str, str]:
    """Call Ollama llama3.2:3b to classify intent via natural language.

    NOTE: ``LLM_TIMEOUT_SECONDS`` is defined but the ollama Python
    library does not natively support per-call timeouts.  Flagged for
    a future threading wrapper.
    """
    # LLM_TIMEOUT_SECONDS is currently a stub — see docstring above.
    _ = LLM_TIMEOUT_SECONDS  # acknowledge the constant for linters

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )

        raw = response["message"]["content"].strip()

        # Strip markdown code fences if model wraps its JSON
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        parsed = json.loads(raw)
        return {
            "intent": parsed.get("intent", "unknown"),
            "entity": parsed.get("entity", ""),
            "source": "llm",
        }

    except Exception as exc:
        print(f"[intent_parser] LLM error: {exc}")
        return {"intent": "unknown", "entity": text, "source": "llm_error"}
