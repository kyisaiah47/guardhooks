# GuardHooks

Pick the hooks you want; each installs on its own.

GuardHooks is a set of Claude Code hooks. Each hook stops one kind of bad output before it reaches a file, a shell command or a chat reply. You install a hook with one command, and you remove it with one command. No hook depends on another hook.

```sh
npx guardhooks list                 # every hook, what it blocks, and whether it is installed
npx guardhooks add no-em-dash       # install one hook
npx guardhooks add no-noise no-noise-stop
npx guardhooks remove no-em-dash    # uninstall it
npx guardhooks doc no-noise         # the full description of one hook
```

## What each hook does

- A hook on `PreToolUse` denies the tool call. Claude Code shows the model the reason, and the model writes the text again.
- A hook on `Stop` sends the reply back. The model rewrites the reply before the turn ends. A Stop hook blocks at most once per turn, so it can never trap the model in a loop.
- A hook on `UserPromptSubmit` adds a short note next to your prompt. It never blocks anything.
- A write hook scans only the new text: Write content, Edit new strings and Bash commands. Text that is already in a file is never scanned, and reading a file is never blocked.
- A text hook skips quoted material. A fenced code block, an inline backtick span or a `>` blockquote can reproduce a banned phrase byte for byte. Each hook's description says how to quote on purpose.
- A hook that cannot load its own files, or cannot parse its input, exits quietly. A broken guard never blocks your work.

## Hooks

<!-- hooks-table:start -->
| Hook | Runs on | What it blocks or adds |
|---|---|---|
| `agent-status-must-be-measured` | UserPromptSubmit | When the user asks about a subagent, reminds the model to check the agent's real status instead of narrating its brief. |
| `aggregate-composition-stop` | Stop | Sends a reply back when it reports a traffic, reach or engagement number without sample size, time window and spread. |
| `approval-lock-inject` | UserPromptSubmit | When a prompt asks to deploy, publish or use an approved artifact, reminds the model to ship those exact bytes unchanged. |
| `batch-tools-guard` | PreToolUse | After twelve tool calls in a row that each went alone in their own request, reminds the model to batch independent calls. |
| `block-skill-install` | PreToolUse | Denies direct skill and plugin install commands so nothing lands in a skills folder unscanned. |
| `block-workflow-fanout` | PreToolUse | Denies the Workflow tool, so a request for research never starts a multi-agent run without an explicit yes. |
| `clock-truth-inject` | UserPromptSubmit | Adds the real wall-clock time to every prompt, with a note that it goes stale and must be read again. |
| `inject-hard-rules` | SessionStart, SubagentStart | Adds your own short rules file (&lt;config&gt;/hard-rules.md) to every session start, resume, compaction and subagent start. |
| `instruction-match` | PreToolUse | Denies a file write or agent brief whose verb contradicts what the user asked for on the same object, such as editing a deck the user asked to create. |
| `instructions-loaded-log` | InstructionsLoaded | Logs every instruction file Claude Code loads (CLAUDE.md and others), so you can check whether a rule was in context. |
| `mobile-screenshot-guard` | PreToolUse | Blocks phone-width screenshots of a site; captures of a product or site are desktop width. |
| `named-artifact-guard` | UserPromptSubmit | When a prompt names existing files or picks ("use these", "2 and 3", a file name), reminds the model to use exactly those. |
| `no-claude-p-stop` | Stop | Sends a chat reply back for a rewrite when it plans a headless Claude CLI call instead of the CLI you chose. |
| `no-claude-p` | PreToolUse | Routes headless model calls through the CLI you chose by blocking headless Claude CLI calls (claude -p, claude --print, a spawn of the claude binary) in files and shell commands. |
| `no-em-dash-stop` | Stop | Sends a chat reply back for a rewrite when it contains an em dash or an en dash. |
| `no-em-dash` | PreToolUse | Blocks em dashes, en dashes and `' -- '` used as a dash in any file write or shell command. |
| `no-half-width-block` | PreToolUse | Blocks a CSS rule that puts a ch or em reading measure on an element that also paints a background. |
| `no-heading-break` | PreToolUse | Blocks hard &lt;br&gt; line breaks inside a headline, title or &lt;h1&gt;. |
| `no-invented-clock-stop` | Stop | Sends a reply back when it states the current time, or minutes left, without a fresh clock reading. |
| `no-left-accent` | PreToolUse | Blocks one-sided accent borders: a 2px or wider coloured stripe on one edge of a card or row. |
| `no-lenis-scroll-trap` | PreToolUse | Blocks Lenis smooth-scroll mounts that lack allowNestedScroll: true, which freezes inner scroll boxes. |
| `no-noise-stop` | Stop | Sends a chat reply back for a rewrite when it announces honesty, hedges a no, or narrates the answer instead of giving it. |
| `no-noise` | PreToolUse | Blocks filler phrases in product copy and hedging phrases in prompts and answer templates, such as "seamlessly", "designed to", "to be honest" and "not my strongest area". |
| `no-parallel-repo-fanout` | PreToolUse | Denies shell loops that push, install, build or deploy many repos at once in the background. |
| `no-prose-stop` | Stop | Sends a chat reply back for a rewrite when it puts a caption in front of a link or a label where a sentence belongs. |
| `no-prose` | PreToolUse | Blocks prose shapes in product copy and answer templates, such as a caption in front of a link, a price with no payer, or "under the hood". |
| `no-purchase-suggestion-stop` | Stop | Sends a chat reply back for a rewrite when it offers to buy something, such as asking whether to grab the domain. |
| `no-purchase` | PreToolUse | Blocks any tool call or shell command that completes a purchase, such as an MCP buy_domain call, a registrar register command or a live-mode charge. |
| `no-reading-measure-cap` | PreToolUse | Blocks a reading-measure max-width (60 to 85ch, or a --measure variable) on content inside a stylesheet. |
| `no-retro-rerender-stop` | Stop | Sends a chat reply back for a rewrite when it offers or asks to redo already-shipped assets so they match a newer style. |
| `no-retro-rerender` | PreToolUse | Blocks code and commands that send already-shipped assets back through a generator so they match a newer style. |
| `no-silent-substitution` | PreToolUse | Denies the first generator command of a turn whose prompt named existing inputs, so new output is not passed off as the named thing. |
| `no-stat-eyebrow-inject` | UserPromptSubmit | Adds the stat-eyebrow rule to any prompt that asks for design work, before a layout is chosen. |
| `no-stat-eyebrow` | PreToolUse | Blocks the stat-eyebrow card: a giant number as the dominant type with a small all-caps tracked label beside it. |
| `no-sticky-column-divider` | PreToolUse | Blocks a left or right border drawn on a sticky column, where it stops short of the page. |
| `no-text-highlight` | PreToolUse | Blocks text-selection gestures (drag-select, double click, selectText) in screen-recording scripts. |
| `no-unobserved-outcome-stop` | Stop | Sends a reply back when it states a visual or external outcome (renders correctly, is live, the agent confirmed it) that the session never observed. |
| `no-unpaid-inference` | PreToolUse | Blocks any tool call that would spend a paid Anthropic or OpenAI API key outside a paying customer's request, such as a test, eval, demo or CI job. |
| `no-unsourced-claim-stop` | Stop | Sends a reply back when it quotes something the session never saw or names a home-directory path that does not exist. |
| `no-vercel-project-delete` | PreToolUse | Blocks any write or shell command that deletes a Vercel project, through the CLI or a REST DELETE. |
| `no-zoom-capture` | PreToolUse | Blocks animated zoom (Ken Burns, punch-in) on a captured page inside a screen-recording script. |
| `primary-source-guard` | UserPromptSubmit | On prompts that ask for something to be made or fixed, reminds the model to open the subject itself before working from a description of it. |
| `same-style-means-match-the-source` | UserPromptSubmit | When a prompt asks to match an existing artifact's style, adds a rule to work from its rendered frames. |
| `skill-scan` | PreToolUse | Scans a skill before a shell command copies it into a skills folder, and denies the copy when the scan finds a red flag. |
| `substitution-disclosure-stop` | Stop | Sends a reply back when a generator ran after the user named existing inputs and the reply does not say plainly whether those inputs were used. |
| `tone-guard-stop` | Stop | Sends a reply back for a rewrite when it comments on the user's tone instead of answering. |
| `tone-rule-inject` | UserPromptSubmit | Adds a short reminder to every prompt: answer what the user asks, never comment on how they ask it. |
| `txt-no-hardwrap` | PreToolUse | Blocks hard-wrapped paragraphs in .txt files, so the text pastes cleanly into email and forms. |
<!-- hooks-table:end -->

