"""An outcome may not be stated as fact unless this session observed it.

Read by no-unobserved-outcome-stop.py.

The failure this catches: the session verifies an input (a redirect resolves, a deploy exits 0, a
config value is set) and then states an outcome in the same confident voice ("the card renders
correctly", "it is live"). Every fact behind the sentence can be true while the outcome is false,
because the outcome lives on someone else's screen or someone else's server.

A sentence is checked only when it carries BOTH:
  (a) a RESULT verb: an achieved state such as renders correctly, now shows, is fixed, is live,
      went live, landed on, I verified, it confirmed; and
  (b) a subject whose truth lives outside this process: pixels (VISUAL) or another system's
      answer (EXTERNAL).

"The tests pass", "committed and pushed" and "the file now contains X" are not checked. Their
evidence is printed in the same turn by the test runner, git or the edit itself.

What counts as observing it, in this turn and on the reply's own chain (a subagent's evidence is
never this session's evidence):
  VISUAL    an image read back as an image (a screenshot or a browser capture) that this turn did
            not compose itself with an image library. When the sentence names a surface (a
            domain, or a platform such as GitHub or X), the capture must be of that surface.
            An image the user pasted in this turn also counts.
  EXTERNAL  a probe of that system: curl, wget, a fetch tool or a driven browser. When the
            sentence names a surface, the probe must reach that host.

A sentence written as a prediction ("should render", "unverified", "I have not checked") is never
checked. Quoted material in code, backticks, blockquotes or double quotes is never checked.
"""
import json
import os
import re

MAX_FLAG = 6

# ---------------------------------------------------------------------------------------------
# masking: quoted, fenced and blockquoted text is reported, not asserted
# ---------------------------------------------------------------------------------------------
_FENCE = re.compile(r"```.*?```", re.S)
_INLINE = re.compile(r"`[^`\n]*`")
_DQUOTE = re.compile("[“\"][^“”\"\n]{0,400}[”\"]")
_BLOCKQUOTE = re.compile(r"^\s*>.*$", re.M)
# A file name is not a platform: "fixed tools/deploy-token.mjs" is a local edit.
_FILEPATH = re.compile(r"(?<!:)\b[\w.~-]*/[\w./~-]+")
_FILENAME = re.compile(
    r"\b[\w.-]+\.(?:mjs|cjs|js|ts|tsx|jsx|py|sh|rb|go|rs|json|ya?ml|toml|css|scss|md|txt|"
    r"log|sql|env|lock)\b", re.I)
# A JSON fragment pasted into a reply claims nothing.
DATA_SHAPED = re.compile(r'^\s*[\{\[\]]|"\s*:\s*|^\s*[\w-]+\s*:\s*[\{\["]')


def mask(text):
    t = _FENCE.sub(" ", text or "")
    t = _BLOCKQUOTE.sub(" ", t)
    t = _INLINE.sub(" ", t)
    t = _DQUOTE.sub(" ", t)
    t = _FILEPATH.sub(" ", t)
    t = _FILENAME.sub(" ", t)
    return t


def sentences(text):
    out = []
    for chunk in re.split(r"\n+", mask(text)):
        chunk = chunk.strip()
        if not chunk:
            continue
        for s in re.split(r"(?<=[.!?])\s+", chunk):
            s = s.strip()
            if s and not DATA_SHAPED.search(s):
                out.append(s)
    return out


