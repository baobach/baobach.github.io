# inbox

Drafts waiting to be published. Jekyll ignores this folder.

```
inbox/<slug>/
  post.md          the post, Markdown (Obsidian syntax is fine)
  figure-1.png     every picture the post uses, referenced by filename
  cover.png        optional: banner and social image (cropped to 1200x630)
  scripts/         optional: code that produced the figures, moved to scripts/<slug>/
```

`<slug>` is lowercase and hyphenated, and becomes the permanent URL `https://quantfin.net/posts/<slug>/`. Copy `_template/post.md` to start.

**Front matter** is optional while drafting. To publish, the post needs `title`, `categories` (one or two from `_data/categories.yml`), `tags` (lowercase, hyphenated), and `description` (50 to 160 characters). `/publish` drafts whatever is missing and asks you to confirm. `date`, `math`, and `image` are filled in automatically.

**Pictures:** `![What it shows](figure-1.png)` or `![[figure-1.png|What it shows]]`. Alt text is required. PNG and JPG become WebP; GIF, SVG, and MP4 are copied as they are (keep GIFs under 1 MB, or use MP4).

**Obsidian:** embeds, `[[wikilinks]]` (to plain text, or to a link when the target is a published post), and callouts (`> [!tip]`, `> [!note]`, `> [!warning]`, `> [!danger]`) are converted.

**Publish:** `/publish <slug>` in Claude Code, or `uv run tools/publish.py --check <slug>` then `uv run tools/publish.py <slug>`.
