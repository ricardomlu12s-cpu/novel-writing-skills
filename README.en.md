# novel-writing-skills

Tools for writing long Chinese fiction. Deconstructing books, building settings, writing chapters, removing AI tone, checking for contradictions — each broken out as its own module, use whichever you need.

> Aimed at Chinese-language writing. The "remove AI tone" wordlists are Chinese-first (English included, other languages have blank templates you can fill in). Works with any AI: Claude, GPT, Gemini, Qwen, Doubao, and so on — CLI or API. See "Works with any AI" below.

## Modules

| module | what it does | when |
|---|---|---|
| `write-novel` | entry point, routes your request to the right module | "write a novel", vague asks |
| `study-book` | deconstruct a book into a settings library | fanfiction, studying a work |
| `build-world` | world, character cards, foreshadowing table, dashboard | build settings, check foreshadowing |
| `write-chapter` | layered summaries + canon ledger + contradiction check | write chapter N, continue |
| `remove-ai-tone` | remove AI tone, unify punctuation | "this doesn't read like a person" |
| `plan-plot` | anti-cliché, pacing, common sense, fights | clichéd plot, stuck, fight scenes |
| `write-romance` | romance arcs | CP, romance scenes |
| `write-mystery` | deduction, clue ledger, fair play | mind games, suspense |
| `adapt-platform` | Qidian / Fanqie style, ensemble cast | pick platform, ensemble cast |
| `apply-feedback` | reader feedback, tiered edits | revise per reader feedback |
| `evolve-style` | style evolution, avoid writing yourself into a corner | "let's summarize", style drift |
| `publish-book` | pre-publish check, typeset export | publish, ship |
| `learn-style` | learn a work's style | absorb style, imitate without copying |
| `reuse-assets` | global asset library, deconstruct once, reuse across books | cross-book reuse, avoid flavor bleed |
| `ideate` | reduce plots to skeletons + cross-domain leaps + tension check | no ideas, predictable plot |
| `pipeline` | entry for non-writing tasks (skip if you only write) | non-creative loops |

## Install

```bash
git clone https://github.com/ricardomlu12s-cpu/novel-writing-skills.git
cd novel-writing-skills
python3 install.py          # asks: English / 中文 / 日本語 / Русский
```

Restart, then say a trigger word (e.g. "写小说") or `/module-name`.

Cross-platform install, update, uninstall: [DEPLOYMENT.md](DEPLOYMENT.md).

## Requirements

- Scripts need Python 3.8+, standard library only, nothing else to install (`ideate` graph mode optionally uses `networkx`, works without it).
- `SKILL.md` and `references/` are plain markdown instructions — the AI reads them directly, no Python needed. Scripts are an optional "deterministic check" layer.

## Works with any AI

A module is just "a folder + a doc + a few scripts", not tied to any vendor:

| usage | how |
|---|---|
| Claude Code | `/module-name` or trigger words |
| other clients with a skills dir | drop folders in, or `install.py --dir` |
| command line (no AI) | run scripts directly: `python3 write-chapter/scripts/continuity_check.py <project>` |
| your own API workflow | use SKILL.md as prompt template, scripts as tools |

## Project layout

One novel = one project folder:

```
<project>/
├── manuscripts/        final text
├── drafts/             AI drafts, kept separate
├── summaries/          layered summaries L1-L5
├── canon-ledger/       canon ledger (facts/promises/timeline, append-only)
├── characters/         character cards
├── foreshadowing.jsonl foreshadowing table
├── relationships.jsonl relationship web
└── ...
```

Global assets (deconstructions, style libraries) live in `~/.omc/assets/`, override with `ASSET_ROOT`.

## Why it's built this way

Three ways long fiction tends to break, each with a module:

- **Contradictions, forgotten settings** → append-only canon ledger + frozen layered summaries + `continuity_check.py` hard scan.
- **Same-y, predictable plots** → `ideate` squeezes plots into "skeletons" and leaps across domains, instead of copying details.
- **Cost grows with length** → layered summaries + `lorebook.py` on-demand + `context_budget.py` pre-chapter gate, per-chapter cost stays flat.

## Notes

- Built from personal writing practice, not an official project, not guaranteed to fit everyone.
- Deconstruction studies technique only — never copy settings or lines.
- MIT license. Free to use, including commercially, keep the copyright notice.

## License

MIT