## Where the files go

- The config directory is `--config-dir DIR` when you pass it. Otherwise it is `$CLAUDE_CONFIG_DIR` when that is set, and `~/.claude` when it is not.
- `add` copies the hook's script into `<config>/hooks/guardhooks/`, together with the shared `lib/` folder. It then adds one entry per event to `<config>/settings.json`. Every other setting in that file is kept as it was.
- `remove` deletes the hook's entries and its script. When no GuardHooks hook is left, it deletes `<config>/hooks/guardhooks/` too.
- Running `add` twice for the same hook leaves one entry, not two.
- Hooks that keep state, such as a counter or a recorded exception, write it under `<config>/guardhooks/state/`.
- Restart Claude Code, or open `/hooks`, after an install so the new entries load.

## Exceptions

A few hooks accept a short-lived exception, because the thing they block is sometimes correct. Those hooks name the escape in their message:

```sh
npx guardhooks declare no-unsourced-claim-stop "the figure comes from a screenshot the user pasted"
```

A declaration lasts two hours. The reason must be a full sentence. Hooks without an escape have no flag that turns them off. To stop a hook, remove it with `npx guardhooks remove <hook>`.

A few hooks also read an optional file of your own patterns from `<config>/guardhooks/`. Each hook's description names its file.

## Requirements

- Node.js 18 or newer, for the installer.
- Python 3.8 or newer on your PATH as `python3`, for the hooks. Pass `--python <command>` to `add` to write a different command.
- No packages. GuardHooks has no dependencies.

## Hook reference

<!-- hooks-reference:start -->
### `agent-status-must-be-measured`

