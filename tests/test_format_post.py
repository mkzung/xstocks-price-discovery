"""The wrapper has already shipped one real regression; it does not get a pass.

It split a URL in the middle of its domain, which killed both wiki links in
every renderer, and nothing here would have noticed because the module had no
tests at all. These hold it to the properties the post depends on.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.format_post import normalise  # noqa: E402

LONG_URL = ("https://github.com/1712n/dn-institute/tree/main/content/research/"
            "market-health/posts/2021-01-19-Gate-io")


def test_a_long_url_is_never_split() -> None:
    # The regression that shipped: a link URL longer than the wrap width was
    # broken at the width, mid-domain.
    text = ("Some prose before the link sits here to force wrapping. The "
            f"[first article]({LONG_URL}) said something worth citing, and the "
            "sentence keeps going long enough to need several wrapped lines "
            "afterwards as well.\n")
    settled = normalise(text)
    assert LONG_URL in settled


def test_a_url_already_broken_is_healed() -> None:
    broken = (f"Prose around a wounded link. The [first article]("
              f"{LONG_URL[:40]}\n{LONG_URL[40:]}) still has to work after "
              "settling.\n")
    assert LONG_URL not in broken
    assert LONG_URL in normalise(broken)


def test_a_split_compound_is_rejoined() -> None:
    text = ("The augmented Dickey-\nFuller regression on each spread has to "
            "come back out as one word pair.\n")
    settled = normalise(text)
    assert "Dickey-Fuller" in settled
    assert "Dickey- Fuller" not in settled


def test_settling_is_idempotent() -> None:
    # If a second pass changes anything, the --check gate in CI oscillates
    # between red and green depending on who ran last.
    text = ("---\ntitle: \"t\"\n---\n\nA paragraph that is long enough to be "
            "wrapped by the normaliser across more than a single line of "
            "output text, with a [link](https://example.com/a/b) inside it.\n\n"
            "| a | b |\n|---|---|\n| 1 | 2 |\n")
    once = normalise(text)
    assert normalise(once) == once


def test_tables_figures_and_code_are_untouched() -> None:
    block = ("| token | value |\n|-------|------:|\n| TSLAX | 0.89 |\n\n"
             "{{< figure src=\"a.png\" alt=\"a\" caption=\"c\" >}}\n\n"
             "```bash\npython x.py --flag\n```\n")
    settled = normalise(block)
    for fragment in ("| TSLAX | 0.89 |", "{{< figure", "```bash",
                     "python x.py --flag"):
        assert fragment in settled
