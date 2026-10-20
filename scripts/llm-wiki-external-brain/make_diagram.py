"""
make_diagram.py: draws the data flow of the agent-maintained vault
(raw sources, the four skills, note layers, Index.md, Log.md).

Post: https://quantfin.net/posts/llm-wiki-external-brain/
Usage: python make_diagram.py [output.png]   (needs matplotlib)
"""

import sys

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = sys.argv[1] if len(sys.argv) > 1 else "vault-flow.png"

INK = "#1f2937"
MUTED = "#6b7280"
FILES = "#e8eef8"     # folders and files
SKILL = "#0b5cad"     # agent skills
HUMAN = "#fff4e0"     # human approval

fig, ax = plt.subplots(figsize=(13, 7.2), dpi=130)
ax.set_xlim(0, 13)
ax.set_ylim(0, 7.2)
ax.axis("off")


def box(x, y, w, h, text, face, color=INK, size=11, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                facecolor=face, edgecolor="none"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=size, color=color, weight=weight, linespacing=1.4)


def arrow(x1, y1, x2, y2, label="", dashed=False, rad=0.0, dx=0.0, dy=0.12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                                 color=MUTED, lw=1.4, linestyle="--" if dashed else "-",
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, ha="center", va="bottom",
                fontsize=9, color=MUTED, style="italic")


# top row: sources and capture
box(0.3, 5.3, 2.3, 1.3, "raw/\nclips, PDFs, photos\n(read-only, transient)", FILES)
box(3.4, 5.55, 1.6, 0.8, "/digest", SKILL, color="white", weight="bold")
box(5.8, 5.3, 2.6, 1.3, "Fleeting Notes/\nnew captures land here", FILES)
box(9.4, 5.55, 1.6, 0.8, "/qna", SKILL, color="white", weight="bold")
box(11.4, 5.3, 1.4, 1.3, "answer\nwith\n[[citations]]", "white", size=10)

# middle row: curation
box(0.3, 3.0, 2.3, 1.3, "Index.md\ntopic catalog,\nread first", FILES)
box(5.8, 3.0, 2.6, 1.3, "/wiki\nrebuild index,\npropose promotions", SKILL, color="white", size=10.5)
box(9.4, 3.15, 3.4, 1.0, "you approve the shortlist", HUMAN, size=10.5)

# bottom row: checks, durable notes, shared rules
box(0.3, 0.6, 2.3, 1.3, "outputs/\nlint reports,\ndrafts for review", FILES)
box(3.4, 0.85, 1.6, 0.8, "/lint", SKILL, color="white", weight="bold")
box(5.8, 0.6, 2.6, 1.3, "Literature Notes/\nPermanent Notes/", FILES)
box(9.4, 0.6, 3.4, 1.3, "AGENTS.md, skills, Log.md\nshared by Claude Code,\nCodex, Hermes Agent", "#f3f4f6", size=10.5)

arrow(2.6, 5.95, 3.4, 5.95)
arrow(5.0, 5.95, 5.8, 5.95, "new note")
arrow(8.4, 5.95, 9.4, 5.95, "reads")
arrow(11.0, 5.95, 11.4, 5.95)
arrow(10.2, 5.55, 8.4, 5.05, "save? (asks first)", dashed=True, rad=-0.15, dx=0.25, dy=-0.38)
arrow(7.1, 5.3, 7.1, 4.3)
arrow(5.8, 3.65, 2.6, 3.65, "rebuilds")
arrow(8.4, 3.65, 9.4, 3.65)
arrow(11.1, 3.15, 8.4, 1.4, "promote", rad=-0.2, dx=0.6, dy=-0.1)
arrow(5.8, 1.25, 5.0, 1.25, "scans", dy=0.1)
arrow(3.4, 1.25, 2.6, 1.25)

fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT}")
