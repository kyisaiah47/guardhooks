#!/usr/bin/env python3
"""Fixtures for no-purchase.py. Each case runs the real hook with a real PreToolUse event."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

t = T("no-purchase")

# must deny: purchase-shaped tool names, bare and as MCP tools
for name in ("buy_domain", "mcp__vercel__buy_domain", "mcp__vercel__buy_domains", "mcp__vercel__buy_single_domain",
             "mcp__vercel__buy_pro", "mcp__vercel__buy_credits", "mcp__vercel__buy_credits_endpoint",
             "mcp__vercel__buy_addon", "mcp__shop__checkout", "mcp__billing__subscribe_team",
             "mcp__billing__add_payment_method", "mcp__billing__upgrade_plan"):
    t.pre("deny tool %s" % name, name, {"name": "example.dev"}, "deny")

# must deny: shell commands that complete a purchase
t.pre("deny: vercel domains buy", "Bash", {"command": "vercel domains buy example.dev"}, "deny")
t.pre("deny: gcloud domains register", "Bash",
      {"command": "gcloud domains registrations register example.dev --yes"}, "deny")
t.pre("deny: aws route53 domain purchase", "Bash",
      {"command": "aws route53domains register-domain --domain-name example.dev purchase"}, "deny")
t.pre("deny: a confirmed renew flag", "Bash", {"command": "registrar renew example.dev --yes"}, "deny")
t.pre("deny: a live-mode Stripe subscription", "Bash",
      {"command": "stripe subscriptions create --customer cus_1 --price price_1 --live"}, "deny")

# must allow: reading price and availability
for name in ("check_domain_availability_and_price", "mcp__vercel__get_domain_price",
             "mcp__vercel__get_purchase_quote", "mcp__vercel__get_bulk_availability", "mcp__vercel__get_project"):
    t.pre("allow read %s" % name, name, {"name": "example.dev"}, "allow")

# must allow: ordinary tools and commands
t.pre("allow: whois lookup", "Bash", {"command": "whois example.dev"}, "allow")
t.pre("allow: vercel domains inspect", "Bash", {"command": "vercel domains inspect example.dev"}, "allow")
t.pre("allow: a test-mode Stripe charge", "Bash",
      {"command": "stripe payment_intents create --amount 500 --currency usd"}, "allow")
t.pre("allow: an ordinary command", "Bash", {"command": "npm test && git status"}, "allow")
t.pre("allow: a doc that names a registrar command", "Write",
      {"file_path": "/tmp/p/docs/domains.md", "content": "The user runs vercel domains buy by hand."}, "allow")
t.pre("allow: the hook's own files in a command", "Bash",
      {"command": "python3 src/hooks/no-purchase.py < /tmp/p/event.json"}, "allow")
t.pre("allow: Read", "Read", {"file_path": "/tmp/p/a.md"}, "allow")

reason = t.pre("deny message states the rule", "mcp__vercel__buy_domain", {"name": "example.dev"}, "deny")
t.check("message says the user buys by hand and price reads are allowed",
        "by hand" in reason and "Reading availability and price is always allowed" in reason)

t.done()
