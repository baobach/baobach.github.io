#!/usr/bin/env bash
#
# bootstrap_vault.sh: scaffold an agent-maintained Zettelkasten vault
# (folders, AGENTS.md, CLAUDE.md, Index.md, Log.md, a note template, and the
# skills digest/wiki/qna/lint/explain for Claude Code, Codex, and Hermes Agent),
# plus wiki_lint.py when it sits next to this script.
#
# Post: https://quantfin.net/posts/llm-wiki-external-brain/
# Usage: bash bootstrap_vault.sh [vault-path]   (default: ~/external-brain)
# Existing files are never overwritten, so it is safe to rerun.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-$HOME/external-brain}"
TODAY="$(date +%F)"

mkdir -p "$VAULT"
cd "$VAULT"
mkdir -p "Fleeting Notes" "Literature Notes" "Permanent Notes" \
  Templates Files raw outputs .claude/skills .agents/skills

# write <path>: copy stdin to <path> unless the file already exists
write() {
  if [[ -e "$1" ]]; then
    echo "skip   $1 (exists)"
    cat >/dev/null
  else
    mkdir -p "$(dirname "$1")"
    cat >"$1"
    echo "wrote  $1"
  fi
}

write AGENTS.md <<'EOF'
# External Brain: guide for AI agents

A Zettelkasten-style Obsidian vault maintained together with AI coding agents.
Claude Code reads this file through `CLAUDE.md`; Codex and Hermes Agent read it
directly. Edit rules here, never in `CLAUDE.md`.

## Folders

- `raw/`: sources waiting to be digested (web clips, PDFs, transcripts, photos
  of handwritten notes). Agents read it and never edit, move, or delete it. It
  is transient: the owner clears it after digestion, so no note may link,
  embed, or cite a `raw/` path.
- `Fleeting Notes/`: quick captures, `type: fleeting`. Every new note lands here.
- `Literature Notes/`: synthesized write-ups of several fleeting notes or
  sources, `type: literature`.
- `Permanent Notes/`: reference-quality notes, rarely edited, `type: permanent`.
- `Files/`: images and attachments that notes embed.
- `Templates/`: note templates. Quote `{{placeholders}}` inside frontmatter.
- `outputs/`: generated reports and drafts waiting for review.
- `Index.md`: topic-grouped catalog of every note, rebuilt by `/wiki`. Read it
  first to find notes; then read the notes themselves.
- `Log.md`: append-only log, one line per change. Read only its last 30 lines.

## Frontmatter

```yaml
---
title: "Note title"
type: fleeting          # fleeting | literature | permanent
created: 2026-01-31T09:00:00
updated:
tags: ["#tag"]
topic: ["[[Concept Note]]"]
sources: []             # URL, DOI, [[note]], or a plain description; never raw/
---
```

## Rules

- Distill, don't transcribe. A fleeting note is a few dense bullets.
- Link related notes with `[[wikilinks]]`; prefer an existing topic over a new one.
- Never promote a note to Literature or Permanent without the owner's approval.
- Never move or delete a fleeting note. After a promotion, append
  `Promoted to [[New Note]]` to its last line.
- A fact added from outside the vault is marked as LLM-suggested, with a source.
- Log every write in `Log.md` (Hermes uses `Log-hermes.md`):
  `- YYYY-MM-DD | <agent> | <skill> | what changed`.

## Writing style

A light version of ASD-STE100 Simplified Technical English, for all new text.

- One instruction per sentence; steps in the imperative, at most 20 words.
- Descriptive sentences at most 25 words; one topic per paragraph.
- Active voice. The same word for the same thing every time.
- Common words: use, start, make sure, before (not utilize, commence, ensure,
  prior to). A vertical list for three or more parallel items.
- Keep technical terms, code, and quotes exactly as they are.

## Write lock

One agent writes at a time. Before any write, run
`mkdir -p .locks && mkdir .locks/vault-write.lock`. The second `mkdir` fails
if another agent holds the lock. Then write `<agent> | <ISO time> | <task>` to
`.locks/vault-write.lock/owner`. Remove the lock directory when the whole
operation is done. A lock older than 30 minutes is stale, but ask the owner
before removing it.

