# GuardHooks

You pick the hooks you want, and each hook installs independently.

GuardHooks provides Claude Code hooks. Each hook stops one kind of bad output before it reaches a file, a shell command or a chat reply. You install a hook with one command, and you remove it with one command. No hook depends on another hook.

```sh
npx guardhooks list                 # every hook, what it blocks, and whether it is installed
npx guardhooks add no-em-dash       # install one hook
npx guardhooks add no-noise no-noise-stop
npx guardhooks remove no-em-dash    # uninstall it
npx guardhooks doc no-noise         # the full description of one hook
```

## What each hook does

- A hook on `PreToolUse` denies the tool call. Claude Code shows the model the reason, and the model writes the text again.
- A hook on `Stop` sends the reply back. The model rewrites the reply before the turn ends. A Stop hook blocks at most once per turn, so it cannot trap the model in a loop.
- A hook on `UserPromptSubmit` adds a short note next to your prompt. It never blocks anything.
- A write hook scans only the new text: Write content, Edit new strings and Bash commands. The hook never scans text already in a file, and it never blocks reading a file.
- A text hook skips quoted material. A fenced code block, an inline backtick span or a `>` blockquote can reproduce a banned phrase byte for byte. Each hook's description explains how to quote text intentionally.
- A hook that cannot load its own files, or cannot parse its input, exits quietly. A broken guard never blocks your work.

## Hooks

<!-- hooks-table:start -->
| Hook | Runs on | What it blocks or adds |
|---|---|---|
| `agent-status-must-be-measured` | UserPromptSubmit | When a user asks about a subagent, the hook tells the model to check the agent's current status instead of repeating its brief. |
| `aggregate-composition-stop` | Stop | Sends a reply back when it reports a traffic, reach, or engagement number without a sample size, time window, and spread. |
| `approval-lock-inject` | UserPromptSubmit | When a prompt asks to deploy, publish, or use an approved artifact, the hook tells the model to ship those exact bytes unchanged. |
| `batch-tools-guard` | PreToolUse | After twelve consecutive tool calls arrive in separate requests, the hook tells the model to batch independent calls. |
| `block-skill-install` | PreToolUse | Denies direct skill and plugin install commands before unscanned content reaches a skills folder. |
| `block-workflow-fanout` | PreToolUse | Denies the Workflow tool before a research request starts a multi-agent run without explicit approval. |
| `clock-truth-inject` | UserPromptSubmit | Adds the actual wall-clock time to every prompt and tells the model to read it again after it becomes stale. |
| `inject-hard-rules` | SessionStart, SubagentStart | Adds your short rules file, &lt;config&gt;/hard-rules.md, at every session start, resume, compaction, and subagent start. |
| `instruction-match` | PreToolUse | Denies a file write or agent brief when its verb conflicts with the user's requested action on the same object, such as editing a deck the user asked to create. |
| `instructions-loaded-log` | InstructionsLoaded | Logs each instruction file Claude Code loads, including CLAUDE.md files, so you can verify which rules entered the context. |
| `mobile-screenshot-guard` | PreToolUse | Blocks phone-width screenshots of a site. Product and site captures use desktop width. |
| `named-artifact-guard` | UserPromptSubmit | When a prompt names existing files or selections, such as "use these", "2 and 3", or a file name, the hook tells the model to use those exact inputs. |
| `no-claude-p-stop` | Stop | Sends a chat reply back for rewriting when it plans a headless Claude CLI call instead of the selected CLI. |
| `no-claude-p` | PreToolUse | Routes headless model calls through the selected CLI by blocking headless Claude CLI calls in files and shell commands, including claude -p, claude --print, and a spawn of the claude binary. |
| `no-em-dash-stop` | Stop | Sends a chat reply back for rewriting when it contains an em dash or an en dash. |
| `no-em-dash` | PreToolUse | Blocks em dashes, en dashes, and `' -- '` used as a dash in file writes and shell commands. |
| `no-half-width-block` | PreToolUse | Blocks CSS rules that combine a ch or em reading measure with a background. |
| `no-heading-break` | PreToolUse | Blocks hard &lt;br&gt; line breaks inside a headline, title or &lt;h1&gt;. |
| `no-invented-clock-stop` | Stop | Sends a reply back when it states the current time or minutes left without a fresh clock reading. |
| `no-left-accent` | PreToolUse | Blocks a coloured stripe that places a 2px or wider border on one edge of a card or row. |
| `no-lenis-scroll-trap` | PreToolUse | Blocks Lenis smooth-scroll mounts that omit allowNestedScroll: true and can freeze inner scroll boxes. |
| `no-noise-stop` | Stop | Sends a chat reply back for rewriting when it announces honesty, hedges a no or narrates the answer instead of giving it. |
| `no-noise` | PreToolUse | Blocks filler phrases in product copy and hedging phrases in prompts and answer templates, such as "seamlessly", "designed to", "to be honest" and "not my strongest area". |
| `no-parallel-repo-fanout` | PreToolUse | Denies shell loops that run push, install, build or deploy work for many repos in parallel. |
| `no-prose-stop` | Stop | Sends a chat reply back for rewriting when it puts a caption before a link or a label where a sentence belongs. |
| `no-prose` | PreToolUse | Blocks prose shapes in product copy and answer templates, such as a caption in front of a link, a price with no payer, or "under the hood". |
| `no-purchase-suggestion-stop` | Stop | Sends a chat reply back for rewriting when it offers to buy something, such as asking whether to grab the domain. |
| `no-purchase` | PreToolUse | Blocks tool calls and shell commands that complete purchases, including MCP buy_domain calls, registrar register commands and live-mode charges. |
| `no-reading-measure-cap` | PreToolUse | Blocks stylesheet content from using a reading-measure max-width of 60 to 85ch or a --measure variable. |
| `no-retro-rerender-stop` | Stop | Sends a chat reply back for rewriting when it offers or asks to redo shipped assets to match a newer style. |
| `no-retro-rerender` | PreToolUse | Blocks code and commands that send shipped assets through a generator to match a newer style. |
| `no-silent-substitution` | PreToolUse | Denies the first generator command in a turn when the prompt names existing inputs, so new output cannot replace the named inputs without disclosure. |
| `no-stat-eyebrow-inject` | UserPromptSubmit | The hook adds the stat-eyebrow rule to prompts that ask for design work before a layout is chosen. |
| `no-stat-eyebrow` | PreToolUse | The hook blocks a stat-eyebrow card that uses a giant number as the dominant type beside a small all-caps tracked label. |
| `no-sticky-column-divider` | PreToolUse | The hook blocks a left or right border on a sticky column when the border stops short of the page. |
| `no-text-highlight` | PreToolUse | The hook blocks text-selection gestures, including drag-select, double click and selectText, in screen-recording scripts. |
| `no-unobserved-outcome-stop` | Stop | The hook sends a reply back when it states a visual or external outcome, such as renders correctly, is live or the agent confirmed it, without an observation from the session. |
| `no-unpaid-inference` | PreToolUse | The hook blocks tool calls that would spend a paid Anthropic or OpenAI API key outside a paying customer's request, including tests, evals, demos and CI jobs. |
| `no-unsourced-claim-stop` | Stop | The hook sends a reply back when it quotes content the session never saw or names a nonexistent home-directory path. |
| `no-vercel-project-delete` | PreToolUse | The hook blocks writes and shell commands that delete a Vercel project through the CLI or a REST DELETE. |
| `no-zoom-capture` | PreToolUse | The hook blocks animated zoom, including Ken Burns and punch-in effects, on a captured page in a screen-recording script. |
| `primary-source-guard` | UserPromptSubmit | The hook reminds the model to open the subject before it makes or fixes something from a description. |
| `same-style-means-match-the-source` | UserPromptSubmit | The hook requires rendered frames from an existing artifact when a prompt asks for a matching style. |
| `skill-scan` | PreToolUse | The hook scans a skill before a shell command copies it into a skills folder and denies the copy when the scan finds a red flag. |
| `substitution-disclosure-stop` | Stop | The hook sends a reply back when a generator ran after the user named existing inputs and the reply does not say whether the generator used them. |
| `tone-guard-stop` | Stop | The hook sends a reply back when the reply comments on the user's tone instead of answering. |
| `tone-rule-inject` | UserPromptSubmit | The hook adds a reminder to every prompt to answer the request without commenting on how the user asks it. |
| `txt-no-hardwrap` | PreToolUse | The hook blocks hard-wrapped paragraphs in .txt files so pasted text stays intact in email and forms. |
<!-- hooks-table:end -->

