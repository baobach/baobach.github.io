#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6"]
# ///
"""
Validate every post in _posts/ against the front matter schema in AGENTS.md.

Usage: uv run tools/lint_posts.py [files...]

Errors (exit 1): missing title/categories/tags/description, category not in
_data/categories.yml, more than two categories, tags not lowercase-hyphenated,
description outside 50-160 characters, em dash in title or description,
permalink set, bad file name, local image or video missing on disk, image
without alt text, social image without alt, mdc: links.
Warnings: local raster image without size attributes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish import (  # noqa: E402
    MD_IMAGE_RE,
    POSTS,
    ROOT,
    load_categories,
    map_prose,
    prose_text,
    split_front_matter,
    validate_front_matter,
)

FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
VIDEO_INCLUDE_RE = re.compile(r"\{%\s*include\s+embed/video\.html\s+src=['\"]([^'\"]+)['\"]")
HTML_SRC_RE = re.compile(r"<(?:img|source|video)\b[^>]*\bsrc=\"([^\"]+)\"")
SIZED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def local_path(src: str, subpath: str | None) -> Path | None:
    """Disk path for a media reference, or None for remote URLs."""
    src = src.strip("<>")
    if "://" in src or src.startswith("data:"):
        return None
    if not src.startswith("/"):
        src = f"{(subpath or '').rstrip('/')}/{src}"
    return ROOT / src.lstrip("/")


def lint(path: Path, categories: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not FILENAME_RE.match(path.name):
        errors.append("file name must be YYYY-MM-DD-<lowercase-hyphenated-slug>.md")
    try:
        fm, body = split_front_matter(path.read_text())
    except Exception as exc:  # malformed YAML
        return [f"front matter does not parse: {exc}"], []
    if not fm:
        return ["no front matter"], []

    fm["categories"] = fm.get("categories") or []
    if isinstance(fm["categories"], str):
        fm["categories"] = [fm["categories"]]
    fm["tags"] = fm.get("tags") or []
    if isinstance(fm["tags"], str):
        fm["tags"] = [fm["tags"]]
    errors += validate_front_matter(fm, categories)
    if "permalink" in fm:
        errors.append("permalink is set; post URLs must come from the file name")
    if "mdc:" in body:
        errors.append("contains an mdc: link (Cursor syntax)")

    subpath = fm.get("media_subpath")
    image = fm.get("image")
    if image:
        img_path = image.get("path") if isinstance(image, dict) else image
        disk = local_path(str(img_path), subpath)
        if disk and not disk.is_file():
            errors.append(f"image: {img_path} not found")
        if not isinstance(image, dict) or not image.get("alt"):
            errors.append("image: alt text missing")

    def check_image(m):
        alt, src = m.group("alt").strip(), m.group("src")
        disk = local_path(src, subpath)
        if not alt:
            errors.append(f"alt text missing: {src}")
        if disk is not None:
            if not disk.is_file():
                errors.append(f"image not found: {src}")
            elif disk.suffix.lower() in SIZED_EXT and not re.search(r'\bw="\d+"', m.group("attr") or ""):
                warnings.append(f"no size attributes: {src}")
        return m.group(0)

    map_prose(body, lambda t: MD_IMAGE_RE.sub(check_image, t))
    prose = prose_text(body)
    for src in VIDEO_INCLUDE_RE.findall(prose) + HTML_SRC_RE.findall(prose):
        disk = local_path(src, subpath)
        if disk is not None and not disk.is_file():
            errors.append(f"media not found: {src}")
    return errors, warnings


def main(argv: list[str]) -> int:
    categories = load_categories()
    files = [Path(a) for a in argv] or sorted(p for p in POSTS.glob("*.md") if not p.name.startswith("_"))
    n_errors = 0
    for path in files:
        errors, warnings = lint(path, categories)
        rel = path.resolve().relative_to(ROOT)
        for e in errors:
            print(f"{rel}: error: {e}")
        for w in warnings:
            print(f"{rel}: warning: {w}")
        n_errors += len(errors)
    print(f"{len(files)} post(s) checked, {n_errors} error(s)")
    return 1 if n_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
