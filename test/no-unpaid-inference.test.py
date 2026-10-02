#!/usr/bin/env python3
"""Fixtures for no-unpaid-inference.py. Each case runs the real hook with a real PreToolUse event.

Host names and key variable names are built from fragments, so this file never carries a spending
call or a key read in a form another tool would act on.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import T  # noqa: E402

A = "api.anthropic" + ".com"
O = "api.openai" + ".com"
ENV_ANTHROPIC = "process.env." + "ANTHROPIC" + "_API_KEY"

t = T("no-unpaid-inference")

DENY = [
    ("curl POST to anthropic messages", "Bash", {
        "command": "curl -s https://%s/v1/messages -H \"x-api-key: $K\" -d '{\"model\":\"m\"}'" % A}),
    ("curl POST to openai chat completions", "Bash", {
        "command": "curl -s https://%s/v1/chat/completions -d '{\"model\":\"m\"}'" % O}),
    ("openai embeddings", "Bash", {"command": "curl -X POST https://%s/v1/embeddings -u \"$K:\"" % O}),
    ("anthropic batches", "Bash", {"command": "curl https://%s/v1/messages/batches -d @batch.json" % A}),
    ("openai files upload", "Bash", {"command": "curl https://%s/v1/files -F purpose=batch -F file=@a.jsonl" % O}),
    ("host named with a body but no path", "Bash", {"command": "curl -X POST https://%s/ -d \"{}\"" % A}),
    ("inline node SDK spend", "Bash", {
        "command": "node -e 'const a=new Anthropic();a.messages.create({model:\"x\"})'"}),
    ("inline python SDK spend", "Bash", {
        "command": "python3 -c \"import anthropic; anthropic.Anthropic().messages.create(model=1)\""}),
    ("python heredoc openai spend", "Bash", {
        "command": "python3 - <<PY\nfrom openai import OpenAI\nOpenAI().chat.completions.create(model=\"x\")\nPY"}),
    ("WebFetch a spending endpoint", "WebFetch", {"url": "https://%s/v1/messages" % A, "prompt": "check it"}),
    ("model call written into a test file", "Write", {
        "file_path": "/tmp/p/app/src/lib/__tests__/inference.test.ts",
        "content": "const r = await client.messages.create({ model: \"m\" });"}),
    ("model call written into a smoke script", "Write", {
        "file_path": "/tmp/p/app/scripts/smoke/warm.ts",
        "content": "await openai.chat.completions.create({ model: \"m\" })"}),
    ("model call written into a CI workflow", "Write", {
        "file_path": "/tmp/p/app/.github/workflows/eval.yml",
        "content": "run: curl https://%s/v1/messages -d @p.json" % A}),
    ("model call written into a launchd plist", "Write", {
        "file_path": "/tmp/p/Library/LaunchAgents/com.example.warmup.plist",
        "content": "<string>curl https://%s/v1/chat/completions -d @p.json</string>" % O}),
    ("model call written into an eval fixture", "Write", {
        "file_path": "/tmp/p/app/evals/fixtures/run.py",
        "content": "client.messages.create(model=\"m\")"}),
    ("MultiEdit adding a spend to a spec file", "MultiEdit", {
        "file_path": "/tmp/p/app/src/a.spec.ts",
        "edits": [{"old_string": "x", "new_string": "await ai.responses.create({model:\"m\"})"}]}),
]

ALLOW = [
    ("GET /v1/models on anthropic", "Bash", {"command": "curl -s https://%s/v1/models -H \"x-api-key: $K\"" % A}),
    ("GET /v1/models on openai", "Bash", {"command": "curl -s https://%s/v1/models -u \"$K:\"" % O}),
    ("reading an error body from a models call", "Bash", {
        "command": "curl -s -o /tmp/err.json -w \"%%{http_code}\" https://%s/v1/models" % O}),
    ("editing a product's Claude driver", "Write", {
        "file_path": "/tmp/p/app/packages/integrations/src/drivers/inference/claude.ts",
        "content": "const DEFAULT_MODEL = \"m\";\nimport Anthropic from \"@anthropic-ai/sdk\";"}),
    ("editing a product's OpenAI driver", "Write", {
        "file_path": "/tmp/p/app/packages/integrations/src/drivers/inference/openai.ts",
        "content": "const API_URL = \"https://%s/v1/chat/completions\";" % O}),
    ("a product route behind an entitlement check", "Write", {
        "file_path": "/tmp/p/app/src/app/api/draft/route.ts",
        "content": ("const access = await requirePaid(userId);\n"
                    "if (!access.allowed) return Response.json(access, { status: 402 });\n"
                    "const out = await inference.text({ prompt });")}),
    ("a test that exercises the stub", "Write", {
        "file_path": "/tmp/p/app/src/lib/__tests__/stub.test.ts",
        "content": ("delete %s;\n" % ENV_ANTHROPIC +
                    "expect(driver.isConfigured()).toBe(false);\n"
                    "expect((await driver.text(p)).status).toBe(\"stub\");")}),
    ("a doc quoting the banned command in a fence", "Write", {
        "file_path": "/tmp/p/app/docs/keys.md",
        "content": "Never run this:\n\n```\ncurl -X POST https://%s/v1/messages -d @p.json\n```\n" % A}),
    ("a doc quoting the banned command in backticks", "Write", {
        "file_path": "/tmp/p/app/docs/keys.md",
        "content": "The line `curl -X POST https://%s/v1/messages -d @p.json` spends money.\n" % A}),
    ("an ordinary bash command", "Bash", {"command": "ls -la /tmp/p"}),
    ("gemini free tier by curl", "Bash", {
        "command": "curl -s \"https://generativelanguage.googleapis.com/v1beta/models/"
                   "gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY\" -d @p.json"}),
    ("gemini free tier through the OpenAI SDK baseURL", "Bash", {
        "command": "node -e 'const c=new OpenAI({baseURL:\"https://generativelanguage."
                   "googleapis.com/v1beta/openai/\",apiKey:process.env.GEMINI_API_KEY});"
                   "c.chat.completions.create({model:\"gemini-2.5-flash\"})'"}),
    ("a local model through the OpenAI SDK baseURL", "Bash", {
        "command": "node -e 'const c=new OpenAI({baseURL:\"http://localhost:11434/v1\"});"
                   "c.chat.completions.create({model:\"local\"})'"}),
    ("a subscription CLI in print mode", "Bash", {"command": "claude -p \"summarise this diff\""}),
    ("a test file that calls the gemini free tier", "Write", {
        "file_path": "/tmp/p/app/evals/fixtures/run.py",
        "content": ("import os\nkey = os.environ[\"GEMINI_API_KEY\"]\n"
                    "client.chat.completions.create(model=\"gemini-2.5-flash\")")}),
    ("the ban's own pattern library", "Write", {
        "file_path": "/tmp/p/hooks/lib/paid_inference.py",
        "content": "SPEND = \"https://%s/v1/messages\"" % A}),
    ("a CLAUDE.md rules file", "Write", {
        "file_path": "/tmp/p/app/CLAUDE.md",
        "content": "Never run curl -X POST https://%s/v1/messages -d @p.json in tests.\n" % A}),
]

for name, tool, ti in DENY:
    t.pre("deny: " + name, tool, ti, "deny")
for name, tool, ti in ALLOW:
    t.pre("allow: " + name, tool, ti, "allow")

reason = t.pre("deny message states the rule and the free moves", "Bash",
               {"command": "curl -s https://%s/v1/messages -d @p.json" % A}, "deny")
t.check("message names GET /v1/models and the quoting carve",
        "GET /v1/models" in reason and "blockquote" in reason and "paying customers" in reason)

t.done()
