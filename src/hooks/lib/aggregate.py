"""A headline number about traffic, reach or engagement needs its composition beside it.

A total can be correct while its meaning is false. Common ways that happens:
  n          a small sample reads like a trend.
  window     most of the total landed in one short burst, for example from a campaign that ended.
  spread     one outlier carries the mean while the median is flat.
  per-person views per visitor of about 1.0 with no return visits often means a crawler.
  coverage   a comparison across platforms where only some of them report the metric.

Read by aggregate-composition-stop.py. scan() returns the missing parts for a reply.
"""
import re

# A headline aggregate about an audience or traffic.
AGGREGATE = re.compile(
    r"(\b\d[\d,]{1,8}\s*(?:people|persons?|humans?|users?|visitors?|views?|impressions?|"
    r"followers?|clicks?|sessions?)\b"
    r"|\bavg\s+views?\b|\baverage[sd]?\s+\d|\b\d+(?:\.\d+)?\s*[x×]\s|\bmedian\b)", re.I)

# A ranking or superlative claim, the shape that most needs decomposition.
SUPERLATIVE = re.compile(
    r"\b(biggest|largest|top|#\s?1|number one|best[- ]performing|worst|outperform\w*|"
    r"beats?\b|leads?\b|dominat\w*|carries? (?:all|most)|more than (?:the )?(?:entire|all)|"
    r"only (?:real )?source|dead\b|winner|wins\b)\b", re.I)

TRAFFIC_CTX = re.compile(
    r"\b(traffic|referr\w+|source|channel|account|platform|reach|views?|people|followers?|"
    r"engagement|posts?|clicks?|threads|bluesky|linkedin|youtube|facebook|reddit|"
    r"hacker ?news|instagram|tiktok|google|bing|newsletter|campaign)\b", re.I)

HAS_N = re.compile(r"\bn\s*[=≥>]\s*\d|\b\d+\s+(?:distinct\s+)?posts?\b|\bsample\b|"
                   r"\bn\b\s*of\s*\d|\bcount\b|\bposts?\b\s*\|", re.I)
HAS_WINDOW = re.compile(r"\blast\s+\d+\s*(?:d\b|days?|weeks?|hours?)|\b\d+\s*[- ]?day\b|"
                        r"\b\d{4}-\d{2}-\d{2}\b|\bper (?:week|day)\b|\bby (?:week|day|date)\b|"
                        r"\bweek of\b|\bsince\b\s+\d|→|->", re.I)
HAS_SPREAD = re.compile(r"\bmedian\b|\bper[- ]person\b|\bviews?\s*/\s*(?:person|visit)|"
                        r"\bp\d{2}\b|\bdistribution\b|\bbreakdown\b|\bby week\b|\bby day\b|"
                        r"\boutlier\b|\bskew\w*\b|\bpercentile\b", re.I)
HAS_COVERAGE = re.compile(r"\breport(?:s|ed|ing)?\s+(?:no\s+)?(?:views?|impressions?|none)\b|"
                          r"\bnull\b|\bdoes not (?:report|publish|expose)\b|\bno views? (?:are )?"
                          r"published\b|\bonly platform\b|\bnot reported\b", re.I)
PLATFORM = re.compile(
    r"\b(threads|bluesky|linkedin|youtube|facebook|reddit|hacker ?news|"
    r"instagram|tiktok|mastodon|x\b|twitter)\b", re.I)

FENCE = re.compile(r"```.*?```", re.S)


def scan(reply):
    """Return [(kind, explanation)]. An empty list means the reply is clean."""
    text = FENCE.sub(" ", reply or "")
    problems = []
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n(?=[^\s|])", text) if s.strip()]
    agg = [s for s in sentences if AGGREGATE.search(s) and TRAFFIC_CTX.search(s)]
    if not agg:
        return problems
    if not HAS_WINDOW.search(text):
        problems.append(("WINDOW", "No time window and no by-week or by-day breakdown. A long-window "
                                   "total can hide that most of it landed in one short burst."))
    if not HAS_N.search(text):
        problems.append(("N", "No sample size. A large ratio over a handful of posts is not a trend."))
    if not HAS_SPREAD.search(text):
        problems.append(("SPREAD", "No median, per-person ratio or distribution. One outlier can carry "
                                   "a mean, and one view per visitor with no returns often means a crawler."))
    sup = [s for s in agg if SUPERLATIVE.search(s)]
    if sup and not HAS_COVERAGE.search(text):
        if len({m.group(1).lower() for m in PLATFORM.finditer(text)}) >= 2:
            problems.append(("COVERAGE", "The reply compares platforms without saying which ones report "
                                         "this metric and which return nothing."))
    return problems
