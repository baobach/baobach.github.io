---
name: seo-audit
description: Audit every published post for SEO and accessibility (front matter, description length, social image, alt text, internal links, generated meta tags), report findings, then fix on approval. Use when the user asks for an SEO audit or check, or before a batch of posts goes out.
---

# /seo-audit

Report first, fix only what the user approves.

## Procedure

1. **Lint.** `uv run tools/lint_posts.py`. Collect errors and warnings.
2. **Per post** in `_posts/`, check beyond the linter:
   - `title` under about 60 characters (Google truncates longer titles) and specific to the content.
   - `description` reads as a search snippet: concrete, states what the reader gets, 50 to 160 characters, not a copy of the first paragraph.
   - `image:` present (a 1200x630 social card). Missing: build one with `uv run tools/publish.py --social-card <figure> assets/img/posts/<slug>/social.jpg` and set `image: {path: /assets/img/posts/<slug>/social.jpg, alt: ...}`.
   - Alt text describes the content of each image, not its file name or a generic label ("plot", "screenshot").
   - Internal links: posts in a series link to each other with `/posts/<slug>/`; related posts on the same topic link where it reads naturally.
   - Hotlinked external images (they break silently if the host moves them).
3. **Built output.** `bash tools/check.sh`, then for two or three posts read `_site/posts/<slug>/index.html` and confirm: `<meta name="description">` at most 160 characters, `og:image` and `twitter:image` present, `twitter:card` is `summary_large_image`, the JSON-LD block parses as JSON (`python3 -c "import json,sys; json.loads(...)"`), and `<link rel="canonical">` points to `https://quantfin.net/posts/<slug>/`.
4. **Report** as one list grouped by post, most important first. Propose concrete replacement text for titles, descriptions, and alt text.
5. **Fix** what the user approves, rerun `bash tools/check.sh`, and commit on a branch (never `master`).

## Pitfalls

- Never rename a post file or set `permalink:` to "improve" a URL; it breaks the live URL.
- No em dashes in titles or descriptions.
