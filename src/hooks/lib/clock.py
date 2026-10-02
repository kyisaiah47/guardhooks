"""Checks clock claims against the transcript's own timestamps.

Every assistant frame in a Claude Code transcript carries an ISO 8601 `timestamp`, which is the
real instant that text was written. A hook can therefore compare a stated "it's 7:36 now" with
the true time of that sentence, without trusting the model.

Tool calls are not a clock. The only way to know the time is to read it again each time it is
stated.
"""
import json
import re
from datetime import datetime, timedelta

# How far a stated "now" may sit from the true instant the sentence was written.
TOLERANCE_MIN = 4
# How old the most recent clock reading may be when deadline or elapsed-time arithmetic is done.
STALE_READ_MIN = 5

CLOCK_READ = [re.compile(p, re.I) for p in (
    r"(?:^|[;&|(\s`$])(?:/bin/)?g?date\b",
    r"\bdatetime\.now\b",
    r"\bdatetime\.utcnow\b",
    r"\btime\.time\s*\(",
    r"\bDate\.now\s*\(",
    r"\bnew\s+Date\s*\(",
    r"\bTZ=[^\s]+\s+date\b",
)]


def reads_clock(cmd):
    return bool(cmd) and any(rx.search(cmd) for rx in CLOCK_READ)


# A time needs minutes or am/pm to count, so "currently 3 files" is never read as 03:00.
# The frames are about the present; a time in "the 00:30 nightly job" claims nothing about now.
_T = (r"(?:(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?"
      r"|(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.))")

NOW_FRAMES = [re.compile(p, re.I) for p in (
    r"\bit'?s\s+(?:now\s+)?(?:about\s+|roughly\s+|around\s+|nearly\s+|almost\s+|just\s+(?:after|before|gone)\s+)?" + _T + r"\b",
    r"\bit\s+is\s+(?:now\s+)?(?:about\s+|roughly\s+|around\s+)?" + _T + r"\b",
    r"\bright\s+now\s+(?:it'?s\s+|is\s+)?" + _T + r"\b",
    r"\b(?:the\s+)?(?:real\s+)?time\s+(?:right\s+now\s+)?is\s+(?:now\s+)?" + _T + r"\b",
    r"\bcurrent(?:ly)?\s+(?:it'?s\s+)?" + _T + r"\b",
    r"\bas\s+of\s+" + _T + r"\b",
    r"\bclock\s+(?:reads|says|is\s+at)\s+" + _T + r"\b",
    r"\bwe'?re\s+at\s+" + _T + r"\b",
    r"\b" + _T + r"\s+(?:right\s+)?now\b",
)]

ELAPSED_FRAMES = [re.compile(p, re.I) for p in (
    r"\b\d+\s*(?:minutes?|mins?|hours?|hrs?)\s+(?:left|remaining|away|to\s+go|until|have\s+passed|has\s+passed|passed|elapsed|ago)\b",
    r"\b(?:that\s+)?(?:leaves|gives|buys)\s+(?:us|you|me)?\s*\d+\s*(?:more\s+)?(?:minutes?|mins?|hours?|hrs?)\b",
    r"\bwe\s+have\s+(?:about\s+|roughly\s+|only\s+)?\d+\s*(?:minutes?|mins?|hours?|hrs?)\s+(?:left|before|until|to\s+go|to\s+work\s+with)\b",
    r"\bwon'?t\s+make\s+" + _T + r"\b",
    r"\b(?:in\s+time\s+for|before)\s+the\s+\d{1,2}\s*(?:am|pm)\s+(?:drop|deadline|cut|post|release|meeting)\b",
    r"\bnot\s+enough\s+time\s+(?:left\s+)?(?:to|before)\b",
    r"\b\d+\s*(?:minutes?|mins?)\s+(?:to|until|before)\s+" + _T + r"\b",
)]

# Quoting is not claiming. Fenced code, inline code, blockquotes and double-quoted spans are
# reported speech.
_FENCE = re.compile(r"```.*?```", re.S)
_INLINE = re.compile(r"`[^`\n]*`")
_BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)
_DQUOTE = re.compile("[\"“‘’”][^\"“”\n]{0,300}[\"”]")


def strip_quoted(text):
    for rx in (_FENCE, _INLINE, _BLOCKQUOTE, _DQUOTE):
        text = rx.sub(" ", text)
    return text


def now_claims(text):
    """[(phrase, hour, minute, ampm or None)] for every time asserted as the present."""
    out = []
    body = strip_quoted(text or "")
    for rx in NOW_FRAMES:
        for m in rx.finditer(body):
            if m.group(1):
                h, mi = int(m.group(1)), int(m.group(2))
                ap = (m.group(3) or "").replace(".", "").lower() or None
            else:
                h, mi = int(m.group(4)), 0
                ap = (m.group(5) or "").replace(".", "").lower() or None
            if h > 24 or mi > 59:
                continue
            out.append((" ".join(m.group(0).split()), h, mi, ap))
    return out


def elapsed_claims(text):
    body = strip_quoted(text or "")
    return sorted({" ".join(m.group(0).split()) for rx in ELAPSED_FRAMES for m in rx.finditer(body)})


def delta_minutes(h, mi, ap, real):
    """Smallest distance in minutes between a stated time and the true instant.

    With no am/pm marker both readings of a 12-hour clock are tried, so a claim is only flagged
    when it is wrong under every honest reading.
    """
    if ap == "pm":
        cands = [h % 12 + 12]
    elif ap == "am":
        cands = [h % 12]
    else:
        cands = [h] if h >= 13 else [h, h + 12]
    best = None
    for hh in cands:
        if hh > 23:
            continue
        for day in (-1, 0, 1):
            t = real.replace(hour=hh, minute=mi, second=0, microsecond=0) + timedelta(days=day)
            d = abs((t - real).total_seconds()) / 60.0
            if best is None or d < best:
                best = d
    return 10 ** 9 if best is None else best


def _text_of(msg):
    c = (msg or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _stamp(d):
    ts = d.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None


def read_turn(transcript_path):
    """(turn start, [(when, text)] assistant text blocks, [(when, command)] tool calls) for this turn.

    A tool_result frame also has role=user, so only a user frame without a tool_use_id starts a turn.
    """
    start, blocks, cmds = None, [], []
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue
                m = d.get("message") or {}
                role = m.get("role")
                content = m.get("content")
                when = _stamp(d)
                if role == "user":
                    t = _text_of(m)
                    if t.strip() and "tool_use_id" not in json.dumps(content)[:400]:
                        start, blocks, cmds = when, [], []
                elif role == "assistant":
                    t = _text_of(m)
                    if t.strip() and when:
                        blocks.append((when, t))
                    if isinstance(content, list):
                        for b in content:
                            if isinstance(b, dict) and b.get("type") == "tool_use":
                                c = (b.get("input") or {}).get("command")
                                if isinstance(c, str) and when:
                                    cmds.append((when, c))
    except Exception:
        pass
    return start, blocks, cmds


def last_read_before(cmds, when):
    """The most recent instant the clock was read before `when`."""
    best = None
    for t, c in cmds:
        if t <= when and reads_clock(c):
            if best is None or t > best:
                best = t
    return best