## Where the files go

- The config directory is `--config-dir DIR` when you pass it. Otherwise, the config directory is `$CLAUDE_CONFIG_DIR` when that is set, and `~/.claude` when it is not.
- `add` copies the hook's script into `<config>/hooks/guardhooks/` with the shared `lib/` folder. It then adds one entry per event to `<config>/settings.json`. It keeps every other setting in that file unchanged.
- `remove` deletes the hook's entries and its script. When no GuardHooks hook remains, it also deletes `<config>/hooks/guardhooks/`.
- Running `add` twice for the same hook leaves one entry, not two.
- Hooks that keep state, such as a counter or a recorded exception, write that state under `<config>/guardhooks/state/`.
- Restart Claude Code, or open `/hooks`, after an install so the new entries load.

## Exceptions

Some hooks accept a short-lived exception because the blocked action is sometimes correct. Those hooks name the escape in their messages:

```sh
npx guardhooks declare no-unsourced-claim-stop "the figure comes from a screenshot the user pasted"
```

A declaration lasts two hours. The reason must be a full sentence. Hooks without an escape have no flag that turns them off. To stop a hook, run `npx guardhooks remove <hook>`.

Some hooks also read an optional file of your patterns from `<config>/guardhooks/`. Each hook's description names its file.

## Requirements

- The installer requires Node.js 18 or newer.
- The hooks require Python 3.8 or newer on your PATH as `python3`. Pass `--python <command>` to `add` to write a different command.
- GuardHooks has no package dependencies.

## Hook reference

<!-- hooks-reference:start -->
### `agent-status-must-be-measured`

This UserPromptSubmit hook runs when a prompt asks what an agent is doing, how long it has run, or whether it is stuck or still running. An agent brief records planned work, so repeating it does not report the agent's current state. The hook tells the model to check the agent tools, read live progress, or ask the agent. It also tells the model not to measure runtime from a file's modification time, to check live processes when the user says an agent is still running, and to state when it cannot establish a fact. The hook blocks nothing.

