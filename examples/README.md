# Examples

## parserail-copy: checking a product FAQ before it ships

ParseRail is one of our products. Its landing page has a short FAQ. `live-faq.md` holds two answers copied from the live page at parserail.thecompound.tech. `draft-faq.md` is the same two answers rewritten the way a model often drafts marketing copy, with filler phrases and a dash.

`run.mjs` installs two hooks into a temporary config directory, then sends each installed hook a Write event for `landing/faq.md`.

```sh
node examples/parserail-copy/run.mjs
```

What happens:

- `event-draft.json` writes the draft. `no-noise` denies it for the filler phrases. `no-em-dash` denies it for the em dash.
- `event-live.json` writes the live copy. Both hooks allow it.

The script exits 0 only when the draft is denied and the live copy is allowed. The temporary config directory is deleted at the end, so your own `~/.claude` is never touched.

## settings.example.json

`settings.example.json` shows the entries that `npx guardhooks add no-noise no-noise-stop no-em-dash` writes into `settings.json`. The path in each command is the absolute path of your own config directory, so yours will differ.
