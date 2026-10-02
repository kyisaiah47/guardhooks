#!/usr/bin/env python3
"""SessionStart: add the contents of <config>/hard-rules.md to the model's context.

The logic lives in lib/hard_rules.py. This file only names the event.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

try:
    import hard_rules
except Exception:
    sys.exit(0)

if __name__ == "__main__":
    hard_rules.run("SessionStart")
