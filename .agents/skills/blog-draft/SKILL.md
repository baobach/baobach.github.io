---
name: blog-draft
description: Draft a quantfin.net blog post from a vault note or an outline into inbox/<slug>/, or proofread a draft against the style guide. Use when the user asks for a blog draft, post ideas for a note, or a proofread of an inbox draft.
version: 0.1.0
author: Claude Code (2026-10-20)
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [blog, writing, draft, quantfin]
    related_skills: [vault-qna]
---

# Blog Draft Skill (Hermes: drafting assistant)

Rules, front matter, and style guide are in `AGENTS.md` at the repo root, already in your context. Repo on lab-2: `/home/bao/baobach.github.io`. Vault: `/home/bao/External-brain` (read only for this skill).

## Limits

- Work only on a branch `hermes/<slug>`. Create or edit files only under `inbox/<slug>/`.
- Never touch `_posts/`, `_config.yml`, `assets/`, `tools/`, `.github/`, or `master`. Never publish. Never edit vault notes.
- Claude fact-checks your draft before it is published. Mark anything you are unsure of with `<!-- CHECK: ... -->`.

## Draft

1. `cd /home/bao/baobach.github.io && git fetch origin`. New draft: `git switch -c hermes/<slug> origin/master`. Existing branch: `git switch hermes/<slug> && git pull --rebase`. If any git command fails, stop and tell the user.
2. Read the vault note and at most 3 notes it links. Caveats: CQF lecture notes need original wording and code; notes tagged `#QCConsultant` need the user's OK first (ask, then stop); remove hostnames, IPs, and network details from lab notes.
3. Write `inbox/<slug>/post.md`: front matter (`title`, `categories` from `_data/categories.yml`, `tags` lowercase-hyphenated, `description` 50 to 160 characters), then the post in the house style. No em dashes.
4. Copy pictures the post uses from the vault `Files/` folder into `inbox/<slug>/` and give each real alt text: `![What the figure shows](file.png)`.
5. `git add inbox/<slug>/ && git commit -m "hermes: draft <slug>" && git push -u origin hermes/<slug>`. On conflict or push failure, stop and tell the user.
6. Tell the user: branch name, vault notes used, and the `CHECK` items.

## Proofread

Read `inbox/<slug>/post.md`, then reply in chat (don't rewrite the file unless asked) with: style-guide violations with line quotes, two or three title options, a description of 50 to 160 characters, tags, and missing alt text.