# ---------------------------------------------------------------------------------------------
# (a) the RESULT verb
# ---------------------------------------------------------------------------------------------
RESULT = re.compile(
    r"(?<![-\w])("
    # "render" is usually a noun, so only the finite verb with a subject in front counts.
    r"(?:the|this|that|it|which)\s+(?:[\w-]+\s+){0,3}renders\b|"
    r"renders\s+(?:correctly|right|fine|clean|properly)|"
    r"rendered\s+(?:correctly|right|fine|clean|properly)|rendering\s+correctly|"
    r"displays\b|displayed|displaying|"
    r"now\s+shows|shows\s+(?:the|correctly)|showing\s+(?:the|correctly)|"
    r"is\s+(?:now\s+)?(?:fixed|correct|live|up|working)|"
    r"are\s+(?:now\s+)?(?:fixed|correct|live|up|working)|"
    r"(?:works|working)\s+now|now\s+works|"
    r"went\s+live|is\s+live|"
    r"landed\s+(?:on|in|at)|lands\s+on|unfurls\b|unfurled|re-?crawle[ds]|re-?crawls\b|"
    r"picked\s+it\s+up|"
    r"came\s+back\s+(?:correct|clean|right|green|fine|good)|"
    r"looks\s+(?:right|correct|as\s+expected)|"
    # a bare "verified" is a label; the claim needs an actor or an object
    r"(?:I|we|it|that|this|he|she|they)\s+(?:confirmed|verified|validated)\b|"
    r"(?:confirmed|verified|validated)\s+(?:it|the|that|this)\b|"
    r"proved|proven|"
    r"no\s+longer\s+(?:shows|broken|wrong|stale)|"
    r"fixed\s+(?:it|the|this|that|its|their|both|all)\b"
    r")(?![-\w])", re.I)

# ---------------------------------------------------------------------------------------------
# (b) subjects whose truth is pixels, or another system's answer
# ---------------------------------------------------------------------------------------------
VISUAL = re.compile(
    r"\b("
    r"share\s+card|og\s+(?:card|image|tag)|card|preview|unfurl|thumbnail|screenshot|"
    r"render|artwork|image|photo|tile|banner|poster|cover|"
    r"logo|mark|favicon|icon|glyph|"
    r"layout|design|typography|spacing|alignment|colou?rs?|font|"
    r"the\s+ui|the\s+page|the\s+site|the\s+landing|the\s+hero|the\s+modal|the\s+carousel|"
    r"the\s+composer|the\s+frame|the\s+shot|the\s+slide|the\s+deck|"
    r"video|film|clip|chart|diagram|graphic|infographic|pdf|"
    r"looks|appearance|visually|on\s+screen|in\s+the\s+browser"
    r")\b", re.I)

EXTERNAL = re.compile(
    r"\b("
    r"live|deployed|production|prod|in\s+prod|"
    r"the\s+(?:post|tweet|reply|thread|comment|listing|entry|email|dm)|"
    r"posted|published|shipped|"
    r"x\.com|twitter|linkedin|bluesky|threads|reddit|facebook|instagram|youtube|mastodon|"
    r"vercel|netlify|supabase|stripe|notion|cloudflare|github|"
    r"crawler|crawl|cache|cdn|redirect|dns|endpoint|the\s+api|webhook|"
    r"the\s+url|the\s+domain|the\s+subdomain|the\s+link"
    r")\b", re.I)

# a sentence that is honestly a prediction is never checked
HEDGE = re.compile(
    r"\b("
    r"should|shall|will\s+(?:be|land|show|render|get|pick)|would|ought|"
    r"expect|expects?d?|anticipate|predict|presumably|likely|probably|in\s+theory|"
    r"in\s+principle|the\s+mechanism|mechanically|means\s+it|implies|"
    r"unverified|unconfirmed|untested|not\s+yet\s+(?:seen|checked|verified|looked|observed)|"
    r"have\s+not\s+(?:seen|looked|checked|opened|verified)|"
    r"haven\Wt\s+(?:seen|looked|checked|opened|verified)|"
    r"did\s+not\s+(?:look|check|open|see)|didn\Wt\s+(?:look|check|open|see)|"
    r"no\s+screenshot|cannot\s+confirm|can\Wt\s+confirm|assume|assuming|"
    r"needs?\s+(?:checking|verifying|a\s+look)|to\s+be\s+(?:confirmed|verified)|"
    r"claims?\s+to|supposed\s+to|"
    r"usually|typically|generally|often|always|anyone|everyone|nobody|no\s+one|"
    r"never|people\s+\w+|tends?\s+to|the\s+kind\s+of"
    r")\b", re.I)
