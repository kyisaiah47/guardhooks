"""Paid model API keys are spent only by paying customers' requests.

The patterns live once, in paid_inference_patterns.json beside this file. Read by
no-unpaid-inference.py.

What spends a paid key: a paying customer's own request inside a shipped product. Nothing else.
Not a test, a health check, a warmup, a smoke test, an eval, a free tier, a trial, a demo, a
scheduled job, a CI run or a script.

Two moves are free and are never blocked:
  1. GET /v1/models on either host. It lists models and does not spend.
  2. Reading an error body. A 401 or a 400 credit message costs nothing.

Never blocked either: editing a product's inference driver, reading it, importing it from product
code behind an entitlement check, and the files that carry this rule.
"""
import json
import os
import re

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "paid_inference_patterns.json"),
          encoding="utf-8") as _fh:
    _P = json.load(_fh)


def _rx(name):
    return re.compile(_P[name], re.I | re.M)


HOST_RE = _rx("host")
SPEND_PATH = _rx("spend_path")
MODELS_PATH = _rx("models_path")
HAS_BODY = _rx("has_body")
SDK_SPEND = _rx("sdk_spend")
SDK_CTOR = _rx("sdk_ctor")
CURL_LIKE = _rx("curl_like")
INLINE_RUN = _rx("inline_run")
FREE_RAIL = _rx("free_rail")
UNPAID_PATH = _rx("unpaid_path")
EXEMPT_PATH = _rx("exempt_path")

BLOCK_TEXT = (
    "Paid model API keys are spent only by paying customers' requests.\n"
    "\n"
    "This call would spend an Anthropic or OpenAI API key outside a paying customer's request.\n"
    "Tests, evals, demos, health checks, warmups, CI jobs and scheduled scripts never spend a paid key.\n"
    "One careless test run against a large document can cost real money.\n"
    "\n"
    "These moves are free and always allowed:\n"
    "  - GET /v1/models lists models and does not spend. Read the status and the error body to check a key.\n"
    "  - Unset the key so the code path runs against its stub.\n"
    "  - Test on a free tier or a local model, such as the Gemini free tier or a model on localhost.\n"
    "  - Put a product's model call behind its paid-entitlement check, and read the key only after the\n"
    "    check passes.\n"
    "\n"
    "To quote a spending command in a file on purpose, put it in a fenced code block, an inline\n"
    "backtick span or a '>' blockquote. A Bash command is never treated as a quotation.\n"
)

_FENCE = re.compile(r"```.*?```", re.S)
_INDENT_BLOCK = re.compile(r"^(?: {4}|\t).*$", re.M)
_QUOTE = re.compile(r"^\s*>.*$", re.M)
_TICK = re.compile(r"`[^`\n]*`")


def _clean(blob):
    """Strip fenced blocks, blockquotes, indented blocks and backtick spans from authored text.
    Applied only when a file is written. A Bash command is matched raw."""
    blob = _FENCE.sub(" ", blob)
    blob = _QUOTE.sub(" ", blob)
    blob = _INDENT_BLOCK.sub(" ", blob)
    blob = _TICK.sub(" ", blob)
    return blob


def find(blob, path="", authored=False):
    """Return the reasons this tool call must be denied. An empty list means allow.

    authored is True for a Write, Edit or NotebookEdit, where the blob is file content and the
    quoting carve applies. It is False for a Bash command or a fetched URL, matched raw.
    """
    if path and EXEMPT_PATH.search(path):
        return []
    if EXEMPT_PATH.search(blob):
        return []
    if authored:
        blob = _clean(blob)

    reasons = []
    # A URL written into product source is a constant, not a spend. Handing it to a shell HTTP
    # client is the spend. So in authored content checks 1 and 2 need a client present.
    executes = (not authored) or bool(CURL_LIKE.search(blob))

    # 1. a direct HTTP call to a spending endpoint
    if executes and SPEND_PATH.search(blob):
        reasons.append(
            "an HTTP call to a spending endpoint on api.anthropic.com or api.openai.com. "
            "Only GET /v1/models is free.")

    # 2. the host named with a request body, whatever path it claims
    if executes and not reasons and HOST_RE.search(blob) and HAS_BODY.search(blob):
        reasons.append(
            "a POST, PUT or PATCH with a body against api.anthropic.com or api.openai.com. "
            "A request that carries a body is a spend.")

    # 3. an SDK spending method a session is about to run
    if (SDK_SPEND.search(blob)
            and not FREE_RAIL.search(blob)
            and (INLINE_RUN.search(blob) or SDK_CTOR.search(blob))):
        reasons.append(
            "an Anthropic or OpenAI SDK method that bills (messages.create, "
            "chat.completions.create, responses.create, embeddings.create or a sibling).")

    # 4. a spending call written into a path that is not a paying customer
    if (path and UNPAID_PATH.search(path)
            and not FREE_RAIL.search(blob)
            and (SDK_SPEND.search(blob) or SPEND_PATH.search(blob))):
        reasons.append(
            "a model call written into %s, which is a test, fixture, seed, eval, smoke, warmup, "
            "health check, example, demo, CI or scheduled-job path. None of those is a paying "
            "customer." % path)

    return reasons