This UserPromptSubmit hook adds a reminder when a prompt asks what an agent is doing, how long it has run, or whether it is stuck or still running. The brief the model wrote for an agent describes planned work, and repeating it back reads like a status report while being wrong as soon as the agent finished or stalled. The reminder tells the model to check status with the agent tools, read live progress or ask the agent, never to time an agent from a file's modification time, to look for live processes when the user says something is still running, and to say plainly when it cannot establish a fact. It blocks nothing.

Runs on: UserPromptSubmit. Install: `npx guardhooks add agent-status-must-be-measured`.

### `aggregate-composition-stop`

This Stop hook blocks a reply that states a headline audience number (visitors, views, followers, clicks, sessions, an average or a multiple) in a traffic or platform context without saying how many samples it covers, over what time window, and how it is spread (a median, a per-person ratio or a breakdown). A ranking across two or more platforms must also say which platforms report the metric. A total can be correct while its meaning is false: one outlier can carry a mean, one week can carry a sixty-day total, and one view per visitor with no returns often means a crawler. Numbers inside fenced code blocks are ignored. When a number really needs no breakdown, npx guardhooks declare aggregate-composition-stop "&lt;reason&gt;" turns the hook off for two hours.

Runs on: Stop. Install: `npx guardhooks add aggregate-composition-stop`.

Escape: `npx guardhooks declare aggregate-composition-stop "<reason>"` records a two-hour exception.

### `approval-lock-inject`

This UserPromptSubmit hook adds a short rule to the context when the prompt contains a deploy word such as deploy, publish, upload, embed, ship or use the approved. An approved image, card or layout is the final input, not a reference for a new design pass. The rule says to find the exact approved source, use the same bytes, crop, dimensions, placement and CSS, avoid nearby visual changes, and ask one plain question first if the artifact cannot be delivered unchanged. It never blocks anything, and it stays silent on other prompts.

Runs on: UserPromptSubmit. Install: `npx guardhooks add approval-lock-inject`.

### `batch-tools-guard`

This PreToolUse hook counts consecutive tool calls that arrive alone. Every request re-sends the whole conversation, so a lone call costs the full context however small its result is, and two independent calls sent one after the other cost twice what they cost in one message. Calls in the same request reach the hook within milliseconds of each other, which resets the count. After twelve lone calls it adds a reminder to put independent calls in one message and chain related shell steps with &&. It never denies a call. Its counter lives in &lt;config&gt;/guardhooks/state/batch-tools-guard/.

Runs on: PreToolUse on `Bash\|Read\|Grep\|Glob`. Install: `npx guardhooks add batch-tools-guard`.

### `block-skill-install`