LEADING_CONDITIONAL = re.compile(r"^\s*(?:-\s*)?(?:if|once|when|unless|assuming)\b", re.I)

# someone else's observation reported as this session's
RELAY = re.compile(
    r"\b("
    r"(?:sub-?agent|the\s+agent|an\s+agent|another\s+agent|the\s+fork|the\s+worker|"
    r"the\s+task|the\s+report|its\s+report|the\s+summary|the\s+subagent)"
    r"[^.!?]{0,80}?"
    r"(?:confirmed|verified|reported|said|says|found|checked|proved|observed|looked|"
    r"came\s+back|tells?\s+me|told\s+me)"
    r"|(?:according\s+to|per)\s+the\s+(?:agent|report|subagent|summary|task)"
    r"|it\s+confirmed|it\s+verified|it\s+reported"
    r")", re.I)


def flag(text):
    """[(sentence, tier, relayed)]: the sentences that assert an outcome."""
    out = []
    for s in sentences(text):
        if LEADING_CONDITIONAL.search(s) or HEDGE.search(s):
            continue
        if not RESULT.search(s):
            continue
        tier = "visual" if VISUAL.search(s) else ("external" if EXTERNAL.search(s) else None)
        if not tier:
            continue
        out.append((s, tier, bool(RELAY.search(s))))
    return out


# ---------------------------------------------------------------------------------------------
# the surface a sentence names
# ---------------------------------------------------------------------------------------------
SURFACE_HOSTS = {
    "google": "google.com", "serp": "google.com", "search result": "google.com",
    "search results": "google.com", "google search": "google.com", "search console": "google.com",
    "x.com": "x.com", "twitter": "x.com", "the tweet": "x.com",
    "linkedin": "linkedin.com", "bluesky": "bsky.app", "bsky": "bsky.app",
    "threads": "threads.net", "reddit": "reddit.com", "facebook": "facebook.com",
    "instagram": "instagram.com", "youtube": "youtube.com", "mastodon": "mastodon",
    "stripe": "stripe.com", "vercel": "vercel.com", "netlify": "netlify.com",
    "supabase": "supabase.com", "github": "github.com",
}
_SURFACE_WORD = re.compile(
    r"\b(google\s+search|search\s+results?|search\s+console|google|serp|"
    r"x\.com|twitter|the\s+tweet|linkedin|bluesky|bsky|threads|reddit|"
    r"facebook|instagram|youtube|mastodon|stripe|vercel|netlify|supabase|github)\b", re.I)
_BARE_HOST = re.compile(
    r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|dev|io|app|net|org|ai|co|so|sh|"
    r"page|site|xyz|me|tech))\b", re.I)


def claimed_surfaces(sentence):
    """The external surfaces a sentence names, as hosts. Empty means no surface is named."""
    out = set()
    for m in _SURFACE_WORD.finditer(sentence or ""):
        key = re.sub(r"\s+", " ", m.group(1).strip().lower())
        out.add(SURFACE_HOSTS.get(key) or SURFACE_HOSTS.get(key.replace("the ", ""), key))
    for m in _BARE_HOST.finditer(sentence or ""):
        out.add(m.group(1).lower())
    return out


def _host_matches(h, w):
    if "." not in w:
        return w in h
    return h == w or h.endswith("." + w)


