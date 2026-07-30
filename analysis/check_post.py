"""Mechanical checks on the post that a careful reader would otherwise have to do.

Frontmatter, figure shortcodes, the metric mapping, ASCII cleanliness, British
spelling, the repository layout, settled line wrapping, and the filler words that
weaken a sentence without adding to it. Every rule here was added after something
slipped through: a smart quote, an inconsistent spelling, a figure with no
caption, a paragraph left ragged by an interpolated number.

These are checks on form. `verify.py` checks the numbers, and the two are kept
apart so that neither can quietly pass by doing the other's job.
"""
import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.format_post import normalise  # noqa: E402

base = Path(__file__).resolve().parent.parent
post = (base / "post" / "index.md").read_text()

checks = []


def check(label, ok, detail=""):
    checks.append((label, ok, detail))


check("frontmatter present", post.lstrip().startswith("---"))
check("figures present", "{{< figure" in post,
      f"figure shortcodes: {post.count('{{< figure')}")
check("metric mapping section", "buysellratio" in post or "volumedist" in post
      or "timeoftrade" in post)
check("metrics-docs link", "dn.institute/market-health/docs" in post)
check("links a prior wiki post", "dn-institute" in post or "dn.institute" in post)
# The analysis used to live in a separate repository, so the post had to pin it
# at a commit. It lives here now, and a stale pin is worse than none: the one
# that was in the post pointed three commits back, before the robustness work
# the same paragraph describes.
check("no stale commit pin left in the post",
      not re.search(r"git checkout [0-9a-f]{7,40}", post))
# Line wrapping has to be settled, or the phrase searches in verify.py become
# hostage to whichever edit ran last.
check("line wrapping is normalised", normalise(post) == post)
check("no chestnut emoji", "\U0001f330" not in post)
check("no shipit", "shipit" not in post.lower())
check("pure ASCII", all(ord(c) < 128 for c in post))
check("no em/en dash", "—" not in post and "–" not in post)

british = {"normalize": "normalise", "summarize": "summarise",
           "analyze": "analyse", "behavior": "behaviour",
           "labeled": "labelled", "modeling": "modelling"}
found = [w for w in british if w in post.lower()]
check("British spelling", not found, f"american forms found: {found}")

overused = [w for w in ("exactly", "significantly", "notably", "clearly")
            if w in post.lower()]
check("no flagged filler", not overused, f"found: {overused}")

files = {
    "post/index.md": (base / "post" / "index.md").exists(),
    "analysis/verify.py": (base / "analysis" / "verify.py").exists(),
    "post figures": len(list((base / "post").glob("*.png"))) >= 3,
    "analysis/build_analysis.py": (base / "analysis" / "build_analysis.py").exists(),
    "dashboard/build_dashboard.py": (base / "dashboard" / "build_dashboard.py").exists(),
    "index.html": (base / "index.html").exists(),
    ".github/workflows/test.yml": (base / ".github" / "workflows" / "test.yml").exists(),
    "requirements.txt has pytest": "pytest" in (base / "requirements.txt").read_text(),
    "LICENSE": (base / "LICENSE").exists(),
    "README.md": (base / "README.md").exists(),
    "data/*.csv committed": len(list((base / "data").glob("*.csv"))) > 0,
}
for name, ok in files.items():
    check(f"file: {name}", ok)

bad = 0
for label, ok, detail in checks:
    bad += not ok
    print(f"  [{'OK ' if ok else 'GAP'}] {label}{'  ' + detail if detail else ''}")
print(f"\nGAPS: {bad} of {len(checks)}")
raise SystemExit(1 if bad else 0)