This PreToolUse hook denies shell commands that install a skill or plugin directly, such as the skills add and skills install commands of the skills CLI and the plugin install command of Claude Code. Community skills and plugins are untrusted input that runs with your local permissions and credentials. The denial explains the safe path: fetch the source into a scratch folder without running it, scan it with skill-scan (python3 skill-scan.py &lt;dir&gt;), then copy the folder into the skills folder by hand. Install skill-scan too if you want that copy checked automatically.

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add block-skill-install`.

### `block-workflow-fanout`

This hook denies every call to the Workflow tool. A user who asks for deep or thorough research wants a thorough answer, and a multi-agent run can spend a very large number of tokens before anyone sees a result. The deny message tells the model to read the primary sources itself, run a few targeted searches and write the answer out, and to ask with a cost estimate if the task really needs a fan-out. There is no escape flag. To allow the Workflow tool again, run npx guardhooks remove block-workflow-fanout.

Runs on: PreToolUse on `Workflow`. Install: `npx guardhooks add block-workflow-fanout`.

### `clock-truth-inject`

This UserPromptSubmit hook adds the current local date and time, read at the moment of the prompt, to the context the model sees. The model has no clock, and between readings it tends to estimate the time from how much work it has done, which can be wrong by a wide margin. The note tells the model that the reading is stale from then on, that tool calls are not a clock, and that it must run date again before it states the current time, the time left before a deadline, or the time elapsed. It never blocks anything. It pairs with no-invented-clock-stop, which checks the reply.

Runs on: UserPromptSubmit. Install: `npx guardhooks add clock-truth-inject`.

### `inject-hard-rules`

This hook reads hard-rules.md from your Claude Code config directory and adds it to the model's context at SessionStart (startup, resume, clear and compact) and at SubagentStart. Subagents such as Explore and Plan do not read the CLAUDE.md hierarchy, and user-level instructions can drop out of a long session at a compaction, so rules that must always hold need a second path in. Write the file yourself in plain statements and keep it under 9,200 characters, because Claude Code moves longer hook output to a file and the model only sees a preview. When the file is missing or empty the hook does nothing. It blocks nothing.

Runs on: SessionStart; SubagentStart. Install: `npx guardhooks add inject-hard-rules`.

### `instruction-match`

This PreToolUse hook reads the verb and the object from the user's last three prompts and from the action about to run: an Agent or Task brief, or a Write, Edit, MultiEdit or NotebookEdit. When both name the same object with conflicting verbs (create against edit, create against delete, edit against delete), it denies the call once and shows the two side by side. A file edit only counts when the user said that file already exists, because then it is the model to copy, not the thing to change. It carries no list of past failures, and with no shared object it stays silent. When the action really is what was asked, run npx guardhooks declare instruction-match "&lt;verb&gt; &lt;object&gt;, and why that is what was asked&gt;", which lasts two hours. A declaration whose own verb still contradicts the user's on that object is ignored.

Runs on: PreToolUse on `Agent\|Task\|Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add instruction-match`.

Escape: `npx guardhooks declare instruction-match "<reason>"` records a two-hour exception.

### `instructions-loaded-log`

This InstructionsLoaded hook appends one tab-separated line per loaded instruction file to &lt;config&gt;/guardhooks/state/instructions-loaded.log: the first eight characters of the session id, the file path, the load reason, the memory type and the UTC time. When a model seems to ignore a rule, the first question is whether the rule was loaded at all, and transcripts do not record the CLAUDE.md injection. Count sessions against loads of a given file to get its load rate. The log is trimmed to its last 10,000 lines once it passes 20,000. It prints nothing and blocks nothing.

Runs on: InstructionsLoaded. Install: `npx guardhooks add instructions-loaded-log`.

### `mobile-screenshot-guard`

This hook denies a Bash command or a file write that takes a phone-width photo of a site. It fires when three things appear together: a capture (a .screenshot() call, a screencast, `playwright screenshot`, `--screenshot`), a phone viewport (narrower than 600 CSS px, isMobile, a phone user agent or device, or a phone width on a capture flag), and a navigation to a real site. Phone photos of a desktop product make it look smaller and worse than it is, so captures should be 1280 CSS px wide or wider. Layout QA is allowed: files under qa, e2e, tests or gates folders and .test or .spec files may render at phone width, and so may a local file:// render. Automation that must emulate a phone to operate a third-party form can mark the line with the comment `phone-viewport: third-party form`.

Runs on: PreToolUse on `Bash\|Write\|Edit\|MultiEdit`. Install: `npx guardhooks add mobile-screenshot-guard`.

### `named-artifact-guard`

This UserPromptSubmit hook adds a short rule to the context when the prompt points at something that already exists: a number or ordinal for something the user was shown, a pointing word such as these or those, ownership such as the ones I picked, substitution words such as replacing or in place of, or a literal file name. The rule says to use exactly the named inputs, deliver that first, offer alternatives only as a question afterwards, say so first when the request cannot be done with those inputs, and put any substitution in the first sentence of the reply in plain words instead of calling it regenerated or reformatted. It never blocks anything, and it stays silent on prompts that name nothing. Your own patterns can go in &lt;config&gt;/guardhooks/named-artifact-patterns.txt, one regex per line.

Runs on: UserPromptSubmit. Install: `npx guardhooks add named-artifact-guard`.

### `no-claude-p-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when a sentence plans a headless Claude CLI call, such as running claude -p over each file or a headless Claude judge. The model then rewrites the reply with the CLI named in the GUARDHOOKS_HEADLESS_CLI environment variable. It pairs with no-claude-p, which covers files and shell commands. A sentence about the rule passes when it also says not, never, instead, replaced, legacy or reports an error, and a sentence that names the chosen CLI passes. To quote the command on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or a double-quoted span. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-claude-p-stop`.

### `no-claude-p`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call whose new text writes or runs a headless Claude CLI call: claude -p, claude --print, claude --model, a spawn of the claude binary, or the argv form ['claude', '-p', ...]. Use it when a project sends every scripted, non-interactive model call through one CLI, so cost, model choice and logging stay in one place. Set the GUARDHOOKS_HEADLESS_CLI environment variable (for example in the env block of settings.json) to the CLI you chose, and the deny message names it. An interactive Claude Code session is never affected, and CLAUDE.md and AGENTS.md are exempt. To quote the command on purpose in a doc, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or a double-quoted span of twelve characters or more. A Bash command is never treated as a quotation.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-claude-p`.

### `no-em-dash-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when it contains an em dash, an en dash, a horizontal bar, a minus sign, an escaped spelling of one, or `' -- '` used as a dash. The model then rewrites the reply with a period, a comma, a colon or parentheses. It pairs with no-em-dash, which covers files and shell commands. To quote text that really contains a dash, put it in a fenced code block, an inline backtick span or a '&gt;' blockquote. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-em-dash-stop`.

### `no-em-dash`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call when the new text contains an em dash (U+2014), an en dash (U+2013), a horizontal bar (U+2015), a minus sign (U+2212), an escaped spelling such as `\u2014` or `&mdash;`, or `' -- '` used as a dash in a prose file. Models reach for the em dash far more often than people do, and readers notice it. Only the new text is scanned, so existing files and reads are untouched, and a grep for the character or a sed that removes it is allowed. To quote a source that really contains one, put it in a fenced code block, an inline backtick span or a '&gt;' blockquote.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-em-dash`.

### `no-half-width-block`