# ---------------------------------------------------------------------------------------------
# evidence in the transcript
# ---------------------------------------------------------------------------------------------
CAPTURE_CMD = re.compile(
    r"("
    r"screencapture|screen\s*recording|"
    r"page\.screenshot|\.screenshot\s*\(|captureScreenshot|captureBeyondViewport|"
    r"recordVideo|--record-video|record_video_dir|startScreencast|screencast|asciinema|"
    r"[\w./-]*(?:shot|screenshot|capture|record)[\w./-]*\.(?:mjs|cjs|js|py|sh)\b|"
    r"scrot|import\s+-window|gnome-screenshot|"
    r"ffmpeg[^\n]*-f\s+(?:avfoundation|x11grab|gdigrab)|"
    r"--screenshot|takeScreenshot"
    r")", re.I)

COMPOSE_CMD = re.compile(
    r"("
    r"from\s+PIL|PIL\.Image|Image\.new|ImageDraw|ImageFont|Image\.open|"
    r"\.paste\s*\(|\.thumbnail\s*\(|\.crop\s*\(|\.resize\s*\(|"
    r"\bmagick\b|\bmontage\b|\bcomposite\b|convert\s+[-\w./]+\.(?:png|jpe?g|webp)|"
    r"sharp\s*\(|createCanvas|node-canvas|canvas\.toBuffer|ctx\.drawImage|"
    r"contact[\s-]*sheet|svg2png|rsvg-convert|cairosvg|"
    r"\bcv2\.|import\s+cv2|opencv|"
    r"matplotlib|plt\.savefig|pyplot|seaborn|plotly\.|kaleido|"
    r"renderToStaticMarkup|renderToString|\bsatori\b|@vercel/og|resvg|"
    r"base64\.b64decode|Buffer\.from\([^)]*base64|atob\(|"
    r"\bJimp\b|wkhtmltoimage|svgwrite|reportlab|"
    r"Image\.fromarray|imwrite\(|"
    r"ffmpeg[^\n]*(?:-filter_complex|hstack|vstack|overlay=|drawtext)"
    r")", re.I)

PROBE_CMD = re.compile(
    r"\b(curl|wget|httpie|http\s+(?:get|head)|dig|nslookup|host\s+\S+\.|openssl\s+s_client|"
    r"playwright|puppeteer|gh\s+api|lighthouse)\b", re.I)
PROBE_TOOL = re.compile(r"WebFetch|WebSearch|browser|navigate|playwright|puppeteer|chrome", re.I)
BROWSER_SHOT_TOOL = re.compile(r"screenshot|computer|gif_creator|take_snapshot", re.I)

_ANYURL = re.compile(r"(?:https?://|file://)[^\s'\"\\)<>,;]+", re.I)
_IMGPATH = re.compile(r"[\w./~$%{}+-]*\.(?:png|jpe?g|webp|avif|gif|mp4|webm|mov)\b", re.I)


def _host(url):
    u = re.sub(r"^https?://(?:www\.)?", "", url, flags=re.I)
    return u.split("/")[0].split(":")[0].lower()


def _base(p):
    return os.path.basename((p or "").strip().strip("'\"").rstrip(","))


