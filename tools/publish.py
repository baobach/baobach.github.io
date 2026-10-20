#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["Pillow>=10.1", "PyYAML>=6"]
# ///
"""
Publish a draft from inbox/<slug>/ into _posts/.

Usage:
  uv run tools/publish.py <slug>            publish inbox/<slug>/post.md
  uv run tools/publish.py --check <slug>    validate only, write nothing
  uv run tools/publish.py --social-card SRC DEST
                                            build a 1200x630 social card from an image

What publishing does:
  - fills front matter: date (today, America/New_York), math, image
  - requires title, categories (from _data/categories.yml), tags, description (50-160 chars)
  - converts Obsidian embeds, wikilinks, and callouts to Chirpy Markdown
  - converts PNG/JPG to WebP (max 1600 px wide), copies GIF/MP4/SVG, adds size attributes
  - writes media to assets/img/posts/<slug>/ and links it with root-relative paths
    (not media_subpath: jekyll-seo-tag 2.9 resolves a relative image.path against the
    page URL, which breaks og:image)
  - builds social.jpg (1200x630) from cover.* or the first figure
  - moves inbox/<slug>/scripts/ to scripts/<slug>/
  - writes _posts/<date>-<slug>.md and deletes inbox/<slug>/

Exit codes: 0 ok, 1 error, 2 required front matter missing or invalid.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox"
POSTS = ROOT / "_posts"
SITE_URL = "https://quantfin.net"
TIMEZONE = "America/New_York"

MAX_WIDTH = 1600
WEBP_QUALITY = 80
LARGE_FILE = 1_000_000
CARD_SIZE = (1200, 630)
CARD_PADDING = 48
CARD_BG = (247, 247, 247)

RASTER_EXT = {".png", ".jpg", ".jpeg", ".webp"}
KEEP_EXT = {".gif", ".svg"}
VIDEO_EXT = {".mp4", ".webm"}
MEDIA_EXT = RASTER_EXT | KEEP_EXT | VIDEO_EXT

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_RE = SLUG_RE
DESC_MIN, DESC_MAX = 50, 160
EM_DASH = "—"

# Front matter keys Chirpy understands; anything else (e.g. Obsidian note metadata) is dropped.
KEY_ORDER = ["title", "date", "categories", "tags", "description", "math", "mermaid", "image"]
ALLOWED_KEYS = set(KEY_ORDER) | {
    "pin", "toc", "comments", "author", "authors", "render_with_liquid", "last_modified_at", "image_alt",
}

CALLOUT_TYPES = {
    "tip": "tip", "hint": "tip", "success": "tip", "check": "tip", "done": "tip",
    "note": "info", "info": "info", "abstract": "info", "summary": "info", "tldr": "info",
    "todo": "info", "question": "info", "help": "info", "faq": "info", "example": "info",
    "quote": "info", "cite": "info",
    "warning": "warning", "caution": "warning", "attention": "warning",
    "danger": "danger", "error": "danger", "bug": "danger", "failure": "danger", "fail": "danger",
    "missing": "danger",
}

MD_IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<src><[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\)(?P<attr>\{:[^}]*\})?"
)
OBS_EMBED_RE = re.compile(r"!\[\[(?P<target>[^\]|#]+)(?:#[^\]|]*)?(?:\|(?P<alt>[^\]]*))?\]\]")
WIKILINK_RE = re.compile(r"(?<!!)\[\[(?P<target>[^\]|#]*)(?:#(?P<heading>[^\]|]*))?(?:\|(?P<text>[^\]]*))?\]\]")
CALLOUT_RE = re.compile(r"^>\s*\[!(?P<type>[A-Za-z-]+)\][+-]?\s*(?P<title>.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
MATH_RE = re.compile(r"\$\$|\\\(|\$[^$\n]*(?:\\[A-Za-z]+|[\^_])[^$\n]*\$")
SIZE_ONLY_RE = re.compile(r"^\s*\d+(?:x\d+)?\s*$")


class PublishError(Exception):
    pass


# ---------------------------------------------------------------- front matter


def load_categories() -> list[str]:
    return yaml.safe_load((ROOT / "_data" / "categories.yml").read_text())


def split_front_matter(text: str) -> tuple[dict, str]:
    """Return (front matter dict, body). Missing front matter gives an empty dict."""
    if text.startswith("---"):
        m = re.match(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.S)
        if m:
            data = yaml.safe_load(m.group(1)) or {}
            if not isinstance(data, dict):
                raise PublishError("front matter is not a YAML mapping")
            return data, text[m.end():]
    return {}, text


def _yaml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_scalar_in_list(v) for v in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)


def _yaml_scalar_in_list(value) -> str:
    s = str(value)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]*", s) and s.lower() not in {"true", "false", "null", "yes", "no"}:
        return s
    return json.dumps(s, ensure_ascii=False)


def dump_front_matter(fm: dict) -> str:
    keys = [k for k in KEY_ORDER if k in fm] + [k for k in fm if k not in KEY_ORDER]
    lines = ["---"]
    for key in keys:
        value = fm[key]
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"  {sub_key}: {_yaml_value(sub_value)}")
        else:
            lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def normalize_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(v).strip() for v in value if str(v).strip()]


def normalize_tag(tag: str) -> str:
    tag = tag.strip().lstrip("#").lower()
    return re.sub(r"[^a-z0-9]+", "-", tag).strip("-")


def validate_front_matter(fm: dict, categories: list[str]) -> list[str]:
    """Return a list of problems with the required fields (empty when valid)."""
    problems = []
    title = fm.get("title")
    if not title or not str(title).strip():
        problems.append("title: missing")
    elif EM_DASH in str(title):
        problems.append("title: contains an em dash")

    cats = fm.get("categories") or []
    if not cats:
        problems.append(f"categories: missing (one or two of: {', '.join(categories)})")
    else:
        if len(cats) > 2:
            problems.append(f"categories: {len(cats)} given, use one or two")
        unknown = [c for c in cats if c not in categories]
        if unknown:
            problems.append(f"categories: not in _data/categories.yml: {', '.join(unknown)}")

    tags = fm.get("tags") or []
    if not tags:
        problems.append("tags: missing (lowercase, hyphenated)")
    else:
        bad = [t for t in tags if not TAG_RE.match(str(t))]
        if bad:
            problems.append(f"tags: not lowercase-hyphenated: {', '.join(map(str, bad))}")

    desc = fm.get("description")
    if not desc or not str(desc).strip():
        problems.append(f"description: missing ({DESC_MIN} to {DESC_MAX} characters)")
    else:
        n = len(str(desc).strip())
        if not DESC_MIN <= n <= DESC_MAX:
            problems.append(f"description: {n} characters, needs {DESC_MIN} to {DESC_MAX}")
        if EM_DASH in str(desc):
            problems.append("description: contains an em dash")
    return problems


# ---------------------------------------------------------------- body segments


def split_code(body: str) -> list[tuple[bool, str]]:
    """Split the body into (is_code, text) chunks on fenced code blocks."""
    chunks: list[tuple[bool, list[str]]] = []
    in_code = False
    fence = ""
    for line in body.splitlines(keepends=True):
        m = FENCE_RE.match(line)
        if not in_code and m:
            in_code, fence = True, m.group(1)
            chunks.append((True, [line]))
            continue
        if in_code:
            chunks[-1][1].append(line)
            if line.strip().startswith(fence) and len(chunks[-1][1]) > 1:
                in_code = False
            continue
        if not chunks or chunks[-1][0]:
            chunks.append((False, []))
        chunks[-1][1].append(line)
    return [(is_code, "".join(lines)) for is_code, lines in chunks]


def map_prose(body: str, fn) -> str:
    """Apply fn to prose only, leaving fenced and inline code untouched."""
    out = []
    for is_code, text in split_code(body):
        if is_code:
            out.append(text)
            continue
        stash: list[str] = []

        def hide(m):
            stash.append(m.group(0))
            return f"\x00{len(stash) - 1}\x00"

        hidden = INLINE_CODE_RE.sub(hide, text)
        converted = fn(hidden)
        out.append(re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], converted))
    return "".join(out)


def prose_text(body: str) -> str:
    return "".join(text for is_code, text in split_code(body) if not is_code)


# ---------------------------------------------------------------- Obsidian conversion


def convert_callouts(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = CALLOUT_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        kind = CALLOUT_TYPES.get(m.group("type").lower(), "info")
        title = m.group("title").strip()
        block = []
        i += 1
        while i < len(lines) and lines[i].startswith(">"):
            block.append(lines[i])
            i += 1
        while block and block[-1].strip() in {">", ""}:
            block.pop()
        if title:
            out.append(f"> **{title}**")
            if block:
                out.append(">")
        out.extend(block)
        out.append(f"{{: .prompt-{kind} }}")
        if i < len(lines) and lines[i].strip():
            out.append("")
    return "\n".join(out)


def published_posts() -> dict[str, str]:
    """Map lowercase slug and lowercase title to slug for every published post."""
    index: dict[str, str] = {}
    for path in POSTS.glob("[0-9]*.md"):
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
        index[slug.lower()] = slug
        try:
            fm, _ = split_front_matter(path.read_text())
        except Exception:
            continue
        if fm.get("title"):
            index[str(fm["title"]).strip().lower()] = slug
    return index


def convert_wikilinks(text: str, posts: dict[str, str]) -> str:
    def repl(m):
        target = (m.group("target") or "").strip()
        label = (m.group("text") or "").strip() or target or (m.group("heading") or "").strip()
        slug = posts.get(target.lower())
        return f"[{label}](/posts/{slug}/)" if slug else label

    return WIKILINK_RE.sub(repl, text)


def embeds_to_markdown(text: str, problems: list[str]) -> str:
    def repl(m):
        target = m.group("target").strip()
        alt = (m.group("alt") or "").strip()
        if Path(target).suffix.lower() not in MEDIA_EXT:
            problems.append(f"note embed ![[{target}]] is not supported; paste the text instead")
            return m.group(0)
        if SIZE_ONLY_RE.match(alt):
            alt = ""
        return f"![{alt}](<{target}>)"

    return OBS_EMBED_RE.sub(repl, text)


# ---------------------------------------------------------------- media


@dataclass
class Media:
    source: Path
    name: str  # output file name in assets/img/posts/<slug>/
    kind: str  # raster | keep | video
    width: int | None = None
    height: int | None = None
    warnings: list[str] = field(default_factory=list)


def safe_name(path: Path, ext: str | None = None) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-") or "image"
    return stem + (ext or path.suffix.lower())


def resolve_source(src: str, folder: Path) -> Path | None:
    src = urllib.parse.unquote(src.strip("<>"))
    candidate = (folder / src).resolve()
    if candidate.is_file() and folder.resolve() in candidate.parents:
        return candidate
    matches = [p for p in folder.rglob(Path(src).name) if p.is_file()]
    return matches[0] if len(matches) == 1 else None


def svg_size(path: Path) -> tuple[int | None, int | None]:
    head = path.read_text(errors="ignore")[:4000]
    w = re.search(r'<svg[^>]*\bwidth="([\d.]+)(?:px)?"', head)
    h = re.search(r'<svg[^>]*\bheight="([\d.]+)(?:px)?"', head)
    if w and h:
        return round(float(w.group(1))), round(float(h.group(1)))
    vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', head)
    if vb:
        return round(float(vb.group(1))), round(float(vb.group(2)))
    return None, None


def inspect_media(source: Path) -> Media:
    from PIL import Image

    ext = source.suffix.lower()
    size = source.stat().st_size
    if ext in RASTER_EXT:
        with Image.open(source) as im:
            w, h = im.size
        if w > MAX_WIDTH:
            w, h = MAX_WIDTH, round(h * MAX_WIDTH / w)
        return Media(source, safe_name(source, ".webp"), "raster", w, h)
    if ext == ".gif":
        with Image.open(source) as im:
            w, h = im.size
        media = Media(source, safe_name(source), "keep", w, h)
        if size > LARGE_FILE:
            media.warnings.append(f"{source.name} is {size / 1e6:.1f} MB; consider converting it to MP4")
        return media
    if ext == ".svg":
        w, h = svg_size(source)
        media = Media(source, safe_name(source), "keep", w, h)
        if w is None:
            media.warnings.append(f"{source.name}: no width/height found, size attributes skipped")
        return media
    media = Media(source, safe_name(source), "video")
    if size > LARGE_FILE:
        media.warnings.append(f"{source.name} is {size / 1e6:.1f} MB")
    return media


def write_media(media: Media, dest_dir: Path) -> None:
    from PIL import Image, ImageOps

    dest = dest_dir / media.name
    if media.kind != "raster":
        shutil.copy2(media.source, dest)
        return
    with Image.open(media.source) as im:
        im = ImageOps.exif_transpose(im)
        if im.width > MAX_WIDTH:
            im = im.resize((media.width, media.height), Image.LANCZOS)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() or im.mode == "P" else "RGB")
        im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)


def make_social_card(source: Path, dest: Path, fill: bool = False) -> None:
    """Build a 1200x630 JPEG. fill=True crops to cover the card; otherwise the
    image is fit inside it on a plain background, so nothing is cut off."""
    from PIL import Image, ImageOps

    cw, ch = CARD_SIZE
    with Image.open(source) as im:
        im.seek(0)
        im = ImageOps.exif_transpose(im).convert("RGBA")
    if fill:
        card = ImageOps.fit(im, CARD_SIZE, Image.LANCZOS).convert("RGB")
    else:
        box_w, box_h = cw - 2 * CARD_PADDING, ch - 2 * CARD_PADDING
        scale = min(box_w / im.width, box_h / im.height, 2.0)
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
        card = Image.new("RGB", CARD_SIZE, CARD_BG)
        card.paste(im, ((cw - im.width) // 2, (ch - im.height) // 2), im)
    dest.parent.mkdir(parents=True, exist_ok=True)
    card.save(dest, "JPEG", quality=85, optimize=True, progressive=True)


# ---------------------------------------------------------------- pipeline


def size_attr(media: Media, existing: str | None) -> str:
    inner = ""
    if existing:
        inner = re.sub(r'\b[wh]="[^"]*"', "", existing[2:-1]).strip()
    parts = []
    if media.width and media.height:
        parts.append(f'w="{media.width}" h="{media.height}"')
    if inner:
        parts.append(inner)
    return "{: " + " ".join(parts) + " }" if parts else ""


def publish(slug: str, check_only: bool) -> int:
    if not SLUG_RE.match(slug):
        raise PublishError(f"slug '{slug}' must be lowercase and hyphenated (it becomes /posts/{slug}/)")
    folder = INBOX / slug
    post_md = folder / "post.md"
    if not post_md.is_file():
        raise PublishError(f"{post_md.relative_to(ROOT)} not found")
    taken = list(POSTS.glob(f"*-{slug}.md"))
    if taken:
        raise PublishError(f"slug already published as {taken[0].relative_to(ROOT)}")
    asset_dir = ROOT / "assets" / "img" / "posts" / slug
    if asset_dir.exists():
        raise PublishError(f"{asset_dir.relative_to(ROOT)} already exists")

    categories = load_categories()
    fm, body = split_front_matter(post_md.read_text())
    notices: list[str] = []
    problems: list[str] = []

    dropped = [k for k in fm if k not in ALLOWED_KEYS]
    for key in dropped:
        del fm[key]
    if dropped:
        notices.append(f"dropped front matter keys Chirpy does not use: {', '.join(dropped)}")
    if "permalink" in dropped:
        notices.append("permalink removed: post URLs always come from the slug")

    media_url = f"/assets/img/posts/{slug}"
    fm["categories"] = normalize_list(fm.get("categories"))
    raw_tags = normalize_list(fm.get("tags"))
    fm["tags"] = list(dict.fromkeys(normalize_tag(t) for t in raw_tags if normalize_tag(t)))
    if fm.get("title"):
        fm["title"] = str(fm["title"]).strip()
    if fm.get("description"):
        fm["description"] = " ".join(str(fm["description"]).split())
    fm_problems = validate_front_matter(fm, categories)

    # Obsidian syntax, then collect media references.
    posts = published_posts()
    body = map_prose(body, lambda t: convert_wikilinks(convert_callouts(embeds_to_markdown(t, problems)), posts))

    media_by_source: dict[Path, Media] = {}
    first_figure: Media | None = None
    first_alt = ""

    def collect(m):
        nonlocal first_figure, first_alt
        alt, src = m.group("alt").strip(), m.group("src")
        if "://" in src or src.startswith("/"):
            return m.group(0)
        source = resolve_source(src, folder)
        if source is None:
            problems.append(f"image not found in inbox/{slug}/: {src.strip('<>')}")
            return m.group(0)
        if source.suffix.lower() not in MEDIA_EXT:
            problems.append(f"unsupported media type: {source.name}")
            return m.group(0)
        if not alt or alt == source.name or SIZE_ONLY_RE.match(alt):
            problems.append(f"alt text missing for {source.name}")
        media = media_by_source.get(source)
        if media is None:
            media = inspect_media(source)
            media_by_source[source] = media
        if first_figure is None and media.kind != "video" and source.suffix.lower() != ".svg":
            first_figure, first_alt = media, alt
        if media.kind == "video":
            title = alt.replace("'", "&#39;")
            return (
                f"{{% include embed/video.html src='{media_url}/{media.name}' title='{title}' "
                f"autoplay=true loop=true muted=true %}}"
            )
        return f"![{alt}]({media_url}/{media.name}){size_attr(media, m.group('attr'))}"

    body = map_prose(body, lambda t: MD_IMAGE_RE.sub(collect, t))

    names = [m.name for m in media_by_source.values()]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        problems.append(f"two images map to the same file name: {', '.join(sorted(dupes))}; rename one")
    for media in media_by_source.values():
        notices.extend(media.warnings)

    # Front matter fields the pipeline owns.
    today = dt.datetime.now(ZoneInfo(TIMEZONE)).date()
    date = fm.get("date") or today
    if isinstance(date, dt.datetime):
        date = date.date()
    if isinstance(date, str):
        try:
            date = dt.date.fromisoformat(date[:10])
        except ValueError:
            problems.append(f"date: '{date}' is not YYYY-MM-DD")
            date = today
    fm["date"] = date
    if MATH_RE.search(prose_text(body)):
        fm["math"] = True

    covers = sorted(p for p in folder.iterdir() if p.stem.lower() == "cover" and p.suffix.lower() in RASTER_EXT | {".gif"})
    card_source, card_fill, card_alt = None, False, ""
    if "image" not in fm:
        if covers:
            card_source, card_fill = covers[0], True
            card_alt = str(fm.pop("image_alt", "") or fm.get("title", ""))
        elif first_figure:
            card_source, card_alt = first_figure.source, first_alt
        if card_source:
            fm["image"] = {"path": f"{media_url}/social.jpg", "alt": card_alt}
        else:
            notices.append("no figure or cover.*: the site-wide social image is used")
    fm.pop("image_alt", None)

    if re.search(r"\{\{|\{%", "".join(t for c, t in split_code(body) if c)):
        notices.append("a code block contains '{{' or '{%'; Liquid will try to render it (wrap it in {% raw %})")

    # Files in the inbox folder that will not be published.
    used = set(media_by_source) | set(covers) | {post_md.resolve()}
    ignored = [
        p.relative_to(folder) for p in folder.rglob("*")
        if p.is_file() and p.resolve() not in used and "scripts" not in p.relative_to(folder).parts
        and p.name != ".DS_Store"
    ]
    if ignored:
        notices.append("not published (deleted with the inbox folder): " + ", ".join(map(str, ignored)))

    dest_post = POSTS / f"{date.isoformat()}-{slug}.md"
    for note in notices:
        print(f"note: {note}")
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
    if fm_problems:
        print("front matter needs:", file=sys.stderr)
        for p in fm_problems:
            print(f"  - {p}", file=sys.stderr)
    if problems:
        return 1
    if fm_problems:
        return 2

    if check_only:
        print(f"ok: would write {dest_post.relative_to(ROOT)} with {len(media_by_source)} media file(s)")
        print(f"url: {SITE_URL}/posts/{slug}/")
        return 0

    asset_dir.mkdir(parents=True)
    for media in media_by_source.values():
        write_media(media, asset_dir)
    if card_source:
        make_social_card(card_source, asset_dir / "social.jpg", fill=card_fill)
    scripts_src = folder / "scripts"
    if scripts_src.is_dir():
        scripts_dest = ROOT / "scripts" / slug
        if scripts_dest.exists():
            raise PublishError(f"{scripts_dest.relative_to(ROOT)} already exists")
        scripts_dest.parent.mkdir(exist_ok=True)
        shutil.move(str(scripts_src), scripts_dest)
    dest_post.write_text(dump_front_matter(fm) + "\n" + body.lstrip("\n"))
    shutil.rmtree(folder)

    print(f"wrote {dest_post.relative_to(ROOT)}")
    print(f"media: {asset_dir.relative_to(ROOT)}/ ({len(media_by_source)} file(s){', social.jpg' if card_source else ''})")
    print(f"url: {SITE_URL}/posts/{slug}/")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish inbox/<slug>/ to _posts/.")
    parser.add_argument("slug", nargs="?")
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    parser.add_argument("--social-card", nargs=2, metavar=("SRC", "DEST"), help="build a 1200x630 card from SRC")
    parser.add_argument("--fill", action="store_true", help="with --social-card: crop to fill instead of fitting")
    args = parser.parse_args()
    try:
        if args.social_card:
            src, dest = map(Path, args.social_card)
            make_social_card(src, dest, fill=args.fill)
            print(f"wrote {dest}")
            return 0
        if not args.slug:
            parser.error("slug is required")
        return publish(args.slug, args.check)
    except PublishError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
