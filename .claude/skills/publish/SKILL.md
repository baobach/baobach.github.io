---
name: publish
description: Publish a draft from inbox/<slug>/ to the blog. Fills missing front matter, runs tools/publish.py (images, Obsidian syntax, social card), runs the checks, and opens a pull request. Use when the user says /publish <slug>, "publish this post", or hands over a finished draft.
---

# /publish <slug>

Turns `inbox/<slug>/post.md` and its pictures into a published post on a pull request. Rules (front matter schema, style guide, roles) are in `AGENTS.md`.

## Procedure

1. **Branch.** Never work on `master`. If on `master`, `git pull` then `git switch -c post/<slug>`. If the draft came from Hermes, `git fetch origin` and merge `origin/hermes/<slug>` into the working branch.
2. **Validate the slug.** `<slug>` must be lowercase and hyphenated, and no `_posts/*-<slug>.md` may exist (that URL is taken). The slug is the permanent URL `/posts/<slug>/`, so suggest a short, descriptive one if the folder name is poor and rename the inbox folder before publishing.
3. **Dry run.** `uv run tools/publish.py --check <slug>`. It lists missing or invalid fields and images without alt text.
4. **Fill the gaps.** Draft every missing value: `title`, `categories` (from `_data/categories.yml`), `tags` (lowercase, hyphenated), `description` (50 to 160 characters, count them), and alt text for each image. Show all drafts to the user in one batch, then write the confirmed values into `inbox/<slug>/post.md`.
5. **Edit pass.** Read the whole draft against the style guide in `AGENTS.md` (opening, banned words, em dashes, conclusion length, math syntax). For a Hermes draft, also fact-check math, code, numbers, and claims about papers or libraries; run the code when practical. Show the proposed changes and apply the ones the user accepts.
6. **Publish.** `uv run tools/publish.py <slug>`. It writes `_posts/<date>-<slug>.md`, `assets/img/posts/<slug>/` (WebP images plus `social.jpg`), moves `scripts/` to `scripts/<slug>/`, and deletes the inbox folder. Read its warnings (large GIFs, ignored files) and relay them.
7. **Check.** `bash tools/check.sh`. Fix failures and rerun. Optionally `bash tools/run.sh` and open `http://127.0.0.1:4000/posts/<slug>/` for the user to look at.
8. **Pull request.** Commit (`post: <title>`), push the branch, `gh pr create` with the URL `https://quantfin.net/posts/<slug>/`, the description, and any warnings. Merging deploys; the user merges.
9. **After merge** (when the user says it is merged): confirm the Actions deploy succeeded and the page is live, then update the vault tracker in `Fleeting Notes/QuantFin Blog.md` (move the row to Published with date, URL, categories, vault source, and word count; set `last_activity`). Follow the vault's write lock and `Log.md` rules in its `AGENTS.md`. Delete `hermes/<slug>` if it exists.

## Pitfalls

- Never rename a file in `_posts/` or set `permalink:`.
- Don't invent alt text from the filename. Look at the image (Read it) and describe what it shows.
- `publish.py` deletes `inbox/<slug>/` on success. Files other than `post.md`, referenced media, `cover.*`, and `scripts/` are not copied; it lists them first, so move anything worth keeping.