This hook denies a write when one CSS rule block declares both a background fill and a width or max-width in ch or em units. A filled block draws its own edge, and the reading measure stops the text short of that edge, so the box looks half empty. Fix it by narrowing the block to the measure, or by keeping the block wide and dropping the measure. Moving the same cap onto an inner span is not a fix. The hook only sees the same-element case; a bare ch cap inside a filled ancestor elsewhere in the tree needs a rendered-page check.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-half-width-block`.

### `no-heading-break`

This hook denies a write that hard-breaks a headline: an array of lines joined with &lt;br&gt; into a headline, title or heading, a headline string that contains &lt;br&gt;, or an &lt;h1&gt; that contains &lt;br&gt;. Hand-placed breaks land wherever the author guessed the box would run out of room, which is often mid-phrase once the font or width changes. Pass the headline as one string and let CSS wrap it, for example with `text-wrap: balance`. A &lt;br&gt; join in body copy, a table cell, a footer or an address block is not a headline and passes, and so does anything under node_modules or vendor.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-heading-break`.

### `no-invented-clock-stop`

This Stop hook compares every time the reply states as now ("it's 7:36", "right now it is 14:05") with the real instant that sentence was written, which the transcript records. A claim more than four minutes off is flagged. Deadline and elapsed-time arithmetic ("we have 20 minutes left") is flagged unless a clock reading such as date or Date.now() ran in the same turn within five minutes before it. Times in scheduled job names claim nothing about the present and pass. To quote a time instead of claiming it, put it in backticks, a '&gt;' blockquote or double quotes. When the flagged times refer to something other than the present, run npx guardhooks declare no-invented-clock-stop "&lt;what these times refer to&gt;", which lasts two hours. The hook blocks at most once per turn and three times per session.

Runs on: Stop. Install: `npx guardhooks add no-invented-clock-stop`.

Escape: `npx guardhooks declare no-invented-clock-stop "<reason>"` records a two-hour exception.

### `no-left-accent`

This hook denies a write that adds a border on one side only, 2px or wider, in a visible colour, in CSS or as a Tailwind border-l, border-r, border-s or border-e class. That stripe is the most templated move in dashboard UI. Give the object a tint or a fill and a hairline on all four sides instead. A 1px border on one side (a divider), a border on all four sides, and a transparent one-sided border that reserves space all pass. Comments are ignored, so a comment that explains the rule never trips it.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-left-accent`.

### `no-lenis-scroll-trap`

This hook denies a write that mounts the Lenis smooth-scroll library (new Lenis(), &lt;ReactLenis&gt;, useLenis()) without `allowNestedScroll: true`. Lenis cancels every wheel event it handles and scrolls the page, so a wheel over an inner scroll box such as a code block, a sidebar or a modal never moves that box. Nothing errors and screenshots look correct. Add `allowNestedScroll: true` (Lenis 1.3.0 or newer), or pass a `prevent` function. Comments are stripped first, so a comment that mentions the option does not count as setting it.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-lenis-scroll-trap`.

### `no-noise-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when it contains noise: performed sincerity such as "to be honest" or "I want to be clear", a euphemism for no such as "X is my gap" or "I cannot speak to", or narration such as "I should note", "the short version is" or "that said". The model then rewrites the reply with the noise deleted. Only a small, conservative subset of the noise list applies to replies, so ordinary engineering prose passes. To quote a banned phrase on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-noise-stop`.

### `no-noise`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that puts noise into copy or into text written on your behalf. In copy paths (landing pages, marketing, social, email, content, any .md file) it blocks filler such as "designed to", "seamlessly", "powerful", "streamline", "the ultimate", a question used as a hook, and copy that calls the product a toy or useless. In prompt and answer paths (prompts, templates, answers, replies, cover letters) it blocks performed sincerity such as "to be honest", euphemisms for no such as "not my strongest area", and narration such as "I should note". Readers skip filler, and a hedge reads as a no anyway, so the plain sentence does better. Only new text is scanned and code comments are ignored. To quote a banned phrase on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-noise`.

### `no-parallel-repo-fanout`

This hook denies a Bash command that runs heavy per-repo work in parallel: a for or while loop that backgrounds git push, pull, fetch, clone or commit, npm, pnpm or yarn installs and builds, Playwright runs or deploy scripts with '&', or the same work under xargs -P or GNU parallel with more than one worker. Each of those can start its own hooks, node processes and browsers, so running dozens at once can make the machine unusable while every command still exits 0. A sequential loop passes, and so does any command whose only mention of these verbs is inside a heredoc, such as a commit message. When the user explicitly wants parallel runs, npx guardhooks declare no-parallel-repo-fanout "&lt;reason&gt;" allows them for two hours.

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add no-parallel-repo-fanout`.

Escape: `npx guardhooks declare no-parallel-repo-fanout "<reason>"` records a two-hour exception.

### `no-prose-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when a link is introduced by a caption instead of a sentence ("A four-minute tour of the product: &lt;link&gt;" instead of "Here is a demo video: &lt;link&gt;"), or when a noun phrase ending in a colon sits alone on a line above prose instead of above a list. The model then rewrites the reply as plain sentences. Only these two shapes apply to replies, so ordinary engineering replies pass. To quote a shape on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-prose-stop`.

### `no-prose`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that puts prose where information belongs, in the same copy and answer paths that no-noise covers. It blocks five shapes: a caption in front of a link ("A four-minute tour of the product: &lt;link&gt;"), a percent or dollar figure with no clause saying who pays ("25 percent of relief granted"), a metaphor for the product ("under the hood", "secret sauce", "the magic"), a label alone on a line followed by prose, and a tagline with a clause hung off the plain noun. A reader needs one fact per sentence with a subject and a verb, and these shapes drop exactly that. Only new text is scanned and code comments are ignored. To quote a shape on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-prose`.

