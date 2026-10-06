# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

"""Lightweight intent gate for the Vibe Coding Assistant.

Decides — cheaply and locally, with NO provider/API call — whether a user
message is a genuine request to build or modify an Odoo module, an obviously
off-topic message (greeting, small talk, general/factual question), or
ambiguous.

The point is to avoid spending ~1k input tokens on the full module-generation
system prompt when the user clearly isn't asking for a module (e.g. "hi",
"what is the time now"). On a confident "offtopic" verdict the caller can
short-circuit with a friendly message at zero token cost.

Verdicts returned by :func:`check_intent`:
    "build"    -> proceed to module generation
    "offtopic" -> refuse for free; do NOT call the provider
    "unsure"   -> ambiguous; the caller decides what to do

Design principle: CONSERVATIVE / fail-open. We only return "offtopic" when
we're confident. Anything carrying a build signal, or that we can't
categorise, is left to the generator so a real request is never silently
blocked. Mis-gating a real request is far worse than occasionally paying for
a borderline one.

Extension hook: :func:`classify_with_llm` is a placeholder for a future tiny
classifier call to resolve "unsure" cases with high accuracy. It is
intentionally NOT wired into :func:`check_intent` — wire it at the call site
if/when you decide the extra round-trip is worth it. See the docstring there
for the recommended hybrid policy.
"""

import re

# ── Signal vocabularies ────────────────────────────────────────────────────

# Strong signals that the user wants something built/changed. Presence of ANY
# of these (as a whole word) classifies the message as "build" immediately —
# this check runs first, so a build request phrased as a question
# ("Can you create a module to…") is still correctly treated as a build.
BUILD_KEYWORDS = frozenset({
    # actions
    "create", "build", "generate", "make", "add", "implement", "develop",
    "scaffold", "extend", "inherit", "customize", "customise", "modify",
    "manage", "track", "handle", "register",
    # odoo artefacts
    "module", "addon", "model", "field", "fields", "view", "views", "form",
    "list", "tree", "kanban", "report", "wizard", "menu", "menuitem",
    "security", "access", "rule", "constraint", "compute", "computed",
    "onchange", "sequence", "automation", "cron", "workflow", "dashboard",
    "crud", "many2one", "one2many", "many2many", "selection",
})
# NOTE: deliberately NOT including weak/ambiguous words like "odoo",
# "record", "screen", "button", or "integration". They appear in off-topic
# questions ("what is odoo", "what is a record") as often as in real build
# requests — and a genuine build request almost always carries a strong
# action verb or artefact word above, so dropping them avoids false
# "build" verdicts on questions without missing real requests.

# Whole-message greetings / acknowledgements / filler. Matched after
# normalisation (lowercased, punctuation stripped, whitespace collapsed).
GREETINGS = frozenset({
    "hi", "hello", "hey", "heya", "hiya", "yo", "howdy", "sup", "howdy",
    "good morning", "good afternoon", "good evening", "good day", "gm",
    "thanks", "thank you", "thx", "ty", "cheers", "ok", "okay", "k",
    "bye", "goodbye", "see you", "test", "testing", "ping", "hello there",
})

# Interrogative openers. A message that starts with one of these and carries
# no build keyword is treated as a general question (offtopic) — but only
# when it's reasonably short, so long descriptive requests phrased as a
# question ("how would I best organise …") fall through to the generator.
QUESTION_STARTERS = frozenset({
    "what", "whats", "who", "whom", "whose", "when", "where", "why",
    "how", "which", "is", "are", "am", "was", "were", "do", "does",
    "did", "can", "could", "will", "would", "should", "tell", "explain",
})

# A question with more words than this is likely a real (if verbose) build
# brief rather than idle chit-chat, so we don't gate it.
MAX_QUESTION_WORDS = 14

_WORD_RE = re.compile(r"[a-z_][a-z0-9_]*")
_NORMALISE_RE = re.compile(r"[^a-z0-9\s]+")


def _tokens(text):
    """Lowercase word tokens, e.g. 'product.template' -> ['product', 'template']."""
    return _WORD_RE.findall(text.lower())


def _normalise(text):
    """Lowercase, strip punctuation, collapse whitespace — for greeting match."""
    stripped = _NORMALISE_RE.sub(" ", text.lower())
    return " ".join(stripped.split())


def check_intent(message):
    """Classify a user message without any network/provider call.

    :param message: the raw user message string.
    :returns: dict ``{"verdict": "build"|"offtopic"|"unsure", "reason": str}``.
        ``reason`` is a short machine-ish tag for logging/debugging, never
        shown to end users.
    """
    text = (message or "").strip()
    if not text:
        # Empty is handled (rejected) upstream; treat as unsure here so we
        # never accidentally swallow it as offtopic.
        return {"verdict": "unsure", "reason": "empty"}

    tokens = _tokens(text)
    token_set = set(tokens)

    # 1. Any build signal wins — checked first so questions that ask for a
    #    build ("can you create a module…") are not mistaken for chit-chat.
    hits = token_set & BUILD_KEYWORDS
    if hits:
        return {"verdict": "build", "reason": "build_kw:" + ",".join(sorted(hits))}

    # 2. Whole-message greeting / acknowledgement.
    if _normalise(text) in GREETINGS:
        return {"verdict": "offtopic", "reason": "greeting"}

    # 3. Short general/factual question with no build signal.
    if tokens and tokens[0] in QUESTION_STARTERS and len(tokens) <= MAX_QUESTION_WORDS:
        return {"verdict": "offtopic", "reason": "short_question"}

    # 4. Anything else is ambiguous — fail open, let the generator handle it.
    return {"verdict": "unsure", "reason": "no_signal"}


# ── Optional classifier hook (NOT wired by default) ────────────────────────

def classify_with_llm(message, generate_fn):
    """Resolve an ambiguous message with a tiny, cheap classifier call.

    This is a deliberate extension point, not used by :func:`check_intent`.
    Recommended hybrid policy at the call site::

        gate = check_intent(content)
        verdict = gate["verdict"]
        if verdict == "unsure":
            # only the genuinely ambiguous minority pays for this call
            verdict = classify_with_llm(content, provider.generate)

        if verdict == "offtopic":
            ...short-circuit, zero generation cost...

    :param message: the raw user message.
    :param generate_fn: a callable ``(system_prompt, user_prompt) -> (text, usage)``
        — e.g. ``provider.generate`` — used to ask a yes/no question with a
        minimal prompt (~tens of tokens rather than ~1k).
    :returns: "build" or "offtopic".

    Intentionally unimplemented: wiring this in is a product decision
    (extra latency + per-request token cost on ambiguous messages) that
    should be made explicitly. See the trade-off discussion in the module
    README / commit history.
    """
    raise NotImplementedError(
        "classify_with_llm is an opt-in extension point — wire it into "
        "vibe.conversation.action_send_message if you want LLM-backed "
        "resolution of 'unsure' verdicts."
    )