Runs on: UserPromptSubmit. Install: `npx guardhooks add agent-status-must-be-measured`.

### `aggregate-composition-stop`

This Stop hook blocks a reply that states a headline audience number, such as visitors, views, followers, clicks, sessions, an average, or a multiple, in a traffic or platform context without stating the sample size, time window, and spread. Spread means a median, a per-person ratio, or a breakdown. A ranking across two or more platforms must name the platforms that report the metric. A total can be correct while its meaning is false. One outlier can carry a mean, one week can carry a sixty-day total, and one view per visitor with no returns often means a crawler. The hook ignores numbers inside fenced code blocks. When a number does not need a breakdown, npx guardhooks declare aggregate-composition-stop "&lt;reason&gt;" disables the hook for two hours.

Runs on: Stop. Install: `npx guardhooks add aggregate-composition-stop`.

Escape: `npx guardhooks declare aggregate-composition-stop "<reason>"` records a two-hour exception.

### `approval-lock-inject`

This UserPromptSubmit hook adds a note when a prompt contains a deploy word such as deploy, publish, upload, embed, ship, or use the approved. An approved image, card, or layout is the final input, not a reference for a new design pass. The note tells the model to find the exact approved source, use the same bytes, crop, dimensions, placement, and CSS, and avoid nearby visual changes. If the artifact cannot be delivered unchanged, the note tells the model to ask one plain question first. The hook never blocks anything and stays silent on other prompts.

Runs on: UserPromptSubmit. Install: `npx guardhooks add approval-lock-inject`.

### `batch-tools-guard`

This PreToolUse hook counts consecutive tool calls that arrive alone. Each request resends the full conversation, so a lone call costs the full context even when its result is small. Two independent calls sent separately cost twice as much as the same calls in one request. Calls in one request reach the hook within milliseconds of each other and reset the count. After twelve lone calls, the hook tells the model to put independent calls in one message and chain related shell steps with &&. The hook never denies a call. Its counter lives in &lt;config&gt;/guardhooks/state/batch-tools-guard/.

Runs on: PreToolUse on `Bash\|Read\|Grep\|Glob`. Install: `npx guardhooks add batch-tools-guard`.

### `block-skill-install`