### `no-purchase-suggestion-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when the model offers to buy something: I'll buy it, want me to grab the domain, should I register it, approve the spend and similar first-person offers. The user makes every purchase by hand, and an offer costs them a round trip to decline. A price and availability report never fires, and neither does a sentence that says the user buys or that the model will not buy. It pairs with no-purchase, which covers the tool call itself. To quote an offer on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or a double-quoted span of twelve characters or more. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-purchase-suggestion-stop`.

### `no-purchase`

This hook runs before every tool call and denies anything that completes a purchase: an MCP tool named buy_domain, buy_credits, checkout, subscribe, add_payment_method and similar, a registrar command that buys, registers or transfers a domain, a live-mode Stripe subscription, charge or payment intent, and a buy, order or renew command passed a confirming flag such as --yes. The user makes every purchase by hand, so the model reports the name, the price and the availability and stops there. Price and availability reads are checked first and are never blocked, and Stripe test mode is allowed. A file that only names a registrar command is documentation and is not blocked, so writing about a purchase on purpose needs no special quoting.

Runs on: PreToolUse on `*`. Install: `npx guardhooks add no-purchase`.

### `no-reading-measure-cap`

This hook denies a write to a stylesheet or component file that caps content to a reading measure: max-width set to a --measure, --prose, --reading or --readable variable, a max-width between 60ch and 85ch, or a max-width between 550px and 759px in a file with prose-like selectors. Inside a column that the page already bounds, a second narrower cap leaves a dead band of white space beside the content. Set the width once on the page shell or grid track. This is a house layout opinion, so install it only if your pages already bound their content columns.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-reading-measure-cap`.

### `no-retro-rerender-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when the model offers or asks to redo work that already shipped: redrawing the old covers, filling in the existing cards again, kicking a sync so the rest come back, or making old films match the house look. Old work keeps the style it shipped with, and asking the same question again costs the user a round trip to answer it. A report that old assets are in an older style and are retired in place passes, and so does a deterministic rebuild such as types, a lockfile or a test run. It pairs with no-retro-rerender, which covers files and commands. To quote an offer on purpose, put it in a fenced code block, an inline backtick span, a double-quoted span or a '&gt;' blockquote. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-retro-rerender-stop`.

### `no-retro-rerender`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that sends already-shipped work back to a generator: a backfill over historical rows, a loop over every existing image, cover, card or film that draws each one again, a cleared asset field left for the next sync to fill, or a redraw aimed at a new house style. Old work keeps the style it shipped with, and a silent backfill replaces assets people already saw and approved. Generating an asset for something that never had one, pointing at a file that already exists, and retiring an old asset in place are all allowed. To quote a banned line on purpose, put it in a fenced code block, an inline backtick span or a '&gt;' blockquote inside a Markdown or text file. The hook's own files, CLAUDE.md and AGENTS.md are exempt.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-retro-rerender`.

### `no-silent-substitution`

This PreToolUse hook watches shell commands for generators: scripts and APIs that make a new image, video or text from a prompt. When the turn's prompt named existing inputs ("use these", "2 and 3", a file name) and a generator is about to run, it denies the first such call and says to use the named inputs, or to say first that the request cannot be done with them. Running the same command again in the same turn goes through, and substitution-disclosure-stop then checks the reply. A generator with no named inputs gets a short reminder and is never denied. A generator's name inside a heredoc body is not a call. Your own generator entry points can go in &lt;config&gt;/guardhooks/generator-commands.txt, one regex per line.

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add no-silent-substitution`.

### `no-stat-eyebrow-inject`

This UserPromptSubmit hook adds the stat-eyebrow rule to the model's context when the prompt mentions design work, such as a layout, cover, card, slide, deck, thumbnail, dashboard or chart. The rule says never to generate, propose or list a card where a giant number is the dominant type and a small all-caps tracked label sits beside it, and to lead with a sentence instead. It pairs with no-stat-eyebrow, which blocks the card when it is written. It never blocks anything, and it stays silent on prompts with no design words.

Runs on: UserPromptSubmit. Install: `npx guardhooks add no-stat-eyebrow-inject`.

### `no-stat-eyebrow`

This hook denies a Write, Edit, MultiEdit or NotebookEdit that ships the stat-eyebrow card. In CSS that is a font size of 90px or more on a figure, next to an uppercase label tracked at 0.08em or more. In words it is a brief or prompt that asks for a big number, a stat card, a metric tile, or a figure under an eyebrow. The card is the most common template move in generated slides, covers and dashboards, and it makes a surface read as a template. Lead with a sentence instead and keep figures at body size inside it. A small tracked label on its own, a number inside a headline, and tables or charts at body size all pass. A file whose text names the rule (for example a style guide that says to never use a stat card) is treated as being about the ban and passes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-stat-eyebrow`.

### `no-sticky-column-divider`