## Git sync

The lock works on one machine only, because `.locks/` is not synced.

- An agent on a second machine runs `git pull --rebase` before every write.
- After the write, it commits only the files it created, then pushes.
- If the pull or the push fails, it stops and tells the owner. It never
  resolves a conflict itself.
- If obsidian-git runs on the main machine, it commits on a timer. Don't
  commit routine edits by hand.

## Agents and roles

- Claude Code and Codex: all skills (`/digest`, `/wiki`, `/qna`, `/lint`,
  `/explain`).
- Hermes Agent on a small local model: `/qna`, and `/digest` into new fleeting
  notes only. It never edits existing notes, rebuilds `Index.md`, promotes, or
  applies lint fixes, and it logs to `Log-hermes.md` instead of `Log.md`.
  The skills it must not run (`/wiki`, `/lint`, `/explain`) say so in their
  first line.
EOF

write CLAUDE.md <<'EOF'
@AGENTS.md
EOF

write Index.md <<EOF
---
title: "Index"
type: index
updated: $TODAY
---

# Vault Index

Catalog of every note, grouped by topic. Rebuilt by \`/wiki\`.

## Uncategorized

## Recently Active
EOF

write Log.md <<EOF
---
title: "Log"
type: log
---

# Operation Log

Append-only. One line per change: \`- YYYY-MM-DD | agent | skill | what changed\`.

- $TODAY | human | setup | vault scaffolded with bootstrap_vault.sh
EOF

write "Templates/Note Template.md" <<'EOF'
---
title: "{{title}}"
type: fleeting
created: "{{date}}"
updated:
tags: []
topic: []
sources: []
---
# {{title}}

-
EOF

write .gitignore <<'EOF'
.locks/
.obsidian/workspace*.json
.DS_Store
EOF

write .claude/skills/digest/SKILL.md <<'EOF'
---
name: digest
description: Turn a file in raw/, a URL, or pasted text into a new fleeting note that cites its origin. Use when the user drops a source into raw/, shares a link, or asks to digest or save something into the vault.
---

# /digest

1. Check `Log.md` and the `sources:` fields for the same source. If it was
   digested before, say so and ask before creating a second note.
2. Take the write lock (see `AGENTS.md`).
3. Read the source. Distill the ideas worth keeping into a few dense bullets;
   don't copy it.
4. Write `Fleeting Notes/<Title>.md` with the frontmatter from `AGENTS.md`.
   `sources:` holds the original URL or a plain description, never a `raw/` path.
5. Copy any image the note needs into `Files/` and embed it with `![[name.png]]`.
6. Link two or three related notes that `Index.md` lists.
7. Append to your log (`Log.md`; Hermes uses `Log-hermes.md`):
   `- <date> | <agent> | /digest | <source> -> [[New Note]]`.
8. Release the lock and tell the user the `raw/` file can now be removed.
EOF

write .claude/skills/wiki/SKILL.md <<'EOF'
---
name: wiki
description: Rebuild Index.md and propose fleeting notes ready for promotion into Literature or Permanent notes. Use when the user asks to update the index, refresh the wiki, or review notes for promotion.
---

# /wiki

Hermes Agent: do not run this skill. Tell the user it belongs to Claude Code
or Codex (see the roles in `AGENTS.md`).

## Rebuild the index
1. Read the frontmatter of every note in the three note folders.
2. Group notes by their `topic:` and `tags:` links. Section names follow the
   clusters you find; a note may appear in several sections. Notes without any
   topic go under `## Uncategorized`. Don't guess a topic for them.
3. List Literature and Permanent notes one per line with a one-line summary;
   fleeting notes of a section may share one comma-separated line.
4. Refresh `## Recently Active` (15 newest by `updated:` or `created:`).
5. Take the write lock, write `Index.md`, log one line, release the lock.