This PreToolUse hook denies shell commands that install a skill or plugin directly, such as the skills add and skills install commands of the skills CLI and the plugin install command of Claude Code. Community skills and plugins are untrusted input that runs with your local permissions and credentials. The denial explains the safe path: fetch the source into a scratch folder without running it, scan it with skill-scan (python3 skill-scan.py &lt;dir&gt;), then copy the folder into the skills folder by hand. Install skill-scan too if you want that copy checked automatically.

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add block-skill-install`.

### `block-workflow-fanout`

This hook denies every call to the Workflow tool. A user who asks for deep or thorough research wants a thorough answer, but a multi-agent run can spend a very large number of tokens before anyone sees a result. The denial tells the model to read the primary sources itself, run a few targeted searches, and write the answer. If the request needs a fan-out, the denial tells the model to ask with a cost estimate. The hook has no escape flag. Run npx guardhooks remove block-workflow-fanout to allow the Workflow tool again.

Runs on: PreToolUse on `Workflow`. Install: `npx guardhooks add block-workflow-fanout`.

### `clock-truth-inject`

This UserPromptSubmit hook adds the current local date and time to the model's prompt. The hook reads the time when the prompt arrives. The model has no clock and may estimate elapsed work incorrectly between readings. The note says that the reading becomes stale, that tool calls do not provide the time, and that the model must run date again before stating the current time, the time left before a deadline, or the time elapsed. The hook never blocks anything. It pairs with no-invented-clock-stop, which checks the reply.

Runs on: UserPromptSubmit. Install: `npx guardhooks add clock-truth-inject`.

### `inject-hard-rules`

This hook reads hard-rules.md from the Claude Code config directory and adds it to the model's context at SessionStart events for startup, resume, clear, and compact, and at SubagentStart. Subagents such as Explore and Plan do not read the CLAUDE.md hierarchy. User-level instructions can also disappear during a long session after compaction, so rules that must persist need this second path. Write the file yourself in plain statements and keep it under 9,200 characters. Claude Code moves longer hook output to a file, and the model sees only a preview. The hook does nothing when the file is missing or empty. It blocks nothing.

Runs on: SessionStart; SubagentStart. Install: `npx guardhooks add inject-hard-rules`.

### `instruction-match`

This PreToolUse hook reads the verb and object from the user's last three prompts and from the action about to run. The action can be an Agent or Task brief, or a Write, Edit, MultiEdit, or NotebookEdit. When both sides name the same object with conflicting verbs, such as create against edit, create against delete, or edit against delete, the hook denies the call once and shows both sides. A file edit counts only when the user said that file already exists, because the model then copies it rather than creates it. The hook keeps no list of past failures and stays silent when no shared object exists. When the action matches the request, run npx guardhooks declare instruction-match "&lt;verb&gt; &lt;object&gt;, and why that is what was asked&gt;". The declaration lasts two hours. The declaration is ignored when its own verb still conflicts with the user's verb on that object.

Runs on: PreToolUse on `Agent\|Task\|Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add instruction-match`.

Escape: `npx guardhooks declare instruction-match "<reason>"` records a two-hour exception.

### `instructions-loaded-log`

This InstructionsLoaded hook appends one tab-separated line for each loaded instruction file to &lt;config&gt;/guardhooks/state/instructions-loaded.log. Each line contains the first eight characters of the session id, the file path, the load reason, the memory type, and the UTC time. When a model seems to ignore a rule, the log shows whether the rule loaded. Transcripts do not record the CLAUDE.md injection. Count sessions against loads of a given file to calculate its load rate. The hook trims the log to its last 10,000 lines after it passes 20,000 lines. It prints nothing and blocks nothing.

Runs on: InstructionsLoaded. Install: `npx guardhooks add instructions-loaded-log`.

### `mobile-screenshot-guard`

This hook denies a Bash command or file write that takes a phone-width photo of a site. It fires when three conditions occur together: the command takes a capture, such as a .screenshot() call, a screencast, `playwright screenshot`, or `--screenshot`; the viewport is narrower than 600 CSS px, uses isMobile, uses a phone user agent or device, or specifies a phone width on a capture flag; and the command navigates to a real site. Phone photos of a desktop product make the product look smaller, so captures should be 1280 CSS px wide or wider. Layout QA is allowed. Files under qa, e2e, tests, or gates folders and .test or .spec files may render at phone width. A local file:// render may also use phone width. Automation that must emulate a phone for a third-party form can mark the line with the comment `phone-viewport: third-party form`.

Runs on: PreToolUse on `Bash\|Write\|Edit\|MultiEdit`. Install: `npx guardhooks add mobile-screenshot-guard`.

### `named-artifact-guard`

This UserPromptSubmit hook adds a note when a prompt points to an existing artifact. Triggers include a number or ordinal for something the user was shown, a pointing word such as these or those, ownership such as the ones I picked, substitution words such as replacing or in place of, or a literal file name. The note tells the model to use the named inputs exactly, deliver them first, offer alternatives only as a question afterward, and say first when the request cannot use those inputs. It also tells the model to state a substitution in the first sentence in plain words instead of calling it regenerated or reformatted. The hook never blocks anything and stays silent when a prompt names nothing. Your own patterns can go in &lt;config&gt;/guardhooks/named-artifact-patterns.txt, one regex per line.

Runs on: UserPromptSubmit. Install: `npx guardhooks add named-artifact-guard`.

### `no-claude-p-stop`

This Stop hook reads the reply before it ends and blocks it when a sentence plans a headless Claude CLI call, such as running claude -p over each file or a headless Claude judge. The hook sends the model back to rewrite the reply with the CLI named in the GUARDHOOKS_HEADLESS_CLI environment variable. It pairs with no-claude-p, which covers files and shell commands. A sentence about this rule passes when it also says not, never, instead, replaced, legacy, or reports an error. A sentence that names the selected CLI also passes. To quote the command, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote, or a double-quoted span. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-claude-p-stop`.

### `no-claude-p`

This hook denies a Write, Edit, MultiEdit, NotebookEdit, or Bash call when its new text writes or runs a headless Claude CLI call. It covers claude -p, claude --print, claude --model, a spawn of the claude binary, and the argv form ['claude', '-p', ...]. Use it when a project sends every scripted, non-interactive model call through one CLI so cost, model choice, and logging stay in one place. Set the GUARDHOOKS_HEADLESS_CLI environment variable, such as in the env block of settings.json, to the selected CLI. The denial names that CLI. An interactive Claude Code session is never affected. CLAUDE.md and AGENTS.md are exempt. To quote the command in a document, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote, or a double-quoted span of twelve characters or more. A Bash command is never treated as a quotation.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-claude-p`.

### `no-em-dash-stop`

This Stop hook reads the reply before it ends and blocks it when the reply contains an em dash, en dash, horizontal bar, minus sign, escaped spelling of one, or `' -- '` used as a dash. The hook sends the model back to rewrite the reply with a period, comma, colon, or parentheses. It pairs with no-em-dash, which covers files and shell commands. To quote text that contains a dash, put it in a fenced code block, an inline backtick span, or a '&gt;' blockquote. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-em-dash-stop`.

### `no-em-dash`

This hook denies a Write, Edit, MultiEdit, NotebookEdit, or Bash call when its new text contains an em dash (U+2014), en dash (U+2013), horizontal bar (U+2015), minus sign (U+2212), escaped spelling such as `\u2014` or `&mdash;`, or `' -- '` used as a dash in a prose file. Models use the em dash more often than people do, and readers notice it. The hook scans only new text, so existing files and reads remain unaffected. A grep for the character or a sed that removes it is allowed. To quote a source that contains a dash, put it in a fenced code block, an inline backtick span, or a '&gt;' blockquote.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-em-dash`.

### `no-half-width-block`

This hook denies a write when one CSS rule block declares both a background fill and a width or max-width in ch or em units. The fill defines the block edge, while the reading measure leaves space before that edge. Narrow the block to the measure, or keep the block wide and remove the measure. Moving the same cap to an inner span does not fix the rule. The hook checks only the same-element case. A bare ch cap inside a separately filled ancestor requires a rendered-page check.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-half-width-block`.