def _text_of(msg):
    c = (msg or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def read_turn(transcript_path):
    """Everything the check needs about the current turn, from the transcript alone.

    Rows on a different chain from the reply (a subagent's sidechain) are ignored: a subagent's
    screenshot is not this session's observation.
    """
    ev = {"reply": "", "images": 0, "pasted": 0, "probe": False, "probe_hosts": set(),
          "seen": [], "produced": {}}
    rows = []
    try:
        with open(transcript_path, encoding="utf-8", errors="ignore") as fh:
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
                raw = json.dumps(content) if content is not None else ""
                side = bool(d.get("isSidechain"))
                if role == "user":
                    t = _text_of(m)
                    is_result = ("tool_use_id" in raw[:400]) or ("tool_result" in raw[:400])
                    if t.strip() and not is_result and not d.get("isMeta") and not side:
                        rows = []
                rows.append((role, raw, side, m))
    except Exception:
        return ev

    chain = False
    for role, raw, side, m in reversed(rows):
        if role == "assistant" and _text_of(m).strip():
            ev["reply"] = _text_of(m)
            chain = side
            break

    produced = ev["produced"]
    state = {"pending": None, "nav": []}

    def classify(cmdtext, tool_name):
        paths = [p for p in _IMGPATH.findall(cmdtext) if len(p) > 4]
        urls = _ANYURL.findall(cmdtext)
        is_cap = bool(CAPTURE_CMD.search(cmdtext))
        is_comp = bool(COMPOSE_CMD.search(cmdtext))
        if not paths or not (is_cap or is_comp):
            return
        subjects = []
        for u in urls:
            subjects.append("file:" + _base(u[7:]) if u.lower().startswith("file://") else _host(u))
        if is_cap and not subjects and state["nav"]:
            subjects = list(state["nav"])
        if is_comp and not is_cap:
            # a crop of a real capture is still a photograph of the real thing
            inherited = [produced[_base(p)] for p in paths
                         if produced.get(_base(p), {}).get("kind") == "capture"]
            if inherited:
                kind = "capture"
                subjects = sorted({s for r in inherited for s in r["subjects"]})
            else:
                kind = "composed"
        else:
            kind = "capture"
        for p in paths:
            produced[_base(p)] = {"kind": kind, "subjects": subjects, "path": p}

    for role, raw, side, m in rows:
        if side != chain:
            continue
        has_img = '"type": "image"' in raw or '"type":"image"' in raw
        if role == "user":
            is_result = ("tool_use_id" in raw[:400]) or ("tool_result" in raw[:400])
            if has_img and is_result:
                ev["images"] += 1
                rec = {"kind": "unknown", "subjects": [], "path": ""}
                if state["pending"]:
                    rec = dict(produced.get(_base(state["pending"])) or rec)
                    rec["path"] = state["pending"]
                elif state["nav"]:
                    rec = {"kind": "capture", "subjects": list(state["nav"]), "path": "(browser tool)"}
                ev["seen"].append(rec)
                state["pending"] = None
            elif has_img:
                ev["pasted"] += 1
        elif role == "assistant":
            c = (m or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name = b.get("name") or ""
                data = b.get("input") or {}
                inp = json.dumps(data)
                fp = data.get("file_path") or data.get("path") or ""
                for u in _ANYURL.findall(inp):
                    if u.lower().startswith("file://"):
                        state["nav"] = ["file:" + _base(u[7:])]
                    else:
                        state["nav"] = [_host(u)]
                        ev["probe_hosts"].add(_host(u))
                if name == "Read" and isinstance(fp, str) and \
                        re.search(r"\.(png|jpe?g|webp|avif|gif)$", fp, re.I):
                    state["pending"] = fp
                elif BROWSER_SHOT_TOOL.search(name):
                    state["pending"] = None
                if PROBE_CMD.search(inp) or PROBE_TOOL.search(name):
                    ev["probe"] = True
                classify(inp, name)
    return ev


def qualifying(ev, sentence=None):
    """The images read back this turn that could settle this sentence."""
    wanted = claimed_surfaces(sentence or "")
    out = []
    for rec in ev.get("seen") or []:
        if rec.get("kind") == "composed":
            continue
        if wanted:
            if rec.get("kind") != "capture":
                continue
            if not any(_host_matches(s, w) for s in rec.get("subjects") or [] for w in wanted):
                continue
        out.append(rec)
    return out


def satisfied(tier, ev, sentence=None):
    """Did this session observe the thing the sentence talks about, in this turn?"""
    if ev.get("pasted", 0) > 0:
        return True
    if qualifying(ev, sentence):
        return True
    if tier == "visual":
        return False
    if not ev.get("probe"):
        return False
    wanted = claimed_surfaces(sentence or "")
    if not wanted:
        return True
    return any(_host_matches(h, w) for h in ev.get("probe_hosts") or set() for w in wanted)


def composed_only(ev):
    seen = ev.get("seen") or []
    return bool(seen) and all(r.get("kind") == "composed" for r in seen)