## Propose promotions
1. Find fleeting notes with real substance, alone or in groups on one theme.
2. Show a shortlist, each with one line on why it is ready. Create nothing yet.
3. Take the write lock. For each item the user approves, write a synthesized
   note in `Literature Notes/` with `sources:` listing the fleeting notes, and
   append `Promoted to [[New Note]]` to each source note.
4. Log one line per promotion, then release the lock.
EOF

write .claude/skills/qna/SKILL.md <<'EOF'
---
name: qna
description: Answer a question from the vault's own notes, citing each note used with a wikilink. Use when the user asks something their notes can answer, or asks to check the vault.
---

# /qna

1. Read `Index.md` to find the relevant notes.
2. Read those notes (at most five). The index is a catalog, not a source.
3. Answer directly and cite every note with a `[[wikilink]]`. If notes disagree
   or the vault is silent on part of the question, say so instead of filling
   the gap with outside knowledge presented as vault content.
4. If the answer is new (not a restatement of one note), offer to save it as a
   fleeting note. Write nothing until the user says yes; then follow /digest
   steps 2, 4, 7, and 8 with the cited notes as `sources:`.

Answering without saving needs no lock and no log line.
EOF

write .claude/skills/lint/SKILL.md <<'EOF'
---
name: lint
description: Health-check the vault for broken links, links into raw/, orphan notes, malformed frontmatter, contradictions, and missing concept notes. Use when the user asks to lint, audit, or clean up the vault.
---

# /lint

Hermes Agent: do not run this skill. Tell the user it belongs to Claude Code
or Codex (see the roles in `AGENTS.md`).

1. Run `python3 wiki_lint.py .` in the vault root for the mechanical checks.
   If the script is missing, check the same things with grep.
2. Read pairs of notes on the same subject and look for contradicting claims.
3. Look for concepts mentioned in several notes that have no note of their own.
4. Take the write lock before the first write.
5. Auto-fix only mechanical problems with one obvious answer (a link that is a
   typo of an existing note, broken YAML syntax). Report everything else.
6. Write `outputs/lint-<date>.md`: fixes applied first, then findings by
   category, then anything you skipped or sampled instead of checking fully.
7. Log one line, then release the lock.
EOF

write .claude/skills/explain/SKILL.md <<'EOF'
---
name: explain
description: Build a self-contained HTML explainer page about a topic from the vault's notes, with inline SVG diagrams and citations, saved to outputs/. Use when the user asks for an explainer, a visual explanation, or an answer in HTML.
---

# /explain <topic>

Hermes Agent: do not run this skill. Tell the user it belongs to Claude Code
or Codex (see the roles in `AGENTS.md`).

1. Read `Index.md` and the notes on the topic. If the vault has little on it,
   say so and ask before you continue.
2. Plan one question for the page to answer, 3 to 6 sections, and a diagram
   for each relationship that prose explains badly.
3. Take the write lock. Write `outputs/explain-<topic>-<date>.html` as one file:
   inline CSS, JavaScript, and SVG; no network requests; light and dark mode.
4. Use only what the notes say. Mark outside facts as LLM-suggested.
5. End with the list of notes used, as `obsidian://open?vault=<vault>&file=<path>`
   links. Do not link the page from any note; it is discardable.
6. Log one line, release the lock, and tell the user the path.
EOF

# Codex and Hermes read skills from .agents/skills/
for skill in digest wiki qna lint explain; do
  if [[ ! -e ".agents/skills/$skill" ]]; then
    cp -R ".claude/skills/$skill" ".agents/skills/$skill"
    echo "copied .agents/skills/$skill"
  fi
done

if [[ -e wiki_lint.py ]]; then
  echo "skip   wiki_lint.py (exists)"
elif [[ -f "$SCRIPT_DIR/wiki_lint.py" ]]; then
  cp "$SCRIPT_DIR/wiki_lint.py" wiki_lint.py
  echo "copied wiki_lint.py"
else
  echo "note   wiki_lint.py not found next to this script; /lint falls back to grep"
fi

if [[ ! -d .git ]]; then
  git init -q
  echo "initialized git repository"
fi

echo "vault ready at $VAULT"