### `no-heading-break`

This hook denies a write that inserts a hard break into a headline. It checks arrays joined with &lt;br&gt;, headline strings containing &lt;br&gt;, and &lt;h1&gt; elements containing &lt;br&gt;. Hand-placed breaks can split a phrase when the font or width changes. Pass one headline string and let CSS wrap it, such as with `text-wrap: balance`. A &lt;br&gt; join in body copy, a table cell, a footer or an address block passes. Content under node_modules or vendor also passes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-heading-break`.

### `no-invented-clock-stop`

This Stop hook compares every time stated as now, such as "it's 7:36" or "right now it is 14:05", with the instant when the sentence was written. It flags a claim that is more than four minutes off. It flags deadline and elapsed-time arithmetic, such as "we have 20 minutes left", unless date or Date.now() ran in the same turn within five minutes before it. Times in scheduled job names do not claim the present and pass. Put a quoted time in backticks, a '&gt;' blockquote or double quotes when it is not a current-time claim. When a flagged time refers to something other than the present, run npx guardhooks declare no-invented-clock-stop "&lt;what these times refer to&gt;". The declaration lasts two hours. The hook blocks at most once per turn and three times per session.

Runs on: Stop. Install: `npx guardhooks add no-invented-clock-stop`.

Escape: `npx guardhooks declare no-invented-clock-stop "<reason>"` records a two-hour exception.

### `no-left-accent`

This hook denies a write that adds a visible coloured border on one side only, when the border is 2px or wider. It checks CSS and Tailwind border-l, border-r, border-s and border-e classes. The stripe is a common dashboard UI pattern. Give the object a tint or fill, or add a hairline border on all four sides. A 1px border on one side passes. A border on all four sides passes. A transparent one-sided border that reserves space passes. The hook ignores comments, so comments that explain the rule do not trigger it.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-left-accent`.

### `no-lenis-scroll-trap`

This hook denies a write that mounts the Lenis smooth-scroll library with new Lenis(), &lt;ReactLenis&gt; or useLenis() without `allowNestedScroll: true`. Lenis cancels each wheel event it handles and scrolls the page, so a wheel over an inner scroll box, such as a code block, sidebar or modal, does not scroll that box. The page can show no error while screenshots still look correct. Add `allowNestedScroll: true` with Lenis 1.3.0 or newer, or pass a `prevent` function. The hook strips comments before checking the option, so a comment that mentions it does not set it.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-lenis-scroll-trap`.

### `no-noise-stop`

This Stop hook reads the reply the model is about to finish with and blocks it when it contains noise: performed sincerity such as "to be honest" or "I want to be clear", a euphemism for no such as "X is my gap" or "I cannot speak to", or narration such as "I should note", "the short version is" or "that said". The model then rewrites the reply with the noise deleted. Only a small, conservative subset of the noise list applies to replies, so ordinary engineering prose passes. To quote a banned phrase on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-noise-stop`.

### `no-noise`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that puts noise into copy or into text written on your behalf. In copy paths (landing pages, marketing, social, email, content, any .md file) it blocks filler such as "designed to", "seamlessly", "powerful", "streamline", "the ultimate", a question used as a hook, and copy that calls the product a toy or useless. In prompt and answer paths (prompts, templates, answers, replies, cover letters) it blocks performed sincerity such as "to be honest", euphemisms for no such as "not my strongest area", and narration such as "I should note". Readers skip filler, and a hedge reads as a no anyway, so the plain sentence does better. Only new text is scanned and code comments are ignored. To quote a banned phrase on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-noise`.

### `no-parallel-repo-fanout`

This hook denies a Bash command that runs heavy work for multiple repos in parallel. It checks for loops that background git push, pull, fetch, clone or commit, npm, pnpm or yarn installs and builds, Playwright runs or deploy scripts with '&'. It also checks xargs -P and GNU parallel with more than one worker. Each job can start its own hooks, node processes and browsers, which can make the machine unusable while every command still exits 0. A sequential loop passes. A command whose only mention of these verbs is inside a heredoc, such as a commit message, also passes. When the user explicitly wants parallel runs, npx guardhooks declare no-parallel-repo-fanout "&lt;reason&gt;" allows them for two hours.

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add no-parallel-repo-fanout`.

Escape: `npx guardhooks declare no-parallel-repo-fanout "<reason>"` records a two-hour exception.

### `no-prose-stop`

This Stop hook blocks a reply that introduces a link with a caption instead of a sentence, such as "A four-minute tour of the product: &lt;link&gt;" instead of "Here is a demo video: &lt;link&gt;". It also blocks a noun phrase ending in a colon when that phrase sits alone above prose instead of above a list. The model then rewrites the reply as plain sentences. Ordinary engineering replies pass when they use neither shape. Put a quoted shape in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes to quote it on purpose. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-prose-stop`.

### `no-prose`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that puts prose where information belongs, in the same copy and answer paths that no-noise covers. It blocks five shapes: a caption in front of a link ("A four-minute tour of the product: &lt;link&gt;"), a percent or dollar figure with no clause saying who pays ("25 percent of relief granted"), a metaphor for the product ("under the hood", "secret sauce", "the magic"), a label alone on a line followed by prose, and a tagline with a clause hung off the plain noun. A reader needs one fact per sentence with a subject and a verb, and these shapes drop exactly that. Only new text is scanned and code comments are ignored. To quote a shape on purpose, put it in a fenced code block, an inline backtick span, a '&gt;' blockquote or double quotes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-prose`.

