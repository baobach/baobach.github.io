#!/usr/bin/env python3
"""
wiki_lint.py: mechanical health checks for an agent-maintained Obsidian vault.

Post: https://quantfin.net/posts/llm-wiki-external-brain/
Usage: python3 wiki_lint.py [vault-path]    (standard library only)

Checks the three note folders for: missing frontmatter fields, broken
[[wikilinks]], links or sources pointing into raw/, and fully isolated notes
(no links in or out; links from Index.md and Log.md don't count). Exit code 1
when anything is found, so an agent or a git hook can act on it. Judgment calls
(contradictions, missing concept notes) stay with the /lint skill.
"""

import re
import sys
from pathlib import Path

NOTE_DIRS = ["Fleeting Notes", "Literature Notes", "Permanent Notes"]
REQUIRED = ["title", "type", "created"]
# pages that list every note; their links don't rescue a note from isolation
CATALOGS = {"index.md", "log.md", "log-hermes.md"}
WIKILINK = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def frontmatter_keys(text: str) -> set[str]:
    m = FRONTMATTER.match(text)
    if not m:
        return set()
    return {line.split(":", 1)[0].strip() for line in m.group(1).splitlines()
            if re.match(r"^[A-Za-z_][\w-]*:", line)}


def main(root: Path) -> int:
    # any file can be a link target (notes by stem, images and PDFs by name);
    # names that exist only under raw/ count as links into raw/
    def names(files):
        return {n.lower() for f in files for n in (f.stem, f.name)}

    files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    in_raw = [p for p in files if p.relative_to(root).parts[0] == "raw"]
    targets = names(p for p in files if p not in in_raw)
    raw_only = names(in_raw) - targets

    notes = [p for d in NOTE_DIRS for p in sorted((root / d).glob("*.md"))]
    outgoing: dict[str, set[str]] = {}
    problems: list[str] = []

    for note in notes:
        text = note.read_text(encoding="utf-8")
        rel = note.relative_to(root)
        missing = [k for k in REQUIRED if k not in frontmatter_keys(text)]
        if missing:
            problems.append(f"{rel}: frontmatter missing {', '.join(missing)}")
        links = set()
        for target in WIKILINK.findall(text):
            name = target.strip().split("/")[-1].lower()
            links.add(name)
            if target.strip().lower().startswith("raw/") or name in raw_only:
                problems.append(f"{rel}: links into raw/: [[{target}]]")
            elif name not in targets:
                problems.append(f"{rel}: broken link [[{target}]]")
        if re.search(r"^sources:.*\braw/", text, re.M):
            problems.append(f"{rel}: sources cites a raw/ path")
        outgoing[note.stem.lower()] = links

    # incoming links from any note or page, but not from the catalogs, raw/,
    # or hidden folders such as .claude/ whose skills hold example links
    incoming: dict[str, int] = {}
    for md in root.rglob("*.md"):
        parts = md.relative_to(root).parts
        if parts[0] == "raw" or any(part.startswith(".") for part in parts):
            continue
        if len(parts) == 1 and md.name.lower() in CATALOGS:
            continue
        for target in WIKILINK.findall(md.read_text(encoding="utf-8")):
            name = target.strip().split("/")[-1].lower()
            if name != md.stem.lower():
                incoming[name] = incoming.get(name, 0) + 1
    for note in notes:
        key = note.stem.lower()
        if not incoming.get(key) and not outgoing.get(key):
            problems.append(f"{note.relative_to(root)}: isolated (no links in or out)")

    for line in problems:
        print(line)
    print(f"{len(notes)} notes checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()))