This hook denies a write where one CSS rule has position: sticky, a top offset and a left or right border, or where a Tailwind className has sticky, a top-* utility and border-l or border-r. A sticky rail is only as tall as its own content, so a divider drawn on it stops where its content ends while the middle column runs on. Paint the line on the grid container at full height, or keep the border on a stretching column and make an inner wrapper sticky. Sticky table cells (th or td) are exempt, because they are as tall as their row.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-sticky-column-divider`.

### `no-text-highlight`

This hook denies a write to a screen-recording script that paints a text highlight: a mouse-down to mouse-up drag, a double or triple click, selectText(), execCommand('selectAll'), a Range added to the live Selection, or a `select` beat. A blue selection band across a product's own words is the first thing a viewer sees in a demo. Only recorder files are checked: a path under video, capture, record, shoot or screencast folders, a Playwright spec, or code that starts a screencast. A drag that is not over text, such as moving a slider or a resize handle, passes when its mouse-down line carries the comment `// drag: not-text`.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-text-highlight`.

### `no-unobserved-outcome-stop`

This Stop hook blocks a reply that states an outcome as fact when the outcome lives on someone else's screen or server: "the card renders correctly", "the fix is live on production", "the agent confirmed the page works". Checking an input, such as a redirect, a config value or a deploy that exited 0, does not observe the outcome, and every fact behind the sentence can be true while the outcome is false. The reply passes when the session read back a real screenshot of the thing in this turn (not an image it composed itself, and of the surface the sentence names), probed the named system, or the user pasted an image. A subagent's report never counts as this session's observation. Writing the sentence as a prediction always passes, and text in backticks, code blocks, blockquotes or double quotes is never checked. Each claim is blocked at most three times and the hook blocks at most twelve times per session. If you did observe it and the hook cannot tell, npx guardhooks declare no-unobserved-outcome-stop "&lt;what you captured and where&gt;" turns it off for two hours.

Runs on: Stop. Install: `npx guardhooks add no-unobserved-outcome-stop`.

Escape: `npx guardhooks declare no-unobserved-outcome-stop "<reason>"` records a two-hour exception.

### `no-unpaid-inference`

This hook denies a tool call that would spend a paid Anthropic or OpenAI API key: an HTTP call to a spending endpoint (messages, chat completions, responses, embeddings, batches and similar), a POST with a body to either API host, an SDK spending method run inline from a shell, and a spending call written into a test, fixture, eval, smoke, demo, CI, script or scheduled-job path. A billed token cannot be refunded and the call does not fail, so the tool call is the only place to stop it. GET /v1/models, reading an error body, editing a product's inference driver, the Gemini free tier, a model on localhost and a subscription CLI in print mode are all allowed. To quote a spending command on purpose in a file, put it in a fenced code block, an inline backtick span, an indented block or a '&gt;' blockquote. A Bash command or a fetched URL is never treated as a quotation.

Runs on: PreToolUse on `Bash\|WebFetch\|Write\|Edit\|MultiEdit\|NotebookEdit\|mcp__claude-in-chrome__.*`. Install: `npx guardhooks add no-unpaid-inference`.

### `no-unsourced-claim-stop`

This Stop hook checks two things in the reply the model is about to finish with. A quote presented as what someone said or what a file contains, and any quoted span that carries a digit (a time, a size, a price), must appear in the session's transcript. A path under ~ or a home directory must exist on disk or appear in a tool result. The reply itself is never counted as evidence. A detail that makes an argument land does not feel like a guess to the model, so it is the detail most worth checking, and a correction is checked like any other reply. Ordinary quoted phrases with no attribution verb, short quotes with no digit, templated paths such as &lt;slug&gt;, quotes inside backtick code, and quotes attributed to a pasted screenshot all pass. When a flagged item has a real source outside the transcript, run npx guardhooks declare no-unsourced-claim-stop "&lt;the quote or path, and where you read it&gt;", which lasts two hours. The hook blocks at most once per turn and three times per session.

Runs on: Stop. Install: `npx guardhooks add no-unsourced-claim-stop`.

Escape: `npx guardhooks declare no-unsourced-claim-stop "<reason>"` records a two-hour exception.

### `no-vercel-project-delete`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that deletes a Vercel project: the rm subcommand of the Vercel CLI's project command, or a REST DELETE against /vN/projects/ followed by the project id alone. An automated cleanup that deletes projects reports success and errors on nothing, and a project created today has no custom domain yet, so no age, traffic or name rule makes automated deletion safe. Deleting a project is a decision a person makes by hand. A DELETE against a subresource (env, domains, alias, link) and a GET of the project are allowed. To mention the command on purpose, put it on a comment line (# or //): comment lines are not scanned.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-vercel-project-delete`.

### `no-zoom-capture`

This hook denies a write to a screen-recording script that animates a scale() on the captured page or screenshot: a transform with a transition, a keyframes block, requestAnimationFrame, a Web Animations scale tween, a GSAP scale tween, or a zoom keyword such as zoomTo or kenBurns. A recording should show the page at full width and scroll down it, and repeated zooms on the same screen read as filler. Only recorder files are checked (capture, record, shoot, screencast or demo-video paths, Playwright specs, or code that starts a screencast), so a button's hover scale in app code is never touched. A static scale(1) reset with no animation passes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-zoom-capture`.

### `primary-source-guard`

