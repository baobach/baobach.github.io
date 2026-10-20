# quantfin.net

Source for [quantfin.net](https://quantfin.net), a blog on quantitative finance, mathematics, and machine learning by Robert Bach.

## Stack

- [Jekyll](https://jekyllrb.com) with the [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) theme gem. Ruby version is pinned in `.ruby-version`; gems are locked in `Gemfile.lock`.
- GitHub Pages, deployed by GitHub Actions. Pull requests run the checks; a push to `master` builds, checks, and deploys the live site.
- Custom domain `quantfin.net` (set in the repository's Pages settings).

Post URLs are `/posts/<slug>/`, where `<slug>` is the post filename without the date. Never rename an existing file in `_posts/`: that changes its URL.

## Layout

```
_posts/            published posts, YYYY-MM-DD-<slug>.md
_tabs/             sidebar pages (about, archives, categories, tags)
_data/             contact icons, share buttons, controlled category list
_plugins/          last-modified date from git history
assets/img/posts/  images for new posts, one folder per slug
assets/img/blog/   images for posts written before 2026 (left in place)
inbox/             drafts waiting to be published (not built)
scripts/<slug>/    code that generated a post's figures or results (not built)
tools/             run.sh, check.sh, publish.py, lint_posts.py
AGENTS.md          instructions and writing style for AI agents
```

## Publish a post

1. Create `inbox/<slug>/post.md` and put every picture it uses next to it. Reference pictures by filename, e.g. `![Payoff of a long call](payoff.png)` or the Obsidian form `![[payoff.png]]`. Front matter is optional; see `inbox/README.md`.
2. In Claude Code, run `/publish <slug>`. It fills in missing front matter (and asks you to confirm), converts images to WebP, moves everything into place, runs the checks, and opens a pull request.
3. Merge the pull request. The site deploys in a couple of minutes.

To run the pipeline by hand: `uv run tools/publish.py <slug>`.

## Local development

```bash
bundle install
bash tools/run.sh        # serve at http://127.0.0.1:4000 with live reload
bash tools/check.sh      # production build, htmlproofer, post linter (same as CI)
```

## Agents

Two AI agents work in this repo. Both read `AGENTS.md`.

- **Claude Code** (on the Mac) owns structure and publishing: config, CI, tooling, theme upgrades, SEO, final edits, `/publish`, and merging into `master` after approval.
- **Hermes Agent** (on dsg-lab-2) is a drafting assistant. It writes first drafts into `inbox/<slug>/` on `hermes/<slug>` branches and never touches anything else. Claude fact-checks every Hermes draft before it is published.

## License

`LICENSE` is the MIT license inherited from the [Chirpy starter](https://github.com/cotes2020/chirpy-starter) (copyright Cotes Chung).
