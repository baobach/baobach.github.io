# quantfin.net, repo guide for AI agents (Claude Code and Hermes Agent)

This repo is the source of [quantfin.net](https://quantfin.net), Robert Bach's blog on quantitative finance, mathematics, and machine learning. Two agents work here (see **Agents and roles**). Both read this file: Claude Code through `CLAUDE.md` (which only contains `@AGENTS.md`), Hermes directly. Edit rules here, never in `CLAUDE.md`, and don't add a `.hermes.md` (it would shadow this file for Hermes).

## Stack

- Jekyll with the `jekyll-theme-chirpy` gem (7.x). Ruby version in `.ruby-version`, gems locked in `Gemfile.lock`.
- GitHub Pages via GitHub Actions. Pull requests run the checks; a push to `master` deploys the live site. Never push to `master` directly.
- MathJax per post (`math: true`), kramdown + Rouge, giscus comments, GA4 (production builds only).

**URL rule.** A post at `_posts/YYYY-MM-DD-<slug>.md` is served at `https://quantfin.net/posts/<slug>/`. Never rename an existing post file and never set `permalink:` in a post: either changes a live URL and loses its search ranking. Changing `title:` is safe.

## Layout

```
_posts/                     published posts
_data/categories.yml        controlled category list
assets/img/posts/<slug>/    images for posts published from 2026 on (one folder per post)
assets/img/blog/            images of older posts (leave in place; moving them changes URLs)
inbox/<slug>/               drafts: post.md plus its pictures (not built)
inbox/_template/post.md     post skeleton
scripts/<slug>/             code that produced a post's figures or results (not built)
tools/publish.py            inbox -> _posts pipeline (uv run tools/publish.py <slug>)
tools/lint_posts.py         front matter and image checks for _posts/
tools/check.sh              build + htmlproofer + linter, same as CI
tools/run.sh                local server
```

## Front matter

```yaml
---
title: "Pricing Barrier Options with Monte Carlo"
date: 2027-01-15
categories: [Quantitative Finance, Tutorial]
tags: [monte-carlo, options, python]
description: "One sentence, 50 to 160 characters, written for the search result snippet."
math: true
media_subpath: /assets/img/posts/barrier-options-monte-carlo
image:
  path: social.jpg
  alt: "Simulated paths knocked out at the barrier"
---
```

- **Required:** `title`, `categories`, `tags`, `description`. `tools/publish.py` fills `date` (today, America/New_York), `math`, `media_subpath`, and `image`.
- **categories:** one or two values from `_data/categories.yml`, main topic first: Quantitative Finance, Mathematics, Artificial Intelligence, Programming, Database Systems, Tutorial. Add a category only with the user's OK.
- **tags:** free-form, lowercase, hyphenated (`monte-carlo`, not `Monte Carlo`).
- **description:** 50 to 160 characters, no em dashes. It is the meta description and the home-page excerpt.
- **image:** a 1200x630 social card (`social.jpg`) that `publish.py` builds from `cover.*` or the first figure. It becomes `og:image`, the banner at the top of the post, and the home-page thumbnail.

## Images and scripts

- In `inbox/<slug>/`, reference pictures by filename: `![Payoff of a long call](payoff.png)` or the Obsidian form `![[payoff.png|Payoff of a long call]]`. Every image needs alt text that describes what it shows.
- `publish.py` converts PNG/JPG to WebP (max 1600 px wide), keeps GIF, MP4, and SVG, adds `{: w="..." h="..." }` size attributes, and writes everything to `assets/img/posts/<slug>/`. Prefer MP4 over GIFs above 1 MB.
- Videos: `![[heat.mp4|Heat spreading from the heaters]]` becomes Chirpy's `{% include embed/video.html %}`.
- Code that generated a figure goes in `inbox/<slug>/scripts/` (moved to `scripts/<slug>/`). Each script starts with a header comment naming its purpose and post; add `requirements.txt` when it needs packages beyond the standard library.

## Writing style

The reader is a competent developer or quant who wants working knowledge.

- **Open with the technical content.** No broad introduction and no "In today's X world". An optional `> **TL;DR:**` blockquote may come first.
- **Tone:** direct and matter-of-fact, peer to peer. Explain the how and the why of each decision.
- **Prose over bullet lists.** Use lists only for genuinely list-shaped content (steps, parameters).
- **Subtitles** carry meaning (not "Section 1"). Each main section opens with a 1 to 2 sentence overview of what it covers.
- **Banned:** "crucial", "ideal", "key", "robust", "enhance" (unless the sentence says concretely what improves and by how much), "landscape", "In today's ... world", sentences that start with "By", generic pros/cons or "real-world use cases" sections, and **em dashes** (use commas, periods, colons, or parentheses).
- Vary sentence structure and don't repeat the same adjective or adverb.
- **Code:** substantial, runnable examples the reader can adapt, explained in depth. Say where each snippet lives in the project.
- **Conclusion:** at most 4 sentences (1 or 2 paragraphs), about practical implications and open problems. Never "In conclusion" or "To sum up".
- **Math:** LaTeX, never Unicode symbols.
  - Inline: `$x^2$`. Inside a list item, escape the opening dollar: `\$x^2$`.
  - Block: `$$ ... $$` with a blank line before and after.
  - Numbered: `$$\begin{equation} ... \label{eq:name} \end{equation}$$`, referenced inline with `\eqref{eq:name}`.
- **Callouts:** Chirpy prompts, i.e. a blockquote followed by `{: .prompt-tip }`, `.prompt-info`, `.prompt-warning`, or `.prompt-danger`. Obsidian callouts (`> [!tip]`) are converted by `publish.py`.
- **Internal links:** link earlier posts in a series with root-relative URLs (`/posts/<slug>/`).
- `_posts/2024-08-28-ohlc-resampling.md` is a good reference for tone and shape.

## Agents and roles

- **Claude Code (Mac)** owns everything structural: config, CI, tooling, theme upgrades, SEO, final editing, publishing (`/publish`), and merging into `master` after the user approves the pull request. Skills: `/publish`, `/draft-from-vault`, `/seo-audit` in `.claude/skills/`.
- **Hermes Agent (dsg-lab-2, local Qwen 27B)** is a drafting assistant. It turns a vault note or an outline into a first draft in `inbox/<slug>/`, suggests titles, descriptions, tags, and alt text, and proofreads against the style guide. Skill: `.agents/skills/blog-draft/`.
  - Hermes works only on branches named `hermes/<slug>` and only creates or edits files under `inbox/`. It never touches `_posts/`, `_config.yml`, `assets/`, `tools/`, `.github/`, or `master`.
  - Hermes drafts come from a 27B model and can get technical details wrong. Claude fact-checks every Hermes draft (math, code, numbers, claims about papers or libraries) before publishing.

### Cross-machine sync

Claude (Mac) and Hermes (lab-2) each have their own clone, so they coordinate through git only.

- Hermes runs `git fetch origin` and `git pull --rebase` before writing, commits only its `inbox/<slug>/` files, and pushes its `hermes/<slug>` branch. On any pull, rebase, or push conflict it stops and tells the user instead of resolving it.
- Claude picks up Hermes work with `git fetch origin` and merges `origin/hermes/<slug>` into its working branch, then publishes from there. After the post's pull request is merged, the `hermes/<slug>` branch can be deleted.

### Vault link

Posts are often rewritten from notes in the user's Obsidian vault (`/Users/baobach/Desktop/External-brain` on the Mac, `/home/bao/External-brain` on lab-2). The hub note `Fleeting Notes/QuantFin Blog.md` holds the article tracker, the editorial calendar, and rewrite caveats (CQF lecture notes need original explanations and code; `#QCConsultant` client-work notes need the user's OK; lab notes must lose hostnames and network details).

After a post is published, Claude updates the tracker in that hub note (move the row to Published, set `last_activity`), following the vault's write lock and `Log.md` rules in the vault's `AGENTS.md`. Hermes never edits that note (vault rule: Hermes only creates new notes).

## Checks

`bash tools/check.sh` must pass before a pull request: production build, htmlproofer (internal links), and `uv run tools/lint_posts.py`. CI runs the same steps on every pull request, and a weekly job checks external links.
