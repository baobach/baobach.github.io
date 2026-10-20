---
name: draft-from-vault
description: Turn a note from the user's Obsidian vault (External Brain) into a blog draft in inbox/<slug>/ in the house style. Use when the user names a vault note to write up, or says "draft a post from <note>".
---

# /draft-from-vault <note name>

Writes `inbox/<slug>/post.md` (and copies its pictures) from a vault note. It does not publish; `/publish <slug>` does that.

Vault: `/Users/baobach/Desktop/External-brain`. Read its `Index.md` to locate notes; read the actual notes, not the index entry.

## Procedure

1. **Find the note** by name (`find` under `Fleeting Notes/`, `Literature Notes/`, `Permanent Notes/`). Read it, then the notes it links that carry substance for the post (usually 2 to 5; skip stubs).
2. **Check the caveats** in `Fleeting Notes/QuantFin Blog.md` (section "Caveats for rewriting") and the note's tags:
   - CQF lecture notes (`Module X - Lecture Y`) paraphrase Fitch Learning material. Write an original explanation with your own code and data; never copy lecture text or slide figures.
   - Notes tagged `#QCConsultant` come from client work. Stop and ask the user whether they own the strategy before drafting.
   - Lab or server notes: remove hostnames, IPs, usernames, ports, and network layout.
3. **Pick the slug** (short, lowercase, hyphenated; it becomes the permanent URL) and check that neither `_posts/*-<slug>.md` nor `inbox/<slug>/` exists.
4. **Write the draft** to `inbox/<slug>/post.md` following `AGENTS.md`: front matter with `title`, `categories`, `tags`, `description`; technical content from the first paragraph; prose; meaningful subtitles with 1 to 2 sentence overviews; runnable code; LaTeX math; a conclusion of at most 4 sentences. Treat the vault note as source material, not as text to transcribe: vault notes are terse bullets, a post is an explanation.
5. **Pictures.** Copy images the post uses from the vault's `Files/` into `inbox/<slug>/` and reference them by filename with real alt text. Generate new figures with a script in `inbox/<slug>/scripts/` when the note has none and a figure helps.
6. **Verify** code you wrote (run it) and math you derived. List anything you could not verify for the user.
7. **Report** the slug, the vault notes used, and open questions. Suggest `/publish <slug>` as the next step.

## Pitfalls

- Don't edit the vault here. The tracker row is updated by `/publish` after the post goes live.
- No em dashes anywhere in the draft.