### `no-purchase-suggestion-stop`

This Stop hook blocks a reply that offers to buy something, including "I'll buy it", "want me to grab the domain" and "should I register it". It also blocks similar first-person offers and offers to approve the spend. A price and availability report passes. A sentence that says the user buys or that the model will not buy also passes. The hook pairs with no-purchase, which covers the tool call itself. Put an offer in a fenced code block, an inline backtick span, a '&gt;' blockquote or a double-quoted span of twelve characters or more to quote it on purpose. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-purchase-suggestion-stop`.

### `no-purchase`

This hook runs before every tool call and denies actions that complete a purchase. It checks MCP tools named buy_domain, buy_credits, checkout, subscribe, add_payment_method and similar tools. It checks registrar commands that buy, register or transfer a domain. It checks live-mode Stripe subscriptions, charges and payment intents. It checks buy, order or renew commands with a confirming flag such as --yes. The user makes every purchase by hand, so the model reports the name, price and availability. Price and availability reads pass. Stripe test mode passes. A file that only names a registrar command is documentation and passes without special quoting.

Runs on: PreToolUse on `*`. Install: `npx guardhooks add no-purchase`.

### `no-reading-measure-cap`

This hook denies a write to a stylesheet or component file when it caps content to a reading measure. It checks max-width set to a --measure, --prose, --reading or --readable variable. It also checks max-width between 60ch and 85ch, or between 550px and 759px in a file with prose-like selectors. A second narrower cap inside an already bounded column leaves unused space beside the content. Set the width once on the page shell or grid track. This rule reflects a house layout opinion, so install it only when the page already bounds its content columns.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-reading-measure-cap`.

### `no-retro-rerender-stop`

This Stop hook blocks a reply that offers or asks to redo shipped work. It covers redrawing old covers, filling existing cards again, starting a sync so the rest return, and making old films match the house look. Old work keeps the style it shipped with. A report that old assets use an older style and remain retired in place passes. A deterministic rebuild, such as types, a lockfile or a test run, also passes. The hook pairs with no-retro-rerender, which covers files and commands. Put an offer in a fenced code block, an inline backtick span, a double-quoted span or a '&gt;' blockquote to quote it on purpose. The hook blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add no-retro-rerender-stop`.

### `no-retro-rerender`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that sends shipped work through a generator. It checks backfills over historical rows, loops over every existing image, cover, card or film, cleared asset fields left for the next sync, and redraws aimed at a new house style. Old work keeps the style it shipped with. A silent backfill replaces assets that people already saw and approved. The hook allows an asset for something that never had one, a reference to an existing file and retirement of an old asset in place. Put a quoted banned line in a fenced code block, an inline backtick span or a '&gt;' blockquote inside a Markdown or text file. The hook's own files, CLAUDE.md and AGENTS.md are exempt.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-retro-rerender`.

### `no-silent-substitution`

This PreToolUse hook watches shell commands for generators, including scripts and APIs that create a new image, video or text from a prompt. When the prompt names existing inputs, such as "use these", "2 and 3" or a file name, and a generator is about to run, the hook denies the first call. The denial requires the command to use the named inputs or the reply to state first that the request cannot use them. A second generator command in the same turn passes. substitution-disclosure-stop then checks the reply. A generator with no named inputs receives a short reminder and passes. A generator name inside a heredoc body is not a call. Add custom generator entry points to &lt;config&gt;/guardhooks/generator-commands.txt, one regex per line.

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add no-silent-substitution`.

### `no-stat-eyebrow-inject`

This UserPromptSubmit hook adds the stat-eyebrow rule to the model's context when the prompt mentions design work, such as a layout, cover, card, slide, deck, thumbnail, dashboard or chart. The rule prohibits generating, proposing or listing a card where a giant number is the dominant type beside a small all-caps tracked label, and requires a sentence instead. The hook pairs with no-stat-eyebrow, which blocks the card when it is written. The hook never blocks anything and stays silent when the prompt contains no design words.

Runs on: UserPromptSubmit. Install: `npx guardhooks add no-stat-eyebrow-inject`.

### `no-stat-eyebrow`

This hook denies a Write, Edit, MultiEdit or NotebookEdit that ships the stat-eyebrow card. In CSS, the card has a font size of 90px or more on a figure beside an uppercase label tracked at 0.08em or more. The hook also treats a brief or prompt that asks for a big number, a stat card, a metric tile or a figure under an eyebrow as a stat-eyebrow request. The card is the most common template move in generated slides, covers and dashboards, and it makes a surface read as a template. Use a sentence instead and keep figures at body size inside it. A small tracked label on its own, a number inside a headline, and tables or charts at body size pass. A file that names the rule, such as a style guide that says to never use a stat card, passes because the file discusses the ban.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-stat-eyebrow`.

### `no-sticky-column-divider`

