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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.build_analysis import POST_DATA  # noqa: E402
from analysis.collect import GATE_FIELDS, GECKO_FIELDS  # noqa: E402
from analysis.format_post import normalise  # noqa: E402

# Field indices are single digits by construction, so this covers every value
# it can be asked for rather than a table that could be outgrown.
_DIGIT_WORDS = ("zero", "one", "two", "three", "four", "five",
                "six", "seven", "eight", "nine")

base = Path(__file__).resolve().parent.parent
post = (base / "post" / "index.md").read_text()
# Read here rather than beside the first rule that wants it. Two rules below
# needed the README and the second one was written above the line that opened
# it, which is the kind of ordering accident a module-level script invites.
_readme = (base / "README.md").read_text()

checks = []


def check(label, ok, detail=""):
    checks.append((label, ok, detail))


check("frontmatter present", post.lstrip().startswith("---"))
check("figures present", "{{< figure" in post,
      f"figure shortcodes: {post.count('{{< figure')}")
check("metric mapping section", "buysellratio" in post or "volumedist" in post
      or "timeoftrade" in post)
check("metrics-docs link", "dn.institute/market-health/docs" in post)
# Every dataset the post names has to be one the build mirrors. Three were
# added by hand into post/data/ and left out of POST_DATA, so nothing synced
# them and verify.py's byte-check skipped them: a dataset the article points at
# could have gone stale without a single check noticing.
_named = set(re.findall(r"data/([A-Za-z0-9_.\-]+\.csv)", post))
_unmirrored = sorted(_named - set(POST_DATA))
check("every dataset the post names is mirrored by the build",
      not _unmirrored, f"not in POST_DATA: {_unmirrored}")

# And every module that writes one of those datasets has to appear in the
# post's reproduce block. Three modules were added without it and the block
# quietly described a shorter pipeline than the one behind the numbers.
_writes = {p.name for p in (Path(__file__).resolve().parent).glob("*.py")
           if re.search(r'to_csv\(\s*DATA\s*/', p.read_text())}
_missing = sorted(m for m in _writes if f"analysis/{m}" not in post)
check("the reproduce block runs every module that writes a dataset",
      not _missing, f"absent from the post: {_missing}")

# And the other direction, which nothing asked. The rule above starts from the
# modules; this one starts from the files, and it is the one that found
# something: data/panel_run1.csv is read by relation.py and by verify.py, is
# the only pass covering all twenty-four tokens, and no module in the tree
# writes it. A reader following the README's rebuild order would have got a
# stale file or none. A dataset with no producer is either a snapshot, in which
# case it is named here with the reason, or an oversight.
_SNAPSHOTS = {
    "panel_run1.csv":
        "the first collection pass, kept because it is the only one that "
        "measured every token; panel.py replaced it with a session split that "
        "drops any token too thin to fit in a regime, so the run cannot be "
        "reproduced from the tree and is committed as data instead",
}
# Three spellings reach the same directory. Matching only the first reported
# vector.py's three files as orphans, which would have made the exemption list
# a place to hide a real gap.
_TO_CSV = re.compile(r'to_csv\(\s*(?:DATA|BASE\s*/\s*"data"|base\s*/\s*"data")'
                     r'\s*/\s*(f?)"([^"]+)"')
_producers = []
for _p in sorted((Path(__file__).resolve().parent).glob("*.py")):
    for _f, _template in _TO_CSV.findall(_p.read_text()):
        _pattern = re.escape(_template)
        if _f:
            _pattern = re.sub(r"\\\{[^}]*\\\}", ".+", _pattern)
        _producers.append(re.compile(f"^{_pattern}$"))
_orphans = sorted(
    f.name for f in (base / "data").glob("*.csv")
    if f.name not in _SNAPSHOTS
    and not any(rx.match(f.name) for rx in _producers))
check("every committed dataset has a producer or a stated reason",
      not _orphans, f"nothing writes: {_orphans}")

# The reproduce blocks name windows by label, and the labels are the one part
# of a command a reader cannot check by eye. A number sweep does not see them
# either: bumping the month in 2026-07-30 leaves every figure in both documents
# correct and every gate green, and hands a reader a command that dies on a
# directory that was never collected. Every label has to be a window that
# exists, except the one that is the argument to collect_raw.py, which is the
# example for starting a new one and so must NOT exist.
# Read as the argument of a command rather than matched as a date. A pattern
# that only recognises well-formed labels cannot see a malformed one: prefixing
# a digit turns 2026-08-05 into 2026-908-05, which stops looking like a label,
# drops out of the search and leaves the rule green over a command that dies.
# Every non-flag argument to a module under analysis/ is a window, so that is
# what gets checked, whatever shape it has been mangled into.
_COMMAND = re.compile(r"\s*python\s+analysis/(\w+)\.py\s*(.*)$")
_windows = {p.name for p in (base / "raw").iterdir() if p.is_dir()}
_examples = set()
_stale_labels = []
for _doc_name, _text in (("the post", post), ("the README", _readme)):
    for _block in re.findall(r"```.*?```", _text, re.S):
        for _line in _block.splitlines():
            _hit = _COMMAND.match(_line)
            if not _hit:
                continue
            for _arg in _hit.group(2).split("#")[0].split():
                if _arg.startswith("-"):
                    continue
                if _hit.group(1) == "collect_raw":
                    _examples.add(_arg)
                elif _arg not in _windows:
                    _stale_labels.append(f"{_doc_name}: {_arg}")