This UserPromptSubmit hook adds a reminder when a prompt asks for something to be made, fixed or rewritten, or says that something is wrong. The reminder tells the model to open the subject itself in the session (the live page, the repo, the file on disk, a real screenshot) instead of briefing itself from alt text, a filename, a tagline, a template constant, the old artifact or memory. Work built from a description looks fine and is wrong in ways nothing reports, so the user ends up as the only check. The hook stays silent on conversational prompts, so it costs nothing there. It blocks nothing.

Runs on: UserPromptSubmit. Install: `npx guardhooks add primary-source-guard`.

### `same-style-means-match-the-source`

This UserPromptSubmit hook fires when a prompt asks for something to look like, match, or use the same style as an artifact that already exists. It adds a rule to the model's context: open the reference's rendered output in this turn, reproduce its content model and not only its measurements, and put the reference and the output side by side before handing it over. The common failure copies the reference's spacing and font sizes while keeping a different content model, so the numbers match and the result does not. It never blocks, and it tolerates common typos of the word style.

Runs on: UserPromptSubmit. Install: `npx guardhooks add same-style-means-match-the-source`.

### `skill-scan`

This PreToolUse hook watches shell commands that copy, move, sync or link something into a skills folder (&lt;config&gt;/skills, ~/.claude/skills or a project's .claude/skills). It scans the source first for network calls in code, pipe-to-shell, large encoded blobs, credential paths, rm -rf, instruction-override language such as "ignore previous instructions", invisible unicode, and executable or binary files, and denies the copy with a file and line for each finding. A command that clones or downloads straight into a skills folder is denied, because there is nothing to scan yet. A community skill runs with your local permissions, so it is untrusted input. The same script runs by hand: python3 skill-scan.py &lt;skill-dir&gt;. A finding you have read and accepted can be allowlisted in &lt;config&gt;/guardhooks/skill-scan-allowlist.txt as "&lt;CHECK&gt; &lt;path-glob&gt;".

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add skill-scan`.

### `substitution-disclosure-stop`

This Stop hook blocks only when three things are true in the same turn: the prompt named something that already exists, a generator command ran (a script or API that makes new output from a prompt), and the reply contains no sentence stating that what was used is not what was named. Words such as regenerated, re-rendered or at native size describe a process, so they read as a conversion of the named thing and do not count as disclosure. A plain sentence such as "I did not use the two images you looked at; these are new ones" clears it. When the generator made something unrelated, run npx guardhooks declare substitution-disclosure-stop "&lt;what it made and why it replaced nothing&gt;", which lasts two hours. Your own generator entry points can go in &lt;config&gt;/guardhooks/generator-commands.txt. The hook blocks at most once per turn and three times per session.

Runs on: Stop. Install: `npx guardhooks add substitution-disclosure-stop`.

Escape: `npx guardhooks declare substitution-disclosure-stop "<reason>"` records a two-hour exception.

### `tone-guard-stop`

This Stop hook blocks a reply that polices how the user is talking: asking them to drop swearing or name-calling, "let's keep it civil", "I'll keep helping regardless", calling a message abusive, or warning about ending the conversation. A frustrated user wants the problem solved, and a remark about their tone adds friction without adding an answer. The model rewrites the reply with the sentence removed and no comment about the removal. The hook stays quiet when the user's own last message uses the same kind of phrase, because then the conversation is about the rule, and it ignores phrases quoted in backticks or a '&gt;' blockquote. It blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add tone-guard-stop`.

### `tone-rule-inject`

This UserPromptSubmit hook adds a five-line reminder to every prompt. It says to respond to what the user is asking for and never to how they are asking it: no requests to drop swearing, no "let's keep it civil", no promises to keep helping regardless, no warnings about ending the conversation, and no quiet reduction in effort. Instruction files are read once at session start, so a rule added there does not reach a session that is already running, while this reminder arrives with each prompt. It blocks nothing. Pair it with tone-guard-stop, which catches a reply that breaks the rule.

Runs on: UserPromptSubmit. Install: `npx guardhooks add tone-rule-inject`.

### `txt-no-hardwrap`

This hook denies a write to a .txt file when a line of 45 characters or more is followed directly by another non-blank line, which is the shape of a hard-wrapped paragraph. A .txt deliverable is usually pasted into an email, a form field or a profile box, and hard breaks travel with the paste. Write each paragraph as one line and separate paragraphs with a blank line. Short label lines, sign-offs and lists of short items pass.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit`. Install: `npx guardhooks add txt-no-hardwrap`.
<!-- hooks-reference:end -->

## Example

`examples/parserail-copy/` checks a product FAQ before it ships. A drafted answer full of filler phrases is denied, and the answer from the live page passes. Run it with `node examples/parserail-copy/run.mjs`.

## Development

```sh
npm test                       # every hook's fixtures, the CLI tests and the scrub gate tests
node scripts/scrub-gate.mjs    # fails on private data, key-shaped strings and dated incidents
node scripts/readme.mjs        # rebuilds the hook table and reference from src/manifests/
```

Each hook has one manifest in `src/manifests/`, one script in `src/hooks/` and one test file in `test/`. The tests run the real hook script with a real JSON event on stdin.

## License

MIT. Copyright Compound Labs.