This hook denies a write when one CSS rule has position: sticky, a top offset and a left or right border, or when a Tailwind className has sticky, a top-* utility and border-l or border-r. A sticky rail has only its own content height, so its divider stops while the middle column continues. Paint the line on the grid container at full height, or keep the border on a stretching column and make an inner wrapper sticky. Sticky table cells, including th or td, are exempt because they match the height of their row.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-sticky-column-divider`.

### `no-text-highlight`

This hook denies a write to a screen-recording script that paints a text highlight through a mouse-down to mouse-up drag, a double or triple click, selectText(), execCommand('selectAll'), a Range added to the live Selection, or a `select` beat. A blue selection band across the product's words is the first thing a viewer sees in a demo. The hook checks only recorder files under video, capture, record, shoot or screencast folders, Playwright specs, or code that starts a screencast. A drag that is not over text, such as moving a slider or resize handle, passes when its mouse-down line carries the comment `// drag: not-text`.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-text-highlight`.

### `no-unobserved-outcome-stop`

This Stop hook blocks a reply that states an outcome as fact when the outcome exists on someone else's screen or server, such as "the card renders correctly", "the fix is live on production" or "the agent confirmed the page works". Checking an input, such as a redirect, a config value or a deploy that exited 0, does not observe the outcome. Every fact behind the sentence can be true while the outcome is false. The reply passes when the session read a real screenshot of the named thing in this turn, probed the named system, or the user pasted an image. A subagent's report never counts as this session's observation. A prediction always passes, and text in backticks, code blocks, blockquotes or double quotes is never checked. The hook blocks each claim at most three times and blocks at most twelve times per session. If the session observed the outcome and the hook cannot tell, npx guardhooks declare no-unobserved-outcome-stop "&lt;what you captured and where&gt;" disables the hook for two hours.

Runs on: Stop. Install: `npx guardhooks add no-unobserved-outcome-stop`.

Escape: `npx guardhooks declare no-unobserved-outcome-stop "<reason>"` records a two-hour exception.

### `no-unpaid-inference`

This hook denies a tool call that would spend a paid Anthropic or OpenAI API key. It blocks HTTP calls to spending endpoints such as messages, chat completions, responses, embeddings and batches, POST requests with a body to either API host, SDK spending methods run inline from a shell, and spending calls written into a test, fixture, eval, smoke, demo, CI, script or scheduled-job path. A billed token cannot be refunded, so the hook stops the call before it runs. GET /v1/models, reading an error body, editing a product's inference driver, the Gemini free tier, a model on localhost and a subscription CLI in print mode are allowed. To quote a spending command on purpose in a file, put it in a fenced code block, an inline backtick span, an indented block or a '&gt;' blockquote. A Bash command or a fetched URL is never treated as a quotation.

Runs on: PreToolUse on `Bash\|WebFetch\|Write\|Edit\|MultiEdit\|NotebookEdit\|mcp__claude-in-chrome__.*`. Install: `npx guardhooks add no-unpaid-inference`.

### `no-unsourced-claim-stop`

This Stop hook checks two things in the reply the model is about to finish. First, a quote presented as what someone said or what a file contains, and any quoted span that carries a digit, must appear in the session transcript. Second, a path under ~ or a home directory must exist on disk or appear in a tool result. The reply itself never counts as evidence. A detail that makes an argument land can feel like a guess to the model, so the hook checks that detail. A correction is checked in the same way. Ordinary quoted phrases with no attribution verb, short quotes with no digit, templated paths such as &lt;slug&gt;, and quotes inside backticks pass. Quotes attributed to a pasted screenshot also pass. When a flagged item has a real source outside the transcript, npx guardhooks declare no-unsourced-claim-stop "&lt;the quote or path, and where you read it&gt;" records a two-hour exception. The hook blocks at most once per turn and three times per session.

Runs on: Stop. Install: `npx guardhooks add no-unsourced-claim-stop`.

Escape: `npx guardhooks declare no-unsourced-claim-stop "<reason>"` records a two-hour exception.

### `no-vercel-project-delete`

This hook denies a Write, Edit, MultiEdit, NotebookEdit or Bash call that deletes a Vercel project. It blocks the rm subcommand of the Vercel CLI's project command and a REST DELETE against /vN/projects/ followed by the project id alone. An automated cleanup can report success without errors, and a project created today has no custom domain yet, so age, traffic and name rules cannot make automated deletion safe. A person must decide whether to delete a project. A DELETE against a subresource, including env, domains, alias or link, and a GET of the project are allowed. To mention the command on purpose, put it on a comment line, using # or //, because comment lines are not scanned.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash`. Install: `npx guardhooks add no-vercel-project-delete`.

### `no-zoom-capture`