check("every window a reproduce block names was collected",
      not _stale_labels, f"no such window under raw/: {_stale_labels}")

# The post tells a reader that every `analysis/`, `tests/` or `raw/` path in it
# hangs off the repository, which is only useful if they all resolve. The post
# is republished on a wiki, where those paths have nothing to resolve against
# until the repository is named. So the sentence naming it earns a check of its
# own: it has to name the repository the badges point at, not a repository.
_REPO = "github.com/mkzung/xstocks-price-discovery"
check("the post names the repository its paths hang off",
      _REPO in post and _REPO in _readme,
      f"in post={_REPO in post} in README={_REPO in _readme}")
_named_modules = sorted({m for m in re.findall(r"`(analysis/[A-Za-z0-9_]+\.py)`", post)}
                        - {p.name for p in (base / "analysis").glob("*.py")}
                        - {f"analysis/{p.name}" for p in (base / "analysis").glob("*.py")})
check("every module the post names by path exists",
      not _named_modules, f"named but absent: {_named_modules}")
# And the example has to be one label, not one per document, or a reader
# following both is told to start two different windows.
check("the two documents offer the same new-window example",
      len(_examples) == 1 and not (_examples & _windows),
      f"collect_raw.py examples: {sorted(_examples)}, "
      f"of which already collected: {sorted(_examples & _windows)}")
# The exemption has to stay honest in the other direction too: a snapshot that
# gains a producer, or is deleted, should not sit here unnoticed.
_stale_snapshots = sorted(
    name for name in _SNAPSHOTS
    if not (base / "data" / name).exists()
    or any(rx.match(name) for rx in _producers))
check("no dataset is exempted that does not need it",
      not _stale_snapshots, f"exempted without cause: {_stale_snapshots}")

# The README repeats the post's account of the bar layouts and nothing checked
# it. Three documents now state which field is which -- the post, the README
# and alignment.py -- and only the first was tied to the tuples the collector
# selects by, so the other two could drift the moment a layout changed.
for _label, _fields, _text in (("Gate", GATE_FIELDS, _readme),
                               ("Gate", GATE_FIELDS, post),
                               ("GeckoTerminal", GECKO_FIELDS, post)):
    _layout = "`[" + ", ".join(_fields) + "]`"
    check(f"{_label}'s field order, as {'the README' if _text is _readme else 'the post'} states it",
          re.sub(r"\s+", " ", _layout) in re.sub(r"\s+", " ", _text),
          _layout[:44])
# The README opens with the finding, in the post's own figures. Three
# documents carrying the same numbers is three chances to drift, so each
# headline claim is required in the README and its figure required in the post.
_flat_readme = re.sub(r"\s+", " ", _readme)
_flat_post = re.sub(r"\s+", " ", post)
for _in_readme, _in_post in (
        ("in 21 of the 23 pair-days that can be ranked",
         "in 21 of the 23 pair-days that can be ranked"),
        ("a rank correlation of -0.93", "Rank correlation -0.93"),
        ("collected daily from 29 to 31 July 2026",
         "collected daily from 29 to 31 July 2026")):
    check(f"README and post agree on {_in_readme[:34]}",
          _in_readme in _flat_readme and _in_post in _flat_post,
          f"readme={_in_readme in _flat_readme} post={_in_post in _flat_post}")

check("the README names the field the collector wrongly read",
      f"field {_DIGIT_WORDS[GATE_FIELDS.index('open')]}, the open" in _readme,
      f"expected field {_DIGIT_WORDS[GATE_FIELDS.index('open')]}")
# The two DOIs, pinned digit for digit. The number sweep cannot check them --
# bumping a digit inside a DOI leaves every figure in the post correct -- and a
# DOI that is one character wrong resolves to nothing or, worse, to a different
# paper. Both were resolved against doi.org and returned Gonzalo and Granger,
# "Estimation of Common Long-Memory Components in Cointegrated Systems", JBES
# 1995, and Hasbrouck, "One Security, Many Markets", Journal of Finance 1995.
for _label, _doi in (("Gonzalo-Granger", "10.1080/07350015.1995.10524576"),
                     ("Hasbrouck", "10.1111/j.1540-6261.1995.tb04054.x")):
    check(f"{_label} DOI is exact", f"https://doi.org/{_doi}" in post)
# The year a reader sees, next to the identifier a reader does not. Both DOIs
# and both wiki paths carry their dates and are pinned above, but the years in
# the running prose are separate strings and the number sweep leaves them
# green: a citation can read 1996 beside a DOI that resolves to 1995 and every
# figure in the post stays correct.
for _label, _year in (("Gonzalo and Granger", "1995"), ("Hasbrouck", "1995"),
                      ("the earlier Gate.io article", "2021")):
    check(f"{_label} is cited as {_year}",
          re.search(rf"\[?{re.escape(_label)}\s+{_year}|\[{_year} Gate\.io", post)
          is not None)
