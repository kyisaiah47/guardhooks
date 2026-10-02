#!/usr/bin/env python3
"""UserPromptSubmit: when a prompt points at something that already exists, remind the model to
use exactly that thing.

"Use these", "run it on 2 and 3", "the ones I picked", "the originals" and a literal file name all
name existing inputs. The reminder appears only on those prompts, so it costs nothing elsewhere.
The patterns are shared with no-silent-substitution and substitution-disclosure-stop.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import guardhooks_core as G
    import substitution as L
except Exception:
    sys.exit(0)


def main():
    ev = G.read_event()
    if not ev:
        return
    named = L.names_existing_artifact(str(ev.get("prompt") or ""))
    if not named:
        return
    G.context(
        "This prompt names something that already exists (matched on %r).\n"
        "Do what was asked, with exactly the inputs that were named.\n\n"
        "1. Use the named thing: that exact file, image, prompt, spec, component or string.\n"
        "   Do not use a fresh one, a better one, or one rebuilt from a description of it.\n"
        "   If it is hard to find, find it.\n"
        "2. Deliver that first, even if you can see a problem with the result.\n"
        "3. After that, offer any alternative as a question. Never ship the alternative in place of the answer.\n"
        "4. If the request cannot be done with the named inputs, say so first in one plain sentence and ask.\n"
        "   An impossibility is a question for the user. It is not permission to pick a different input.\n"
        "5. If something the user saw or approved is not what ended up used, say that in the first sentence\n"
        "   of the reply, in plain words: \"I did not use the image you looked at; this is a new one.\"\n"
        "   Do not describe it as regenerated, re-ran, reformatted, rebuilt, refreshed, reprocessed or\n"
        "   \"at native size\". Each of those reads as a conversion of the thing the user named.\n\n"
        "Running a generator again with the same prompt makes new output. It does not reformat the old one."
        % named
    )


if __name__ == "__main__":
    main()