This hook denies a write to a screen-recording script that animates a scale() on the captured page or screenshot. It blocks a transform with a transition, a keyframes block, requestAnimationFrame, a Web Animations scale tween, a GSAP scale tween, or a zoom keyword such as zoomTo or kenBurns. A recording should show the page at full width and scroll down it because repeated zooms on the same screen add filler. The hook checks only recorder files in capture, record, shoot, screencast or demo-video paths, Playwright specs, or code that starts a screencast. A static scale(1) reset with no animation passes.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit\|NotebookEdit`. Install: `npx guardhooks add no-zoom-capture`.

### `primary-source-guard`

This UserPromptSubmit hook adds a reminder when a prompt asks for something to be made, fixed or rewritten, or says that something is wrong. The reminder tells the model to open the subject in the session, such as the live page, repo, file on disk or real screenshot, instead of using alt text, a filename, a tagline, a template constant, the old artifact or memory. Work based on a description can look fine while containing errors that nothing reports, leaving the user as the only check. The hook stays silent on conversational prompts and blocks nothing.

Runs on: UserPromptSubmit. Install: `npx guardhooks add primary-source-guard`.

### `same-style-means-match-the-source`

This UserPromptSubmit hook runs when a prompt asks for something to look like, match or use the same style as an existing artifact. It adds a rule to the model's context: open the reference's rendered output in this turn, reproduce its content model as well as its measurements, and put the reference beside the output before handing it over. The common failure copies the reference's spacing and font sizes while keeping a different content model, so the numbers match but the result does not. The hook never blocks and accepts common typos of the word style.

Runs on: UserPromptSubmit. Install: `npx guardhooks add same-style-means-match-the-source`.

### `skill-scan`

This PreToolUse hook watches shell commands that copy, move, sync or link something into a skills folder, including &lt;config&gt;/skills, ~/.claude/skills or a project's .claude/skills. It scans the source first for network calls in code, pipe-to-shell, large encoded blobs, credential paths, rm -rf, instruction-override language such as "ignore previous instructions", invisible unicode, and executable or binary files. It denies the copy with a file and line for each finding. A command that clones or downloads straight into a skills folder is denied because the hook cannot scan the source first. A community skill runs with local permissions, so it is untrusted input. The same script runs by hand with python3 skill-scan.py &lt;skill-dir&gt;. A finding that you have read and accepted can be allowlisted in &lt;config&gt;/guardhooks/skill-scan-allowlist.txt as "&lt;CHECK&gt; &lt;path-glob&gt;".

Runs on: PreToolUse on `Bash`. Install: `npx guardhooks add skill-scan`.

### `substitution-disclosure-stop`

This Stop hook blocks only when three conditions occur in the same turn: the prompt names something that already exists, a generator command runs, and the reply contains no sentence stating whether the generator used the named input. A generator is a script or API that makes new output from a prompt. Words such as regenerated, re-rendered or at native size describe a process, so they do not state whether the named input was used. A sentence such as "I did not use the two images you looked at; these are new ones" clears the hook. When the generator made unrelated output, npx guardhooks declare substitution-disclosure-stop "&lt;what it made and why it replaced nothing&gt;" records a two-hour exception. Your generator entry points can go in &lt;config&gt;/guardhooks/generator-commands.txt. The hook blocks at most once per turn and three times per session.

Runs on: Stop. Install: `npx guardhooks add substitution-disclosure-stop`.

Escape: `npx guardhooks declare substitution-disclosure-stop "<reason>"` records a two-hour exception.

### `tone-guard-stop`

This Stop hook blocks a reply that polices how the user talks. It blocks requests to drop swearing or name-calling, "let's keep it civil", promises to keep helping regardless, warnings about ending the conversation, and claims that a message is abusive. A frustrated user needs the problem solved, so a remark about tone adds no answer. The hook rewrites the reply with that sentence removed and does not comment on the removal. The hook stays quiet when the user's own last message uses the same kind of phrase because the conversation then concerns the rule. It ignores phrases quoted in backticks or a '&gt;' blockquote and blocks at most once per turn.

Runs on: Stop. Install: `npx guardhooks add tone-guard-stop`.

### `tone-rule-inject`

This UserPromptSubmit hook adds a five-line reminder to every prompt. The reminder requires a response to what the user asks and prohibits responses about how the user asks it. It prohibits requests to drop swearing, "let's keep it civil", promises to keep helping regardless, warnings about ending the conversation, and quiet reductions in effort. Instruction files load once at session start, so a rule added there does not reach a session that is already running. This reminder arrives with each prompt. The hook blocks nothing. Pair it with tone-guard-stop, which catches a reply that breaks the rule.

Runs on: UserPromptSubmit. Install: `npx guardhooks add tone-rule-inject`.

### `txt-no-hardwrap`

This hook denies a write to a .txt file when a line of 45 characters or more is followed directly by another non-blank line. That pattern forms a hard-wrapped paragraph. A .txt deliverable usually goes into an email, form field or profile box, and hard breaks remain in the pasted text. Write each paragraph as one line and separate paragraphs with a blank line. Short label lines, sign-offs and lists of short items pass.

Runs on: PreToolUse on `Write\|Edit\|MultiEdit`. Install: `npx guardhooks add txt-no-hardwrap`.
<!-- hooks-reference:end -->

## Example

`examples/parserail-copy/` checks a product FAQ before it ships. A drafted answer full of filler phrases is denied, and the answer from the live page passes. Run the check with `node examples/parserail-copy/run.mjs`.

## Development

```sh
npm test                       # every hook's fixtures, the CLI tests and the scrub gate tests
node scripts/scrub-gate.mjs    # fails on private data, key-shaped strings and dated incidents
node scripts/readme.mjs        # rebuilds the hook table and reference from src/manifests/
```

Each hook has one manifest in `src/manifests/`, one script in `src/hooks/` and one test file in `test/`. The tests run the real hook script with a real JSON event on stdin.

## License

MIT. Copyright Compound Labs.