# Every markdown link URL must be contiguous. The wrapper once split a URL in
# the middle of its domain, which killed both wiki links in any renderer, and
# the substring check that stood here kept passing because fragments of the
# domain were still present somewhere in the text.
_urls = re.findall(r"\]\(([^)]*)\)", post)
_broken = [u[:50] for u in _urls if re.search(r"\s", u)]
check("no link URL is broken across lines", not _broken,
      f"whitespace inside: {_broken}")
_flat_urls = [re.sub(r"\s+", "", u) for u in _urls]
check("links the two prior wiki posts", all(
    any(path in u for u in _flat_urls) for path in (
        "content/research/market-health/posts/2021-01-19-Gate-io",
        "content/research/market-health/posts/2026-06-13-bybit",
    )))
# The analysis used to live in a separate repository, so the post had to pin it
# at a commit. It lives here now, and a stale pin is worse than none: the one
# that was in the post pointed three commits back, before the robustness work
# the same paragraph describes.
check("no stale commit pin left in the post",
      not re.search(r"git checkout [0-9a-f]{7,40}", post))
# Line wrapping has to be settled, or the phrase searches in verify.py become
# hostage to whichever edit ran last.
check("line wrapping is normalised", normalise(post) == post)
# The wiki's figure convention: the first figure loads eagerly, the rest lazily.
_figs = re.findall(r"\{\{< figure[^>]*>\}\}", post)
check("first figure eager, the rest lazy",
      len(_figs) > 1 and "lazy" not in _figs[0]
      and all("lazy" in g for g in _figs[1:]))
# The accepted article template opens with Summary and closes with Scope.
# find() returns -1 for a missing heading, and -1 sorts before everything, so
# the naive ordering comparison passed precisely when Summary was absent. The
# mutation drill caught it before it could not-catch anything else.
_summary_at = post.find("## Summary")
# Every figure the README quotes in its prose has to be one the post carries,
# because the post's figures are the ones verify.py holds to the data. Fenced
# blocks are stripped first: a runtime estimate beside a command is not a claim
# about the study. One operational number survives that and is named rather
# than silently tolerated.
_OPERATIONAL = {"429"}  # the HTTP status GeckoTerminal rate-limits with
_readme_prose = re.sub(r"```.*?```", " ", _readme, flags=re.S)
_readme_prose = "\n".join(
    line for line in _readme_prose.splitlines()
    if not line.startswith(("|", "[!", "python ", "pip ")))
_FIGURE = re.compile(r"(?<![\w.\-/])\d+(?:\.\d+)?(?![\d])(?![a-zA-Z/])")
_orphans = sorted(set(_FIGURE.findall(_readme_prose))
                  - set(_FIGURE.findall(post)) - _OPERATIONAL)
check("every figure the README quotes appears in the post",
      not _orphans, f"only in the README: {_orphans}")

# The robustness section counts itself in words. Adding a check without
# updating the count, or the reverse, leaves the article miscounting its own
# argument, which no number sweep would notice.
_WORD_COUNTS = {"Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8}
_section = post[post.index("## What would have to be true"):
                post.index("## Measured again")]
_stated = re.search(r"(\w+) things could have gone wrong underneath it",
                    re.sub(r"\s+", " ", _section))
check("the robustness section counts its own checks",
      _stated is not None
      and _WORD_COUNTS.get(_stated.group(1)) == len(re.findall(r"^### ", _section, re.M)),
      f"says {_stated.group(1) if _stated else '?'}, "
      f"has {len(re.findall(r'^### ', _section, re.M))}")

check("opens with a Summary section",
      _summary_at != -1 and _summary_at < post.find("## The universe")
      and post[_summary_at:].splitlines()[0].strip() == "## Summary",
      f"found {post[_summary_at:].splitlines()[0].strip()!r}"
      if _summary_at != -1 else "no Summary heading")
# The heading has to be Scope, not merely start with it. Renaming it to
# "Scopey" left this rule green, because a substring test cannot tell a section
# from one whose name it happens to begin.
_last_heading = post.rstrip().split("## ")[-1].splitlines()[0].strip()
check("closes with a Scope section", _last_heading == "Scope",
      f"last heading is {_last_heading!r}")
check("no chestnut emoji", "\U0001f330" not in post)
check("no shipit", "shipit" not in post.lower())
check("pure ASCII", all(ord(c) < 128 for c in post))
check("no em/en dash", "—" not in post and "–" not in post)

# "tokenized" stays as spelled: it is the asset class's own name, written that
# way by the issuer and across the wiki's sources.
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
    # Detail only when something is wrong. A passing run printing "not in
    # POST_DATA: []" beside every green line buries the names a reader is
    # scanning for, and an empty list is not information.
    print(f"  [{'OK ' if ok else 'GAP'}] {label}"
          f"{'  ' + detail if detail and not ok else ''}")
print(f"\nGAPS: {bad} of {len(checks)}")
raise SystemExit(1 if bad else 0)
