"""Machine-check every quantitative claim in post/index.md against the committed CSVs.

Each check has two legs. The first recomputes a value from `data/`, which
catches a data refresh that moved a number. The second searches the document for
that value formatted the way the prose writes it, which catches the case the
first cannot see: the data is fine and the sentence is stale. The second leg is
the point. An earlier version had only the first, compared computed values
against hardcoded constants, and never opened the post at all.

Four surfaces carry the findings and for a long time one of them was checked.

The post. Bumping each of the 238 distinct numbers in it turns every one red,
and prepending a digit does the same. Its four tables are compared cell for cell, which is where
55 of 69 unguarded numbers turned up the first time anyone looked.

index.html. The workflow diff proves the page matches its builder, not the data,
so a builder reading speed_dex where it means speed_cex ships a page that is
wrong, regenerable and green. Its figures are checked here, anchored on the
element they sit in because the correlation appears twice and a bare search
passed while one of the two sites was wrong. Its three data tables are compared
from what each column means rather than from what the builder writes. 100 of its
105 distinct numbers go red; the five left are line heights and font weights.

README.md. Held only by check_post's rule that every number it quotes appears
somewhere in the post, which is not verification: it fires because 99 happens to
be absent and stops the day a sentence introduces one. Bumping each of the
twenty-eight numbers in the README left fourteen standing, eleven of them
claims. 26 of 28 now; the two left are a bump that lands on another collected
window and a runtime estimate.

The module docstrings, read by whoever reuses the code and by nobody else, so
they drift in private. They carry 39 figures between them and two were wrong:
discovery.py gave the near-even recovery as a rate off twelve runs, the framing
the post had already corrected, and dependence.py said two tokens share 86
usable minutes when they share 79. 31 of the 39 go red; the eight left are
formula symbols, a unit, and a note about a collection that failed.

Five mutation sweeps, and each of them had to be fixed before it measured
anything.

Bumping a digit, and prepending one. Prepending is the corruption a bump cannot
make: it turns 16 into 916, and a plain substring test finds "16 cents" inside
"916 cents", so every phrase search here is anchored.

Flipping direction words in every claim-bearing sentence, leads for follows,
above for below, exchange for pool. 72 of 93 go red, and the thirty-five
DIRECTIONS entries below are what closed the gap, by tying a phrase to a sign in
the data rather than requiring it to exist. Four cover figure captions and alt
text, which is the entire figure for a reader using a screen reader.

Deleting the negation, since dropping a "not" inverts a claim without moving a
digit or touching a word the flip sweep tries. 76 sentences qualify and 60
deletions still pass, most of them prose where the inverted sentence is merely
odd. The rest are named rather than transcribed into a check apiece, which would
test each sentence against itself.

Swapping a unit or a comparator, which moves no digit at all. Three claims fell:
a correction speed given as a bound, an artefact range in a caption, and the
one-minute bar the study samples at, which read the same as "five-minute".
Figures spelled out in words are invisible to a digit sweep too, which is how a
hundred and twenty-seven thousand dollars of turnover sat unguarded.

Dropping a minus sign, which the first four patterns all refused to match, so no
signed figure had ever been mutated: not the rank correlation the second finding
rests on, not AMZNX's pool lead, not one correction speed. Dropping the sign and
bumping the last digit of each of the seventeen signed figures goes red now. A sweep reports what its own pattern can see, so
its silence is evidence about the part of the document the pattern matches and
nothing else.

Five things about running one, each learned by getting it wrong. Match numbers
with a pattern that allows a full stop after them, or every figure ending a
sentence is invisible: six were. Pass `--sweep`, which drops the five checks
that count distinct numbers, because a bump to a value the document already
holds merges two tokens and reddens the check whatever it sat next to; 93 of the
post's bumps collide that way, 37 of the page's, 6 of the README's. Rewrap the
post before judging, or a mutation that changes a line's length trips the
wrapping rule and scores as caught while its meaning went untested, which alone
moved the direction figure from 85 of 89 to 72 of 93. Clear the results file
before re-running a range, or a chunk re-run after a timeout appends twice and
reports gaps that are green one by one. And check the gate is green before the
first mutation, because a gate that cannot import scores every mutation as
caught: a name defined below the list that read it turned a run of nine into
nine of nine.

The sweeps have earned it. They found the robustness table shipping uncompared,
the lede's tally unguarded in both places it is made, the strict rule's own band
movable while every count stayed green, the citation years free to disagree with
the DOIs beside them, and the unit on every coefficient in the post.

"""
import ast
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from analysis.bootstrap import sign_test
from analysis.collect import GATE_FIELDS, GECKO_FIELDS
from analysis.dependence import MIN_OVERLAP, effective_pairs, minute_changes
from analysis.collect import MIN_CEX_VOLUME
from analysis.robustness import MIN_PAIRED
from analysis.relation import spearman, test_relation


def _flat(text: str) -> str:
    """Collapse every run of whitespace to one space.

    Searches run against the flattened post so that a phrase is found wherever
    the line break inside it happens to fall. Matching the raw text made every
    check hostage to the wrap: rewrapping one paragraph reddened a dozen checks
    that were about numbers, not layout, and the fix each time was to move a
    newline inside a search string, which is not verification of anything.
    """
    return re.sub(r"\s+", " ", text)

_SPELLED = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
            7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven",
            12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
            16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
            20: "twenty", 21: "twenty-one", 22: "twenty-two",
            23: "twenty-three", 24: "twenty-four", 26: "twenty-six",
            35: "thirty-five", 60: "sixty", 96: "ninety-six"}


def _WORDS_LOW(n: int) -> str:
    """The word for a count, or the digits if the post would not spell it.

    A bare dict lookup here crashed the whole file with a KeyError the moment a
    count moved outside the table, which reads in CI as broken tooling rather
    than as a claim that drifted. A miss now produces a search string that
    will not be found, so the check fails and names itself.
    """
    return _SPELLED.get(int(n), str(int(n)))

def _present(phrase: str, haystack: str) -> bool:
    """Is the phrase in the text, and not as part of a longer number.

    A plain substring test says yes to "0.43" inside "10.43" and to "16 cents"
    inside "916 cents". Fifty-four of the searches below begin with the value
    they are checking and so carried that hole; a prepended digit was the one
    corruption the mutation sweep never tried. The phrase is anchored here
    instead: no digit or decimal point may sit immediately before it when it
    opens with a digit, nor immediately after when it ends with one.
    """
    pattern = re.escape(_flat(phrase))
    if _flat(phrase)[:1].isdigit():
        pattern = r"(?<![\d.])" + pattern
    if _flat(phrase)[-1:].isdigit():
        pattern = pattern + r"(?![\d])"
    return re.search(pattern, haystack) is not None


base = Path(__file__).resolve().parent.parent
u = pd.read_csv(base / "data" / "universe.csv")
d = pd.read_csv(base / "data" / "panel_run1.csv")
p = pd.read_csv(base / "data" / "panel_sessions.csv")
m = pd.read_csv(base / "data" / "venue_matrix.csv")
g = pd.read_csv(base / "data" / "token_groups.csv")
post = (base / "post" / "index.md").read_text()

u["ratio"] = u.cex_volume_24h / u.dex_volume_24h.clip(lower=1)
allr = p[p.regime == "all"].dropna(subset=["w_cex"])
closed = p[p.regime == "closed"].dropna(subset=["w_cex"])
rest = allr[allr.symbol != "AMZNX"]
byrow = allr.set_index("symbol")
gap = p.pivot_table(index="symbol", columns="regime",
                    values="mean_gap_pct").dropna(subset=["open", "closed"])
bybit = m[m.venue_a == "bybit"].dropna(subset=["weight_a"]).iloc[0]
pools = m[m.venue_a == "pool_deep"].dropna(subset=["weight_a"])
ranked = g[g.group == "ranked"]
thin = g[g.group == "thin"]
dead = g[g.group == "no on-chain market"]
trimmed = g.sort_values("ratio").iloc[:-6]
rho = spearman(g.paired_min, g.ratio)
rel = test_relation(g.paired_min, g.ratio, draws=20000, seed=0)

# The four wrong-sign exchange coefficients split into two that are noise and
# two that are small but real; the post names all four values.
wrong = allr[allr.speed_cex > 0].speed_cex.sort_values()
noise, real_wrong = wrong.iloc[:2], wrong.iloc[2:]

# Share of the paired window with the US equity market shut.
closed_share = (p[p.regime == "closed"].minutes.sum()
                / p[p.regime == "all"].minutes.sum())

# The robustness section restates a second window's results and the sensitivity
# sweeps. It is the same hand-typed layer as the tables above and gets the same
# treatment.
LABEL = "2026-07-29b"
FIRST_DAY = LABEL.rstrip("ab")
rob = pd.read_csv(base / "data" / f"robustness_{LABEL}.csv")
ranked_pairs = rob[rob.verdict == "ranked"]
# Minutes between one paired observation and the next, per ranked pair, read
# off the committed series rather than assumed to be one.
_steps = pd.DataFrame({
    _s: pd.Series(pd.read_csv(base / "raw" / LABEL / f"{_s}.csv",
                              index_col="ts").index).diff().dropna() / 60
    for _s in ranked_pairs.symbol})
_spacing = pd.read_csv(base / "data" / "spacing.csv")
_spacing_tight = _spacing[_spacing.mean_step_min <= _spacing.mean_step_min.median()]
_spacing_wide = _spacing[_spacing.mean_step_min > _spacing.mean_step_min.median()]
# The largest of the three correlations against what a sample this size can
# resolve. Both halves of the null the article states rest on this comparison.
_spacing_strongest = max(
    abs(spearman(_col, _spacing.w_cex))
    for _col in (_spacing.mean_step_min, _spacing.paired_minutes,
                 _spacing.fill_rate))
_spacing_resolvable = 1.96 / (len(_spacing) - 1) ** 0.5
_grid_tslax = pd.read_csv(
    base / "data" / f"sensitivity_grid_{LABEL}.csv"
).query("symbol == 'TSLAX'").set_index("grid")
stale_risk = pd.read_csv(base / "data" / f"sensitivity_staleness_{LABEL}.csv")
ranked_risk = stale_risk[stale_risk.symbol.isin(ranked_pairs.symbol)]
rep = pd.read_csv(base / "data" / f"sensitivity_replication_{LABEL}.csv")
lag_sweep = pd.read_csv(base / "data" / f"sensitivity_lags_{LABEL}.csv")
grid_sweep = pd.read_csv(base / "data" / f"sensitivity_grid_{LABEL}.csv")
grid_fitted = grid_sweep.dropna(subset=["w_cex"])
lag_flips = int((lag_sweep.groupby("symbol").leads.nunique() > 1).sum())
grid_agree = int((grid_fitted.groupby("symbol").leads.nunique() == 1).sum())
# The later collection days, and the cross-window comparison built from them.
SECOND = "2026-07-30"
THIRD = "2026-07-31"
day2 = (pd.read_csv(base / "data" / "windows_relation.csv")
        .set_index("window").loc[SECOND])
day2_universe = pd.read_csv(base / "raw" / SECOND / "universe.csv")
day2_coverage = pd.read_csv(base / "raw" / SECOND / "coverage.csv")
day2_rob = pd.read_csv(base / "data" / f"robustness_{SECOND}.csv")
day2_ranked = day2_rob[day2_rob.verdict == "ranked"]
day2_vec = pd.read_csv(base / "data" / f"vector_{SECOND}.csv")
day3 = (pd.read_csv(base / "data" / "windows_relation.csv")
        .set_index("window").loc[THIRD])
day3_universe = pd.read_csv(base / "raw" / THIRD / "universe.csv")
day3_coverage = pd.read_csv(base / "raw" / THIRD / "coverage.csv")
day3_rob = pd.read_csv(base / "data" / f"robustness_{THIRD}.csv")
day3_ranked = day3_rob[day3_rob.verdict == "ranked"].set_index("symbol")

# The lede's joint claim: pair-days across every series pass, each day's ranked
# pairs counted once, led where the weight clears an even split. The mutation
# sweep found both numbers unguarded in the description and the lede.
pair_days = len(ranked_pairs) + len(day2_ranked) + len(day3_ranked)
led_days = (int((ranked_pairs.w_cex > 0.5).sum())
            + int((day2_ranked.w_cex > 0.5).sum())
            + int((day3_ranked.w_cex > 0.5).sum()))
both_windows = pd.read_csv(base / "data" / "windows_leadership.csv", index_col=0)
both_windows = (both_windows[both_windows.windows_ranked >= 2]
                .sort_values("spread_across_windows"))

# TSLAX is the token the registry uses to show the four passes disagree.
tslax_counts = [
    int(d.set_index("symbol").loc["TSLAX"].paired_min),
    int(byrow.loc["TSLAX"].minutes),
    int(pd.read_csv(base / "raw" / LABEL / "coverage.csv")
        .set_index("symbol").loc["TSLAX"].paired_minutes),
    int(pd.read_csv(base / "raw" / SECOND / "coverage.csv")
        .set_index("symbol").loc["TSLAX"].paired_minutes),
    int(pd.read_csv(base / "raw" / THIRD / "coverage.csv")
        .set_index("symbol").loc["TSLAX"].paired_minutes),
]

vec = pd.read_csv(base / "data" / f"vector_{LABEL}.csv")
vecrow = vec.set_index("symbol")
sim = pd.read_csv(base / "data" / "staleness.csv")
hold_false = (sim[sim.scheme == "hold"].groupby("keep")
              .apply(lambda s: float((s.w_cex > 0.5).mean()),
                     include_groups=False))

collisions = pd.read_csv(base / "data" / "collisions.csv")
registry = pd.read_csv(base / "data" / "registry_check.csv")
shut_pairs = (pd.read_csv(base / "data" / "sessions_from_series.csv")
              .dropna(subset=["w_shut"]))
# The two counts match at 17, which reads like stability and is not: one pair
# crosses each way. The post names both crossings, so both are checked here.
STRICT_LOW, STRICT_HIGH = 0.3, 0.7
shut_flip = shut_pairs[(shut_pairs.w_all > 0.5) != (shut_pairs.w_shut > 0.5)]
flip_by = shut_flip.set_index("symbol")
# Two claims in that paragraph are qualitative, so the number checks cannot see
# them: that AMZNX is a pool lead in both regimes, and that the strict band
# swallows all four crossing weights. Both are encoded as counts and checked.
amznx_shut = shut_pairs[shut_pairs.symbol == "AMZNX"]
amznx_pool_both = int(((amznx_shut.w_all < 0.5)
                       & (amznx_shut.w_shut < 0.5)).sum())
flip_weights = list(shut_flip.w_all) + list(shut_flip.w_shut)
flip_in_band = sum(STRICT_LOW <= float(w) <= STRICT_HIGH
                   for w in flip_weights)

# The window each pass actually covers, read off the raw epochs rather than
# taken from the pass label. Nothing checked this: the labels say 29 to 31 July
# while the earliest bar falls on the 28th, and a study whose split turns on
# market hours cannot leave that for the reader to reconstruct. The numeric leg
# is the first bar's epoch, so a re-collection that moved the window fails on
# the data as well as on the prose.
def _pass_window(label: str) -> tuple[int, int, str]:
    lo = hi = None
    for path in (base / "raw" / label).glob("*.csv"):
        if path.stem in ("coverage", "universe"):
            continue
        stamps = pd.read_csv(path, usecols=["ts"]).ts
        low, high = int(stamps.min()), int(stamps.max())
        lo = low if lo is None or low < lo else lo
        hi = high if hi is None or high > hi else hi
    fmt = "%-d %B %H:%M"
    return lo, hi, (f"{pd.to_datetime(lo, unit='s', utc=True).strftime(fmt)} to "
                    f"{pd.to_datetime(hi, unit='s', utc=True).strftime(fmt)}")


WINDOWS = [_pass_window(x) for x in (LABEL, SECOND, THIRD)]

# The dependence measurement behind the sign test's null. Read from the
# committed table rather than recomputed, like every other check here.
dep = pd.read_csv(base / "data" / "dependence.csv")
dep_first = dep[dep.window == LABEL].set_index("leg")
n_ranked = len(ranked_pairs)
n_effective = effective_pairs(n_ranked, float(dep_first.loc["spread"]["mean"]))

# What the pairs below the paired-minute floor say, so the cut can be shown
# not to select on the outcome. Read from the committed table.
thr = pd.read_csv(base / "data" / "threshold.csv")
thr_fit = thr.dropna(subset=["w_cex"])
thr_kept = thr_fit[thr_fit.kept]
thr_below = thr_fit[~thr_fit.kept]
thr_outside = int(((thr_below.w_cex < 0) | (thr_below.w_cex > 1)).sum())
thr_refused = int(thr.w_cex.isna().sum())

# The bar-alignment comparison: what reading Gate's open instead of its close
# cost, refitted from the same committed minutes.
align = pd.read_csv(base / "data" / "alignment.csv")
align_fit = align.dropna(subset=["w_realigned"])
_amznx = align[align.symbol == "AMZNX"].iloc[0]
# Three documents said the correction moves "every" weight towards the
# exchange. It moves twenty-one of twenty-three; two move the other way. The
# argument survives -- both are smaller than a hundredth and neither changes a
# leader -- but "every" was a word nothing could have caught, since it carries
# no digit for a number sweep and no direction word for a flip sweep. What is
# load-bearing is not that the move is universal, it is that the exchange side
# gains nothing to set against the pool reading the correction costs, so that
# is what is stated and what is checked.
_align_move = align_fit.w_realigned - align_fit.w_as_collected
# Strictly towards. No pair sits at exactly zero today, so the two readings
# agree, but "moves towards the exchange" is not a thing a weight that did not
# move has done, and the check should mean what the sentence means.
_align_towards = int((_align_move > 0).sum())
_align_against_max = float(_align_move[_align_move < 0].abs().max())
_align_leads_lost = int(((align_fit.w_as_collected > 0.5)
                         & (align_fit.w_realigned <= 0.5)).sum())


def _strict_class(weight: float) -> str:
    if weight > STRICT_HIGH:
        return "exchange"
    return "pool" if weight < STRICT_LOW else "unclassified"


# Defined beside the rest of the alignment arithmetic rather than beside the
# first check that wanted it. Two lists further down both read these, and the
# one written earlier in the file crashed on a name the one written later had
# introduced.
_pool_before = sum(_strict_class(w) == "pool" for w in align_fit.w_as_collected)
_pool_after = sum(_strict_class(w) == "pool" for w in align_fit.w_realigned)

# The strict predeclared tally. The band is named here rather than typed into
# three comparisons and again into the post: the sweep found that moving 0.3 or
# 0.7 in the prose changed the stated rule while every count stayed green, so
# the prose is now checked against the same two constants the counting uses.
strict_ex = strict_pool = strict_near = 0
for _day in (ranked_pairs, day2_ranked, day3_ranked.reset_index()):
    strict_ex += int((_day.w_cex > STRICT_HIGH).sum())
    strict_pool += int((_day.w_cex < STRICT_LOW).sum())
    strict_near += int(((_day.w_cex >= STRICT_LOW)
                        & (_day.w_cex <= STRICT_HIGH)).sum())

matched = pd.read_csv(base / "data" / "staleness_matched.csv")
matched = matched[matched.fitted]
matched_1000_50 = matched[(matched.n == 1000) & (matched.keep == 0.5)]
matched_1000_12 = matched[(matched.n == 1000) & (matched.keep == 0.12)]

cal = pd.read_csv(base / "data" / "calibration.csv")
lead = cal[~cal.even]
near = lead[(lead.truth - 0.5).abs() < 0.2]
far = lead[(lead.truth - 0.5).abs() >= 0.2]
rank_clear = ((far.weight_a > 0.5) == (far.truth > 0.5)).mean()
rank_near = ((near.weight_a > 0.5) == (near.truth > 0.5)).mean()

# label, computed value, the value the pipeline produced, and the exact string
# the post must contain for that value. The string is built from the computed
# value, so a data refresh that moves a number also moves what the post has to
# say before this passes.
checks = [
    ("24 paired tokens", len(u), 24, f"**{len(u)} tokens quoted on both venues**"),
    ("token count in the description", len(u), 24,
     f"measured on {len(u)} xStocks quoted at once"),
    ("max ratio", round(u.ratio.max()), 7311, f"**{round(u.ratio.max()):,} dollars**"),
    ("min ratio", round(u.ratio.min(), 2), 0.16, f"{u.ratio.min():.2f} cents".replace("0.", "")),
    ("median ratio", round(u.ratio.median(), 1), 6.8, f"The median is {u.ratio.median():.1f}."),
    ("nine rankable", len(allr), 9, f"| {len(allr)} | {ranked.paired_min.median():.0f} |"),
    ("all exchange-led", int((allr.w_cex > 0.5).all()), 1,
     "in that pass the exchange leads every one"),
    ("four weights above one", int((allr.w_cex > 1).sum()), 4,
     f"That is why {'four' if (allr.w_cex > 1).sum() == 4 else 'ERR'} of the nine exchange"),
    ("eight-pair exchange speed", round(rest.speed_cex.abs().max(), 2), 0.08,
     f"moves at most {rest.speed_cex.abs().max():.2f} of the gap per observation"),
    # The caption's unit, not only its numbers. Swapping "percent" for "basis
    # points" there is a hundredfold change in the artefact risk being claimed,
    # and it passed. Written as an ordinary two-leg check: the first attempt
    # put it among the direction entries with the presence test as its own
    # condition, which compares a thing to itself and can never fail.
    ("the staleness caption keeps its unit",
     round(float(ranked_risk.false_lead_drop.max()), 2), 0.19,
     f"lower curve, between {ranked_risk.false_lead_drop.min() * 100:.0f} and "
     f"{ranked_risk.false_lead_drop.max() * 100:.0f} percent"),
    # Figures written out in words. The number sweep mutates digits and never
    # sees these, and the ACNX sentence carries three of them: an exchange
    # turnover, a pool's whole liquidity, and the minutes they overlapped.
    ("ACNX turnover, spelled out",
     int(u.set_index("symbol").loc["ACNX"].cex_volume_24h), 127448,
     "The exchange reports a hundred and twenty-seven thousand dollars of "
     "turnover"),
    ("ACNX liquidity, spelled out",
     int(u.set_index("symbol").loc["ACNX"].dex_liquidity), 225,
     "entire on-chain market is two hundred and twenty-five dollars of "
     "liquidity"),
    ("the arbitrage-cannot-bind figure, spelled out",
     int(u.dex_liquidity.min()), 225,
     "arbitrage cannot bind on a pool holding two hundred dollars"),
    ("the ranked pairs the null is asked about, spelled out",
     len(ranked_pairs), 7,
     "That null treats the seven pairs as seven separate draws"),
    ("pool speed span", round(rest.speed_dex.min(), 2), 0.22,
     f"while the pool closes {rest.speed_dex.min() * 100:.0f} to "
     f"{rest.speed_dex.max() * 100:.0f} percent of it"),
    # The same two speeds are restated in the closing argument, with the
    # exchange's given as a bound. Swapping "at most" for "at least" there left
    # every check green, because nothing searched past the number.
    ("the speeds where the argument restates them",
     round(rest.speed_dex.min(), 2), 0.22,
     f"the pool closes {rest.speed_dex.min() * 100:.0f} to "
     f"{rest.speed_dex.max() * 100:.0f} percent of the gap per observation "
     f"while the exchange closes at most {rest.speed_cex.abs().max() * 100:.0f}"),
    # What one step of the fit actually spans. The coefficients were read as a
    # rate per minute in six places, and a rate per minute is what they are
    # only where a pool traded in nearly every minute. Untraded minutes are
    # dropped, so a step is one observation to the next, and on the ranked
    # pairs that is a median of one minute for four of the seven and a mean of
    # two to eight. Nothing had measured the spacing the whole reading rests on.
    ("ranked pairs whose median step is one minute",
     int((_steps.median() == 1).sum()) * 10 + len(_steps.columns), 47,
     f"one minute for {_WORDS_LOW(int((_steps.median() == 1).sum()))} of the "
     f"{_WORDS_LOW(len(_steps.columns))} ranked pairs"),
    ("the span of the mean step", round(_steps.mean().min(), 1), 2.0,
     f"the mean runs from {_steps.mean().min():.1f} to "
     f"{_steps.mean().max():.1f} minutes"),
    ("a coarser bar is a longer step",
     round(float(_grid_tslax.loc["5min"].speed_dex), 2), 0.67,
     f"from {float(_grid_tslax.loc['1min'].speed_dex):.2f} to "
     f"{float(_grid_tslax.loc['5min'].speed_dex):.2f}"),
    # Whether sparseness predicts the reading, asked of the data rather than of
    # a simulation. Three readings of sparseness, one weight, no relation in
    # any of them. The rank correlations are recomputed here; the permutation
    # p-values stay in spacing.py, because twenty thousand draws three times
    # over would double the time this file takes for a number that cannot move
    # without one of these moving first.
    ("spacing against the weight",
     round(spearman(_spacing.mean_step_min, _spacing.w_cex), 2), -0.01,
     f"between the exchange weight and the mean minutes between rows is "
     f"{spearman(_spacing.mean_step_min, _spacing.w_cex):+.2f}"),
    ("paired minutes against the weight",
     round(spearman(_spacing.paired_minutes, _spacing.w_cex), 2), 0.02,
     f"the count of paired minutes {spearman(_spacing.paired_minutes, _spacing.w_cex):+.2f}"),
    ("fill rate against the weight",
     round(spearman(_spacing.fill_rate, _spacing.w_cex), 2), 0.01,
     f"the fill rate {spearman(_spacing.fill_rate, _spacing.w_cex):+.2f}"),
    # Two checks rather than one. Packing four counts into a single integer is
    # the house pattern stretched past the point where a reader can see what
    # the expected value means, and the first attempt at it was arithmetic I
    # got wrong.
    ("the tally on the tighter-spaced side",
     int((_spacing_tight.w_cex > 0.5).sum()) * 100 + len(_spacing_tight), 1112,
     f"{int((_spacing_tight.w_cex > 0.5).sum())} of {len(_spacing_tight)} on "
     f"the tighter-spaced side"),
    ("the tally on the wider-spaced side",
     int((_spacing_wide.w_cex > 0.5).sum()) * 100 + len(_spacing_wide), 1011,
     f"against {int((_spacing_wide.w_cex > 0.5).sum())} of {len(_spacing_wide)} "
     f"on the wider"),
    ("what a sample this size can resolve",
     round(1.96 / (len(_spacing) - 1) ** 0.5, 2), 0.43,
     "resolves a rank correlation of about 0.42"),
    ("the saturation argument the data declined",
     round(spearman(_spacing.mean_step_min,
                    (_spacing.w_cex - 0.5).abs()), 2), 0.13,
     f"distance from an even split is "
     f"{spearman(_spacing.mean_step_min, (_spacing.w_cex - 0.5).abs()):+.2f}"),
    ("four wrong-way", int((allr.speed_cex > 0).sum()), 4,
     f"{'Four' if (allr.speed_cex > 0).sum() == 4 else 'ERR'} of the exchange coefficients come out positive"),
    ("AMZNX speed", round(byrow.loc["AMZNX"].speed_cex, 2), -0.35,
     f"corrects meaningfully, at {abs(byrow.loc['AMZNX'].speed_cex):.2f}"),
    ("AMZNX weight", round(byrow.loc["AMZNX"].w_cex, 2), 0.63,
     f"lowest exchange weight at {byrow.loc['AMZNX'].w_cex:.2f}"),
    ("AMZNX minutes vs TSLAX", int(byrow.loc["AMZNX"].minutes), 82,
     f"{int(byrow.loc['AMZNX'].minutes)} paired minutes against\n"
     f"{int(byrow.loc['TSLAX'].minutes)} for TSLAX"),
    ("closed-session rankable", len(closed), 8, f"across the {'eight' if len(closed) == 8 else 'ERR'} pairs measurable"),
    ("closed-session weight span", round(closed.w_cex.min(), 2), 0.96,
     f"at weights of {closed.w_cex.min():.2f} to {closed.w_cex.max():.2f}"),
    ("six dead tokens", int((d.paired_min < 10).sum()), 6,
     f"sit {'six' if (d.paired_min < 10).sum() == 6 else 'ERR'} tokens whose pools are too close"),
    ("bybit weight", round(bybit.weight_a, 2), 0.75, f"at a weight of {bybit.weight_a:.2f}"),
    ("bybit minutes", int(bybit.minutes), 498, f"over {int(bybit.minutes)} paired minutes"),
    ("bybit speeds", round(bybit.speed_a, 2), -0.09,
     f"at {abs(bybit.speed_a):.2f} of the gap per observation while the pool "
     f"closes {bybit.speed_b:.2f}"),
    ("pool-pair weights", round(pools.weight_a.max(), 2), 0.43,
     f"Two of the three weights, {pools.weight_a.nsmallest(2).max():.2f} and "
     f"{pools.weight_a.max():.2f}"),
    ("pool-pair lowest", round(pools.weight_a.min(), 2), 0.06,
     f"NVDAX at\n{pools.weight_a.min():.2f}"),
    ("pool-pair speeds", round(pools.speed_a.abs().min(), 2), 0.58,
     f"the deeper one by {pools.speed_a.abs().min():.2f} to {pools.speed_a.abs().max():.2f} of the gap"),
    ("groups cover all", len(g), 24, "The twenty-four tokens sort into three groups"),
    ("ranked group row", len(ranked), 9,
     f"| rankable | {len(ranked)} | {ranked.paired_min.median():.0f} | {ranked.ratio.median():.1f} |"),
    ("thin group row", len(thin), 9,
     f"| thin | {len(thin)} | {thin.paired_min.median():.0f} | {thin.ratio.median():.1f} |"),
    ("dead group row", len(dead), 6,
     f"| no on-chain market | {len(dead)} | {dead.paired_min.median():.0f} | "
     f"{dead.ratio.median():,.0f} |"),
    ("thin minutes span", int(thin.paired_min.max()), 73,
     f"printed in {'eleven' if thin.paired_min.min() == 11 else 'ERR'} to\n"
     f"seventy-three minutes"),
    ("spearman", round(rho, 2), -0.93, f"is **{rho:.2f}**"),
    ("spearman trimmed", round(spearman(trimmed.paired_min.reset_index(drop=True),
                                        trimmed.ratio.reset_index(drop=True)), 2), -0.92,
     f"holds at {spearman(trimmed.paired_min.reset_index(drop=True), trimmed.ratio.reset_index(drop=True)):.2f}"),
    ("liquidity rank", round(spearman(g.dex_liquidity, g.paired_min), 2), 0.92,
     f"with traded minutes at {spearman(g.dex_liquidity, g.paired_min):.2f}"),
    ("gap median", round(allr.mean_gap_pct.median(), 2), 0.10,
     f"median of {allr.mean_gap_pct.median():.2f} percent"),
    ("gap max", round(allr.mean_gap_pct.max(), 2), 0.14,
     f"at most {allr.mean_gap_pct.max():.2f}\n  percent"),
    # The two wrong-sign coefficients the post dismisses as noise, named.
    ("wrong-sign span", round(real_wrong.max(), 2), 0.08,
     f"All four are small, from {noise.min():.3f} to {real_wrong.max():.2f}"),
    ("wrong-sign largest two", round(real_wrong.min(), 2), 0.04,
     f"GLDX at {real_wrong.min():.2f} and GOOGLX at {real_wrong.max():.2f}"),
    ("GOOGLX band includes zero",
     int(ranked_pairs.set_index("symbol").loc["GOOGLX"].speed_cex_low <= 0
         <= ranked_pairs.set_index("symbol").loc["GOOGLX"].speed_cex_high), 1,
     "the band includes zero"),
    # Calibration, recomputed from the committed grid.
    ("calibration runs", len(cal), 96, "ninety-six runs over eight speed pairs"),
    ("calibration bias", round(lead.error.mean(), 2), 0.03,
     f"lands {lead.error.mean():.2f} above the truth on average"),
    ("calibration scatter low", round(lead.error.min(), 2), -0.33,
     f"from {abs(lead.error.min()):.2f} below the truth"),
    ("calibration scatter high", round(lead.error.max(), 2), 0.28,
     f"to {lead.error.max():.2f} above it"),
    ("ranking recovery clear", round(rank_clear, 2), 0.98,
     f"Across the {len(far)} runs where the true weight is plainly one-sided "
     f"the estimator picks the right leader {rank_clear * 100:.0f} percent"),
    # A percentage off twelve runs at one grid point is precision the grid does
    # not have, and the post used to quote it as a rate. It gives the count now,
    # and says that the genuinely even runs are excluded, which they always were
    # and which nothing had disclosed.
    ("ranking recovery near an even split",
     int(round(rank_near * len(near))) * 100 + len(near), 1112,
     f"right in {int(round(rank_near * len(near)))} of {len(near)} runs"),
    # The share of the window with the US equity market shut.
    ("closed share of window", round(closed_share, 2), 0.86,
     f"shut, which is {closed_share * 100:.0f} percent of the window"),
    # Figure captions and alt text restate computed numbers. Nothing checked
    # them until a mutation sweep changed the caption correlation from -0.93 to
    # -0.94 and verify.py stayed green.
    ("caption correlation", round(rho, 2), -0.93,
     f"Rank correlation {rho:.2f} across all twenty-four."),
    # The alt text used to read "all at or above 0.63", and this check agreed
    # with it, because it compared the number and not the claim: the stored
    # minimum is 0.629, which prints as 0.63 and is not at or above it. A
    # rounded figure can be quoted, but not as a bound. It now names the
    # lowest weight the way the table beside it prints the same token.
    ("alt text lowest weight", round(allr.w_cex.min(), 2), 0.63,
     f"nine tokens, the lowest at {allr.w_cex.min():.2f}."),
    ("alt text bybit weight", round(bybit.weight_a, 2), 0.75,
     f"pool bar sits at {bybit.weight_a:.2f}"),
    # The permutation test behind the headline correlation.
    ("permutation draws and p", int(rel.p_value < 0.0001), 1,
     f"p below {0.0001:g} on twenty thousand draws"),
    # The worked example of the Hasbrouck transformation in the prose. It is
    # arithmetic rather than data, and arithmetic in prose is still a claim.
    ("hasbrouck worked example",
     round(0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2), 2), 0.94,
     f"a weight of {0.8:.2f} corresponds to a share near "
     f"{0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2):.2f}."),
    # Cointegration, tested rather than assumed.
    ("spread stationary count", int(ranked_pairs.spread_stationary.sum()), 7,
     f"**{int(ranked_pairs.spread_stationary.sum())} of {len(ranked_pairs)}** rankable pairs"),
    ("spread half-life span",
     round(ranked_pairs.spread_half_life_obs.max(), 1), 3.9,
     f"half-lives of {ranked_pairs.spread_half_life_obs.min():.1f} to "
     f"{ranked_pairs.spread_half_life_obs.max():.1f} observations"),
    # And the same span read on a clock, each pair scaled by its own mean
    # spacing. The post gave only the first reading and called it minutes.
    ("the half-life span in clock minutes",
     round((ranked_pairs.set_index("symbol").spread_half_life_obs
            * _steps.mean()).max(), 1), 25.0,
     f"between {(ranked_pairs.set_index('symbol').spread_half_life_obs * _steps.mean()).min():.1f} and "
     f"{(ranked_pairs.set_index('symbol').spread_half_life_obs * _steps.mean()).max():.1f}\nminutes"),
    # The collection registry. Four passes, and the sentence that tells them
    # apart quotes all four of TSLAX's minute counts.
    ("TSLAX across the five passes", int(tslax_counts[-1]), 433,
     "TSLAX shows " + ", ".join(str(n) for n in tslax_counts[:-1])
     + f" and {tslax_counts[-1]} paired minutes"),
    # The cointegrating vector: fitted rather than imposed.
    ("GOOGLX imposed weight",
     round(float(vecrow.loc["GOOGLX"].w_imposed), 2), 1.2,
     f"imposed weight of {float(vecrow.loc['GOOGLX'].w_imposed):.2f}"),
    ("fitted beta span", round(vec.beta.min(), 2), 0.85,
     f"between\n{vec.beta.min():.2f} and {vec.beta.max():.2f}, below one in every pair"),
    ("one inside the bracket", int(vec.one_bracketed.sum()), 7,
     f"and it does in **{int(vec.one_bracketed.sum())} of {len(vec)}** pairs"),
    ("same leader either vector", int(vec.same_leader.sum()), 7,
     f"names the same leader in **{int(vec.same_leader.sum())} of {len(vec)}**"),
    ("largest vector weight move",
     round((vec.w_fitted - vec.w_imposed).abs().max(), 2), 0.2,
     f"largest weight by {(vec.w_fitted - vec.w_imposed).abs().max():.2f}"),
    ("GOOGLX imposed vs fitted",
     round(float(vecrow.loc["GOOGLX"].w_fitted), 2), 1.0,
     f"brings it to {float(vecrow.loc['GOOGLX'].w_fitted):.2f}, a more plausible"),
    # The second estimator.
    ("estimators agree", int(ranked_pairs.agree.sum()), 7,
     f"agrees in **{int(ranked_pairs.agree.sum())} of {len(ranked_pairs)}** pairs"),
    ("innovation correlation",
     round(ranked_pairs.innovation_correlation.median(), 2), 0.39,
     f"correlation is a median {ranked_pairs.innovation_correlation.median():.2f} rather"),
    ("bootstrap lead span", round(ranked_pairs.lead_share.min(), 2), 0.99,
     f"leads in\n{ranked_pairs.lead_share.min() * 100:.0f} to "
     f"{ranked_pairs.lead_share.max() * 100:.0f} percent of resamples"),
    # The staleness bound, read at the ranked pairs' own fill rates.
    ("hold scheme errs at every partial fill",
     round(hold_false[hold_false.index < 1.0].min(), 2), 0.95,
     f"the exchange the leader in **{hold_false[hold_false.index < 1.0].min() * 100:.0f} to "
     f"{hold_false[hold_false.index < 1.0].max() * 100:.0f} percent** of runs"),
    ("hold scheme is right at complete fill", round(hold_false.loc[1.0], 2), 0.0,
     "At complete fill the estimator is right"),
    ("drop scheme bound", round(ranked_risk.false_lead_drop.max(), 2), 0.19,
     f"holds the error to **{ranked_risk.false_lead_drop.min() * 100:.0f} to "
     f"{ranked_risk.false_lead_drop.max() * 100:.0f} percent** on a long base"),
    ("thinnest tokens bound", round(stale_risk.false_lead_drop.max(), 2), 0.38,
     f"errs up to {stale_risk.false_lead_drop.max() * 100:.0f} percent of the time"),
    ("TSLAX risk",
     round(float(ranked_risk.set_index("symbol").loc["TSLAX"].false_lead_drop), 2),
     0.02,
     "TSLAX at half its minutes filled sits at "
     f"{float(ranked_risk.set_index('symbol').loc['TSLAX'].false_lead_drop) * 100:.0f} percent"),
    # Specification sweeps.
    ("lag flips", lag_flips, 0,
     f"changes the leader in **{lag_flips} of {lag_sweep.symbol.nunique()}**"),
    ("grid agreement", grid_agree, 7,
     f"leaves the same leader in **{grid_agree} of {grid_fitted.symbol.nunique()}**"),
    # The lede's joint claim, in both places it is made.
    ("pair-days in the lede", led_days * 100 + pair_days, 2123,
     f"follows in {led_days} of the {pair_days} pair-days that can be ranked"),
    ("pair-days in the description", led_days * 100 + pair_days, 2123,
     f"The exchange leads in {led_days} of {pair_days} rankable pair-days"),
    ("pair-days in the limits section", led_days * 100 + pair_days, 2123,
     f"It rests on {led_days} of {pair_days} pair-days pointing the same way"),
    ("universe volume floor", int(MIN_CEX_VOLUME), 20000,
     f"at least {'twenty thousand' if MIN_CEX_VOLUME == 20000 else 'ERR'} "
     "dollars of 24-hour volume"),
    ("floor is below every kept token",
     int((u.cex_volume_24h >= MIN_CEX_VOLUME).all()), 1,
     "printed at least twenty"),
    ("collision screen pools", len(collisions), 13,
     f"found {len(collisions)} Solana pools answering to "
     f"{collisions.symbol.nunique()} of these tickers"),
    ("collision liquidity negligible",
     int(collisions.claimed_liquidity_usd.max() < 1), 1,
     "Their claimed liquidity was negligible that day"),
    ("ACNX seven minutes",
     int(g.set_index("symbol").loc["ACNX"].paired_min), 7,
     f"whose pool overlapped the exchange tape for "
     f"{'seven' if int(g.set_index('symbol').loc['ACNX'].paired_min) == 7 else 'ERR'} minutes"),
    # Every mint in the universe carries the issuer's vanity prefix; the post
    # says the screen enforced it, so the data has to show it.
    ("mint prefix on every token",
     int(u.mint.str.startswith("Xs").sum()), 24,
     "the vanity prefix Backed uses for its issued mints"),
    ("issuer list confirms every mint", int(registry.confirmed.sum()), 24,
     f"All {int(registry.confirmed.sum())} match the Solana address Backed publishes"),
    ("second opinion agrees", int(registry.in_jupiter_verified.sum()), 24,
     f"the same {int(registry.in_jupiter_verified.sum())} also appear in"),
    ("shut-hours pairs from series", len(shut_pairs), 19,
     f"{len(shut_pairs)} pair-days carry at least {MIN_PAIRED} shut-hours minutes"),
    ("shut-hours exchange leads",
     int((shut_pairs.w_shut > 0.5).sum()), 17,
     f"the exchange leads {int((shut_pairs.w_shut > 0.5).sum())} of them on the shut hours"),
    ("ranking floor in scope", MIN_PAIRED, 120,
     f"pairs with at least {MIN_PAIRED} paired minutes"),
    ("numerator-only control", round(spearman(g.paired_min, g.cex_volume_24h), 2),
     0.64, f"rank positively with pool activity, at "
     f"{spearman(g.paired_min, g.cex_volume_24h):.2f}"),
    ("panel gate names its thin rows",
     int((allr.minutes < MIN_PAIRED).sum()), 2,
     f"GOOGLX at {int(byrow.loc['GOOGLX'].minutes)} and AMZNX at "
     f"{int(byrow.loc['AMZNX'].minutes)}"),
    # The comparison paragraph restates both tallies in its own words. The
    # mutation sweep found them unguarded there: the bold sentence below was
    # checked and this restatement of the same numbers was not, which is the
    # same gap the lede's 21-of-23 had.
    ("whole-window leads beside the shut-hours count",
     int((shut_pairs.w_all > 0.5).sum()), 17,
     f"on the shut hours against {int((shut_pairs.w_all > 0.5).sum())} on the "
     f"whole window"),
    ("the two regime crossings", len(shut_flip), 2,
     f"That equality is {'two' if len(shut_flip) == 2 else 'ERR'} offsetting "
     f"flips"),
    ("METAX across regimes",
     int(round(flip_by.loc["METAX"].w_all * 100)) * 100
     + int(round(flip_by.loc["METAX"].w_shut * 100)), 5741,
     f"METAX falls from {flip_by.loc['METAX'].w_all:.2f} to "
     f"{flip_by.loc['METAX'].w_shut:.2f}"),
    ("TSLAX across regimes",
     int(round(flip_by.loc["TSLAX"].w_all * 100)) * 100
     + int(round(flip_by.loc["TSLAX"].w_shut * 100)), 4751,
     f"TSLAX rises from {flip_by.loc['TSLAX'].w_all:.2f} to "
     f"{flip_by.loc['TSLAX'].w_shut:.2f}"),
    ("AMZNX is a pool lead in both regimes",
     amznx_pool_both * 10 + len(amznx_shut), 11,
     "AMZNX stays a pool lead in both"),
    ("both crossings sit inside the strict band",
     flip_in_band * 10 + len(flip_weights), 44,
     "the strict rule declines to call either of them in either regime"),
    ("the strict band as the prose states it",
     int(STRICT_LOW * 100) * 100 + int(STRICT_HIGH * 100), 3070,
     f"only classifies weights outside {STRICT_LOW} to {STRICT_HIGH}"),
    ("the paired-minute floor, where the text names it again",
     MIN_PAIRED, 120, f"the stricter {MIN_PAIRED}-minute floor"),
    ("the window the post claims to cover",
     int(FIRST_DAY[-2:]) * 100 + int(THIRD[-2:]), 2931,
     f"collected daily from {int(FIRST_DAY[-2:])} to {int(THIRD[-2:])} July "
     f"{THIRD[:4]}"),
    ("the frontmatter dates itself to the last pass",
     int(THIRD.replace("-", "")), 20260731, f"date: {THIRD}"),
    ("first pass window, read off the raw epochs",
     WINDOWS[0][0], 1785281700, f"the three run from {WINDOWS[0][2]}"),
    ("second pass window, read off the raw epochs",
     WINDOWS[1][0], 1785339540, f"from {WINDOWS[1][2]}"),
    ("third pass window, read off the raw epochs",
     WINDOWS[2][0], 1785434520, f"and from {WINDOWS[2][2]}, all UTC"),
    ("token pairs with enough joint minutes",
     int(dep_first.loc["spread"]["usable_pairs"]) * 100
     + int(dep_first.loc["spread"]["token_pairs"]), 1021,
     f"Measured on the {_WORDS_LOW(dep_first.loc['spread']['usable_pairs'])} "
     f"token pairs of this pass"),
    ("the pairings left out for thin overlap",
     int(dep_first.loc["spread"]["pairs_below_floor"]) * 100
     + int(dep_first.loc["spread"]["token_pairs"]), 1121,
     f"{_WORDS_LOW(dep_first.loc['spread']['pairs_below_floor'])} of the "
     f"{_WORDS_LOW(dep_first.loc['spread']['token_pairs'])} pairings do "
     f"not clear the floor"),
    ("the exchange legs share a market factor",
     float(dep_first.loc["exchange"]["median"]), 0.506,
     f"exchange legs move together at a median "
     f"{float(dep_first.loc['exchange']['median']):.2f}"),
    ("the pool legs share less of one",
     float(dep_first.loc["pool"]["median"]), 0.145,
     f"the pool legs at {float(dep_first.loc['pool']['median']):.2f}"),
    ("the spread the model fits is near-idiosyncratic",
     float(dep_first.loc["spread"]["median"]), 0.080,
     f"the model actually uses at **{float(dep_first.loc['spread']['median']):.2f}**"),
    ("the discount rate the sample is cut by",
     round(float(dep_first.loc["spread"]["mean"]), 3), 0.12,
     f"mean spread correlation of {float(dep_first.loc['spread']['mean']):.2f}"),
    ("the discounted tally, and its p-value",
     round(float(sign_test(round(n_effective), round(n_effective))), 4), 0.125,
     f"worth about {_WORDS_LOW(round(n_effective))}, and "
     f"{_WORDS_LOW(round(n_effective))} of {_WORDS_LOW(round(n_effective))} one "
     f"way is {sign_test(round(n_effective), round(n_effective)):.3f} under the "
     f"same coin-flip null"),
    ("pairs fittable below the floor", len(thr_below), 16,
     f"The {len(thr_below)} pairs it can fit there lean the same way"),
    ("which way they lean, and how far",
     int((thr_below.w_cex > 0.5).sum()) * 100
     + int(round(float(thr_below.w_cex.median()) * 100)), 1293,
     f"{int((thr_below.w_cex > 0.5).sum())} of them to the exchange at a "
     f"median {float(thr_below.w_cex.median()):.2f}"),
    ("against the kept pairs on the same footing",
     int((thr_kept.w_cex > 0.5).sum()) * 100 + len(thr_kept), 2123,
     f"against {int((thr_kept.w_cex > 0.5).sum())} of {len(thr_kept)} at 0.90 "
     f"above it"),
    ("the span of minutes below the floor",
     int(thr_below.minutes.min()) * 1000 + int(thr_below.minutes.max()), 43111,
     f"at {int(thr_below.minutes.min())} to {int(thr_below.minutes.max())} "
     f"paired minutes the estimator scatters"),
    ("readings outside the range a weight can take", thr_outside, 6,
     f"{thr_outside} of the {len(thr_below)} print outside the range"),
    ("pairs the estimator refuses outright", thr_refused, 26,
     f"A further {thr_refused} pairs the estimator refuses outright"),
    ("pairs whose strongest correlation sits at a one-minute lag",
     int((align.best_lag == 1).sum()) * 100 + len(align), 1423,
     f"plus one rather than zero on **{int((align.best_lag == 1).sum())} of "
     f"{len(align)}** ranked pairs"),
    ("the realigned tally", int((align_fit.w_realigned > 0.5).sum()) * 100
     + int((align_fit.w_as_collected > 0.5).sum()), 2221,
     f"the exchange leads **{int((align_fit.w_realigned > 0.5).sum())} of "
     f"{len(align_fit)}** rather than "
     f"{int((align_fit.w_as_collected > 0.5).sum())}"),
    ("what the correction does to the median weight",
     float(align_fit.w_realigned.median()), 1.168,
     f"the median weight rises from "
     f"{float(align_fit.w_as_collected.median()):.2f} to "
     f"**{float(align_fit.w_realigned.median()):.2f}**"),
    ("the spread is the same size either way",
     float(align.spread_sd_bp_as_collected.median()) * 100
     + float(align.spread_sd_bp_realigned.median()), 2110.7,
     f"a median standard deviation of "
     f"{align.spread_sd_bp_as_collected.median():.1f} basis points as "
     f"collected against {align.spread_sd_bp_realigned.median():.1f} "
     f"realigned"),
    ("stationarity under both alignments",
     int(align.stationary_realigned.sum()) * 100
     + int(align.stationary_as_collected.sum()), 2123,
     f"stationary in {int(align.stationary_realigned.sum())} of {len(align)} "
     f"pairs after the correction against "
     f"{int(align.stationary_as_collected.sum())} of {len(align)}"),
    # The field orders the post quotes, taken from the tuples the collector
    # selects by, so a payload layout described in prose cannot drift from the
    # one the code reads.
    ("Gate's field order as the post states it",
     GATE_FIELDS.index("close") * 10 + GATE_FIELDS.index("open"), 25,
     "`[" + ", ".join(GATE_FIELDS) + "]`"),
    ("GeckoTerminal's field order as the post states it",
     GECKO_FIELDS.index("close"), 4,
     "`[" + ", ".join(GECKO_FIELDS) + "]`"),
    ("the field the collector wrongly read",
     GATE_FIELDS.index("open"), 5,
     f"the collector read field {_WORDS_LOW(GATE_FIELDS.index('open'))}, the open"),
    ("the field it should have read on the pool side",
     GECKO_FIELDS.index("close"), 4,
     f"the collector read field {_WORDS_LOW(GECKO_FIELDS.index('close'))}, the "
     f"close"),
    # The one pool lead, and what the correction does to it. Review pointed
    # out that "conservative" was being said of the aggregate and quietly
    # extended to every claim: a correction that moves all weights towards the
    # exchange must weaken the study's only reading in the other direction, and
    # it does, from a clear lead to an unclassified one.
    # The Summary and the AMZNX section state the pool lead as a finding, so
    # each has to carry what the correction does to it. Guarded separately
    # because a caveat in one place is not a caveat in the other.
    ("the Summary says which alignment its pool lead rests on",
     int(float(_amznx.w_realigned) >= STRICT_LOW), 1,
     "is a clear pool lead the one day it can be measured, on the alignment "
     "these tables use"),
    ("the AMZNX section gives the corrected reading",
     round(float(_amznx.w_realigned), 3), 0.332,
     f"realigned, AMZNX is {float(_amznx.w_realigned):.2f}, which the strict "
     f"rule declines to call for either side"),
    ("AMZNX realigned", round(float(_amznx.w_realigned), 3), 0.332,
     f"it is {float(_amznx.w_realigned):.2f} rather than "
     f"{float(_amznx.w_as_collected):.2f}"),
    ("AMZNX as collected", round(float(_amznx.w_as_collected), 3), -0.238,
     f"single clear pool lead at {float(_amznx.w_as_collected):.2f}"),
    ("the corrected AMZNX reading is no longer a clear lead",
     int(float(_amznx.w_realigned) >= STRICT_LOW), 1,
     "no longer a clear lead for either side"),
    # Both places the article leans on the correction's direction, and the two
    # facts that make leaning on it fair.
    ("the correction's direction, in the Summary",
     _align_towards * 100 + len(align_fit), 2123,
     f"moves {_align_towards} of {len(align_fit)} weights the same way"),
    ("the correction's direction, where the exception is named",
     _align_towards * 100 + len(align_fit), 2123,
     f"moves {_align_towards} of {len(align_fit)} weights towards the exchange"),
    ("the size of the two pairs that move the other way",
     round(_align_against_max, 2), 0.01,
     f"move the other way by {_align_against_max:.2f} and less"),
    ("the correction costs a lead without buying one",
     _align_leads_lost, 0, "no pair loses a lead it had"),
    ("loose tally, restated", led_days * 100 + pair_days, 2123,
     f"{led_days} of {pair_days} under the loose rule"),
    ("strict tally, restated",
     strict_ex * 100 + strict_pool * 10 + strict_near, 1715,
     f"becomes {strict_ex} classified one way, {strict_pool} the other, and "
     f"{strict_near} that the strict rule"),
    ("strict tally", strict_ex * 100 + strict_pool * 10 + strict_near, 1715,
     f"**{strict_ex} pair-days are clear exchange leads, {strict_pool} is a "
     f"clear pool lead, and {strict_near} are unclassified**"),
    ("matched-length staleness",
     round(float((matched_1000_12.w_cex > 0.5).mean()), 2), 0.42,
     f"error to about {float((matched_1000_50.w_cex > 0.5).mean()) * 100:.0f} "
     f"percent at half fill and "
     f"{float((matched_1000_12.w_cex > 0.5).mean()) * 100:.0f} percent at an eighth"),
    # The daily replication, three days in.
    ("registry row, second day", len(day2_coverage), 25,
     f"| next day | 30 July, two sessions | {len(day2_coverage)} |"),
    ("registry row, third day", len(day3_coverage), 24,
     f"| third day | 31 July, two sessions | {len(day3_coverage)} |"),
    ("second-day correlation", round(day2.rho, 2), -0.93,
     f"prints {day2.rho:.2f} on {int(day2.tokens)} tokens on the second day"),
    ("third-day correlation", round(day3.rho, 2), -0.93,
     f"**{day3.rho:.2f}** on {int(day3.tokens)} on the third"),
    ("both later days significant",
     int(day2.p_value < 0.0001 and day3.p_value < 0.0001), 1,
     "each with a permutation p below 0.0001"),
    ("third-day tail check", round(day3.rho_trimmed, 2), -0.92,
     f"leaves the third day at {day3.rho_trimmed:.2f} on "
     f"{int(day3.trimmed_tokens)} tokens"),
    ("third-day liquidity rank", round(day3.rho_liquidity, 2), 0.9,
     f"ranks with pool activity at {day3.rho_liquidity:.2f}"),
    ("multi-window leaders", int(both_windows.led_every_window.sum()), 7,
     f"{'Seven' if both_windows.led_every_window.sum() == 7 else 'ERR'} of the "
     f"{'eight' if len(both_windows) == 8 else 'ERR'} tokens rankable in more "
     "than one window"),
    ("second-day rankable", len(day2_ranked), 9,
     f"ranks nine and the exchange leads all nine, at a sign-test p of "
     f"{sign_test(int((day2_ranked.w_cex > 0.5).sum()), len(day2_ranked)):.4f}"),
    ("third-day split", int((day3_ranked.w_cex > 0.5).sum()), 5,
     f"{'five of seven' if (day3_ranked.w_cex > 0.5).sum() == 5 and len(day3_ranked) == 7 else 'ERR'}"),
    ("TSLAX third day", round(float(day3_ranked.loc["TSLAX"].w_cex), 2), 0.47,
     f"TSLAX prints {float(day3_ranked.loc['TSLAX'].w_cex):.2f} on the third "
     "day after 0.89 and 0.92"),
    ("TSLAX third-day exchange speed",
     round(abs(float(day3_ranked.loc["TSLAX"].speed_cex)), 2), 0.21,
     f"correcting meaningfully, at "
     f"{abs(float(day3_ranked.loc['TSLAX'].speed_cex)):.2f} of the gap per observation"),
    ("AMZNX pool lead", round(float(day3_ranked.loc["AMZNX"].w_cex), 2), -0.24,
     f"prints a weight of {float(day3_ranked.loc['AMZNX'].w_cex):.2f} with the "
     "pool ahead in"),
    ("AMZNX bootstrap",
     round(100 - float(day3_ranked.loc["AMZNX"].lead_share) * 100), 98,
     f"pool ahead in {100 - float(day3_ranked.loc['AMZNX'].lead_share) * 100:.0f} "
     "percent of bootstrap resamples"),
    ("GLDX across days",
     round(float(day3_ranked.loc["GLDX"].w_cex), 2), 0.67,
     f"Its {float(day2_ranked.set_index('symbol').loc['GLDX'].w_cex):.2f} and "
     f"{float(day3_ranked.loc['GLDX'].w_cex):.2f} count as exchange leads"),
    ("METAX second day",
     round(float(day2_ranked.set_index("symbol").loc["METAX"].w_cex), 2), 0.57,
     f"METAX printed "
     f"{float(day2_ranked.set_index('symbol').loc['METAX'].w_cex):.2f} on the "
     "second day, the one pair where the estimators disagreed"),
    ("METAX went silent",
     int(day2_coverage.set_index("symbol").loc["METAX"].paired_minutes), 142,
     f"after {int(day2_coverage.set_index('symbol').loc['METAX'].paired_minutes)} "
     "paired minutes the day before"),
    ("unpaired counts by day",
     (len(day2_universe) - len(day2_coverage)) * 10
     + (len(day3_universe) - len(day3_coverage)), 23,
     f"numbered {'two' if len(day2_universe) - len(day2_coverage) == 2 else 'ERR'} "
     f"on the second day and "
     f"{'three' if len(day3_universe) - len(day3_coverage) == 3 else 'ERR'} on the third"),
    ("one-minute pairings",
     int(day3_coverage.set_index("symbol").loc[["ABTX", "PMX"]].paired_minutes.max()),
     1, "ABTX and PMX, paired for the first time on the third day"),
    # Out-of-sample.
    ("replication count", int(rep.leads_both.sum()), 7,
     f"In this pass {'seven of seven' if rep.leads_both.sum() == 7 else 'ERR'} "
     "point the same way"),
    ("sign test p-value", round(float(sign_test(len(ranked_pairs), len(ranked_pairs))), 4), 0.0156,
     f"p = {sign_test(len(ranked_pairs), len(ranked_pairs)):.4f}"),
    ("replication drift", round((rep.w_second - rep.w_first).abs().max(), 2), 0.11,
     f"weights moving by at most {(rep.w_second - rep.w_first).abs().max():.2f}"),
]

def table_rows(header: tuple[str, ...]) -> list[list[str]]:
    """Pull one markdown table out of the post by its full header row.

    Matching on the first column alone is not enough: three of the four tables
    lead with "token", so a first-column match returned the same table for all
    three and two of them silently went unchecked.

    Tables are the largest hand-typed restatement of the data in the post, and
    nothing checked them until every cell was compared here. A mutation sweep
    over the post found 55 of 69 numbers unguarded, almost all of them table
    cells.
    """
    for block in post.split("\n\n"):
        lines = [ln for ln in block.strip().splitlines() if ln.startswith("|")]
        cells = tuple(c.strip() for c in lines[0].split("|")[1:-1]) if lines else ()
        if len(lines) > 2 and cells == header:
            return [[c.strip() for c in ln.split("|")[1:-1]] for ln in lines[2:]]
    return []


def compare_rows(name: str, tag: str, where: str, header: tuple[str, ...],
                 got: list[list[str]], expected: list[list[str]]) -> int:
    """Report every row that differs, in either direction.

    Walking `expected` alone leaves a document with more rows than the data
    failing silently: the check goes red and prints not one row, because every
    row it knows about matched. That is the least useful moment to say nothing,
    so the walk runs to the longer of the two.
    """
    if not got:
        print(f"  [{tag}] {name}: no table in {where} with header {header}")
        return 1
    if got == expected:
        return 0
    print(f"  [{tag}] {name}: table does not match the data")
    for i in range(max(len(got), len(expected))):
        have = got[i] if i < len(got) else None
        want = expected[i] if i < len(expected) else None
        if have != want:
            print(f"         row {i}: {where} {have} expected {want}")
    return 1


def check_table(name: str, header: tuple[str, ...],
                expected: list[list[str]]) -> int:
    """Compare every cell of a post table against the recomputed values."""
    return compare_rows(name, "POST", "the post", header,
                        table_rows(header), expected)


money = "${:,.0f}".format
uni = u.set_index("symbol")
universe_table = [
    [t, money(uni.loc[t].cex_volume_24h), money(uni.loc[t].dex_volume_24h),
     money(uni.loc[t].dex_liquidity),
     f"{uni.loc[t].ratio:,.0f}" if uni.loc[t].ratio >= 100 else f"{uni.loc[t].ratio:.2f}"]
    for t in ("VTIX", "ACNX", "NFLXX", "AZNX", "TQQQX", "KOX", "MSTRX",
              "TSLAX", "CRCLX", "NVDAX", "QQQX")
]
weights_table = [
    [t, f"{byrow.loc[t].w_cex:.2f}", f"{byrow.loc[t].speed_cex:+.2f}",
     f"{byrow.loc[t].speed_dex:.2f}"]
    for t in allr.sort_values("w_cex", ascending=False).symbol
]
groups_table = [
    [name, str(len(sub)), f"{sub.paired_min.median():.0f}",
     f"{sub.ratio.median():,.0f}" if sub.ratio.median() >= 100
     else f"{sub.ratio.median():.1f}"]
    for name, sub in (("rankable", ranked), ("thin", thin),
                      ("no on-chain market", dead))
]
gdead = dead.set_index("symbol").sort_values("paired_min")
dead_table = [
    [t, str(int(gdead.loc[t].paired_min)), money(gdead.loc[t].cex_volume_24h),
     money(gdead.loc[t].dex_volume_24h), money(gdead.loc[t].dex_liquidity)]
    for t in gdead.index
]
# The robustness table carries seven tokens across seven columns, all of it
# hand-typed from robustness_<label>.csv. A mutation sweep found every cell of it
# unguarded, which is the same hole the four tables above had.
robust_table = [
    [r.symbol, str(int(r.paired_minutes)), f"{r.fill_rate:.0%}",
     f"{r.w_cex:.2f}", f"{r.hasbrouck_low:.2f} to {r.hasbrouck_high:.2f}",
     f"{r.lead_share:.0%}", f"{r.spread_half_life_obs:.1f}"]
    for r in ranked_pairs.itertuples()
]

# The post directory carries its own copy of every dataset behind a figure or
# table, per the wiki's in-directory rule. A copy can drift; a byte comparison
# cannot lie about it.
from analysis.build_analysis import POST_DATA  # noqa: E402

mirror_bad = 0
for name in POST_DATA:
    canonical = (base / "data" / name)
    mirrored = (base / "post" / "data" / name)
    if not mirrored.exists():
        print(f"  [POST] post/data/{name} is missing")
        mirror_bad += 1
    elif mirrored.read_bytes() != canonical.read_bytes():
        print(f"  [POST] post/data/{name} has drifted from data/{name}")
        mirror_bad += 1

bad = mirror_bad
# Counted per surface rather than as one total. The single number this used to
# print sat beside "lines of post" and read as though the post were the only
# thing being checked, which stopped being true three surfaces ago.
tally: Counter[str] = Counter()
tally["post"] += len(POST_DATA)
tables = (
    ("universe table",
     ("token", "Gate 24h", "on-chain 24h", "on-chain liquidity",
      "Gate per on-chain dollar"), universe_table),
    ("weights table",
     ("token", "Gate weight", "Gate correction speed", "pool correction speed"),
     weights_table),
    ("groups table",
     ("group", "tokens", "median minutes the pool traded",
      "median exchange dollars per on-chain dollar"), groups_table),
    ("dead-token table",
     ("token", "minutes the pool traded", "exchange 24h volume",
      "on-chain 24h volume", "on-chain liquidity"), dead_table),
    ("robustness table",
     ("token", "paired minutes", "pool fill", "GG weight",
      "Hasbrouck bounds", "bootstrap lead", "half-life, obs"),
     robust_table),
    ("cross-window table",
     ("token", "29 July", "30 July", "31 July", "span"),
     [[sym,
       f"{r['2026-07-29b']:.2f}" if pd.notna(r['2026-07-29b']) else "-",
       f"{r['2026-07-30']:.2f}" if pd.notna(r['2026-07-30']) else "-",
       f"{r['2026-07-31']:.2f}" if pd.notna(r['2026-07-31']) else "-",
       f"{r.spread_across_windows:.2f}"]
      for sym, r in both_windows.iterrows()]),
)
for name, header, expected in tables:
    tally["post"] += sum(len(r) for r in expected)
    bad += check_table(name, header, expected)

# The daily correlation range the page quotes, from the same table the post
# uses for it.
_window_rho = pd.read_csv(base / "data" / "windows_relation.csv").rho
both_days_low = f"{_window_rho.min():.2f}"
both_days_high = f"{_window_rho.max():.2f}"

# The second shipped surface. Everything above reads post/index.md, and the
# single-page view was checked only for being regenerable, never for saying the
# same thing: the workflow diff catches a stale page, not a page built from the
# wrong column. Its headline figures are tied to the data here, the same way
# the post's are.
_collector = (base / "analysis" / "collect.py").read_text()
page = (base / "index.html").read_text()
flat_page = _flat(page)

PAGE = [
    ("the page's alignment row",
     f"exchange ahead in {int((align_fit.w_realigned > 0.5).sum())} of "
     f"{len(align_fit)}, against "
     f"{int((align_fit.w_as_collected > 0.5).sum())} as collected"),
    ("the page's dependence row",
     f"{float(dep_first.loc['spread']['median']):.2f}, against "
     f"{float(dep_first.loc['exchange']['median']):.2f} on the exchange legs"),
    ("the page's floor row",
     f"{int((thr_below.w_cex > 0.5).sum())} of {len(thr_below)} lean the same "
     f"way, median {float(thr_below.w_cex.median()):.2f}, {thr_refused} too "
     f"thin to fit"),
    ("the page's joint tally", f"{led_days}/{pair_days}"),
    # Anchored on the card it sits in, not on the bare value. The figure
    # appears twice on the page, so a bare search passed while one of the two
    # sites carried a wrong number, which is the gap the post's restated
    # tallies had.
    ("the page's rank correlation card",
     f'<b>{rho:.2f}</b><span>rank correlation between pool activity'),
    ("the page's daily correlation range",
     f"prints between {both_days_low} and {both_days_high} across"),
    ("the page's dead-pool count",
     f"<b>{len(dead)}</b><span>tokens whose pool traded"),
    ("the page's largest volume ratio", f"{u.ratio.max():,.0f}x"),
    ("the page's artefact range",
     f"error {ranked_risk.false_lead_drop.min() * 100:.0f}% to "
     f"{ranked_risk.false_lead_drop.max() * 100:.0f}%"),
    # Three figures the digit sweep found standing on the page after the tables
    # were covered. Each states what was done rather than what came out, which
    # is why no result check touched them, and each is wrong in a way a reader
    # cannot see: a page that says ten lags when the sweep ran eight describes a
    # robustness check nobody performed.
    ("the page's lag orders",
     "refitted at "
     + ", ".join(str(x) for x in sorted(lag_sweep.lags.unique())[:-1])
     + f" and {sorted(lag_sweep.lags.unique())[-1]} lags"),
    # What one step of the fit spans, on the surface that prints the speeds
    # without the article's paragraph beside them. A reader of the page alone
    # saw two coefficients and no unit at all.
    ("the page's account of the step a speed is measured over",
     f"a median of one minute on {int((_steps.median() == 1).sum())} of the "
     f"{len(_steps.columns)} ranked pairs"),
    ("the page's spacing row",
     f"rank correlation {spearman(_spacing.mean_step_min, _spacing.w_cex):+.2f} "
     f"over {len(_spacing)} pair-days"),
    ("the page's lag-order result",
     f"leader changes in {lag_flips} of {lag_sweep.symbol.nunique()}"),
    ("the page's floor, in the question it asks",
     f"Does the {MIN_PAIRED}-minute floor pick its own answer"),
    ("the page's collection dates",
     f"Collected daily, {int(FIRST_DAY[-2:])} "
     f"{pd.Timestamp(FIRST_DAY).strftime('%B')} {FIRST_DAY[:4]} to "
     f"{int(THIRD[-2:])} {pd.Timestamp(THIRD).strftime('%B')} {THIRD[:4]}"),
]

readme = (base / "README.md").read_text()
flat_readme = _flat(readme)

# Read off the headers rather than remembered. Only the column names are
# needed, so nothing is parsed beyond the first line of each file.
_panel_all = p[p.regime == "all"]
_panel_writes = set(re.findall(
    r'to_csv\(\s*DATA\s*/\s*"([^"]+)"',
    (base / "analysis" / "panel.py").read_text()))
_groups_reads = set(re.findall(
    r'read_csv\(\s*DATA\s*/\s*"([^"]+)"',
    (base / "analysis" / "relation.py").read_text()))

_CAPTURE_WORDS = ("captur", "fetched_at", "collected_at", "retrieved", "as_of")
_capture_columns = sorted(
    {c for _f in sorted((base / "data").glob("*.csv"))
     for c in pd.read_csv(_f, nrows=0).columns
     if any(w in c.lower() for w in _CAPTURE_WORDS)})

# The README's figures, tied to the same computed values the post's copies are
# tied to, so the two documents cannot drift apart or from the data.
README_CLAIMS = [
    ("the README's universe size", f"Across {len(u)} xStocks quoted at once"),
    ("the README's dead-pool count",
     f"{_WORDS_LOW(len(dead)).capitalize()} of the {len(u)} have pools too "
     f"close to dead"),
    ("the README's joint tally", f"in {led_days} of the {pair_days} pair-days"),
    ("the README's rank correlation", f"a rank correlation of {rho:.2f}"),
    ("the README's calibration bias",
     f"The fit sits {lead.error.mean():.2f} above the truth"),
    ("the README's calibration scatter",
     f"from {abs(lead.error.min()):.2f} below the truth to "
     f"{lead.error.max():.2f} above it"),
    ("the README's recovery away from an even split",
     f"the right leader in {rank_clear * 100:.0f} percent of the {len(far)} runs"),
    ("the README's recovery near an even split",
     f"in {int(round(rank_near * len(near)))} of the {len(near)} at the one "
     f"grid point"),
    ("the README's worked Hasbrouck example",
     f"a weight of {0.8:.2f} goes with a share near "
     f"{0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2):.2f}"),
    ("the README's hold-scheme bound",
     f"leader in {hold_false[hold_false.index < 1.0].min() * 100:.0f} to "
     f"{hold_false[hold_false.index < 1.0].max() * 100:.0f} percent of runs"),
    ("the README's drop-scheme bound",
     f"keeps the error to {ranked_risk.false_lead_drop.min() * 100:.0f} to "
     f"{ranked_risk.false_lead_drop.max() * 100:.0f} percent"),
    # The correction's cost, which the README carried without it. The post
    # names the exception in five places; the README said only that the
    # as-collected fit is the conservative side, which is the aggregate claim
    # review had already rejected as a stand-in for every part.
    ("the README's AMZNX reading, as collected",
     f"one clear pool lead at {float(_amznx.w_as_collected):.2f}"),
    ("the README's AMZNX reading, realigned",
     f"realigned it is {float(_amznx.w_realigned):.2f}"),
    ("the README's account of the correction's direction",
     f"moves {_align_towards} of {len(align_fit)} weights towards the exchange"),
    # How far each panel reaches. The sentence saying so was written with the
    # second number guessed off a merge printout and was wrong by two, which is
    # the reason a number in prose gets a check rather than a proofread.
    ("the README's first-pass coverage",
     f"the only one that measured all {d.symbol.nunique()}"),
    ("the README's session-panel coverage",
     f"a regime and so covers {_panel_all.symbol.nunique()}"),
]

# The README's directions, tied to a sign rather than to a value. A flip sweep
# over it swapped exchange for pool and leads for follows in each of its ten
# claim-bearing sentences and only one of the ten went red, the headline among
# the nine that did not: "the pool leads and the exchange follows" passed every
# gate, because the cross-document rule requires the tally and never asked who
# won it. A negation sweep did worse, nought of eight. The entries below cover
# the sentences whose inversion contradicts the data; the rest are prose where
# the inverted sentence is merely odd, and they are left alone rather than
# given a check that asserts a phrase exists, which tests the sentence against
# itself.
README_DIRECTIONS = [
    ("the README's headline direction", bool(led_days * 2 > pair_days),
     "the exchange leads and the pool follows"),
    # Carrying a stale price forward biases the estimator towards the exchange,
    # so the warning not to do it and the direction of the damage are one fact
    # said twice.
    ("the README warns against carrying a stale price forward",
     bool(hold_false[hold_false.index < 1.0].min() > 0.5),
     "Do not carry a pool's last price forward"),
    ("the README names the venue the stale-price artefact favours",
     bool(hold_false[hold_false.index < 1.0].min() > 0.5),
     "calls the exchange the leader in"),
    ("the README's account of which way the correction moves the weights",
     bool(_align_towards * 2 > len(align_fit)), "towards the exchange has"),
    # The sentence the whole correction turns on: true of the aggregate, false
    # of one part. It holds only while both halves hold, so both are read off
    # the data -- the weights move to the exchange, and a reading is lost all
    # the same.
    ("the README keeps the aggregate and the parts apart",
     bool(_align_towards * 2 > len(align_fit) and _pool_before == 1),
     "cannot be left to stand for each part"),
    # The reuse hazard the section exists for. Delete the "not" and the README
    # tells a reader the two decompositions are the same object.
    ("the README keeps the two decompositions apart",
     bool(round(0.8, 2) != round(0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2), 2)),
     "is not a Gonzalo-Granger weight"),
    # Why the post is dated by its commit. The claim is about what the CSVs do
    # not carry, so it is read off their headers: the day one of them gains a
    # capture column, the provenance note becomes false and this says so.
    ("the README's reason for dating the post by its commit",
     not _capture_columns, "carry no capture timestamp of their own"),
    # The rebuild order says the grouping does not read what run_panel writes.
    # That is a fact about two files and it is read off them, because the day
    # relation.py is pointed at the session panel the sentence becomes a lie
    # that no number in it would move.
    # Disjoint, not difference. The first version asked whether relation.py
    # reads anything panel.py does not write, which is true of universe.csv
    # whatever the panel file is, so repointing the grouping at the session
    # panel left it green. Two legs, and only the second one caught it.
    ("the README on which panel file the grouping reads",
     _panel_writes.isdisjoint(_groups_reads),
     "not the file `run_panel` writes"),
]

# The module docstrings, pulled from the same computed values the post's copies
# are pulled from.
def _all_docstrings(name: str) -> str:
    """Every docstring in one module, module-level and per function alike.

    Reading only the module docstring would have missed both of the arguments
    that carry a measurement: staleness's simulator grid and collect_raw's
    account of the day a collection lost its network.
    """
    tree = ast.parse((base / "analysis" / f"{name}.py").read_text())
    return " ".join(
        ast.get_docstring(node) or ""
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)))


_stale_grid = pd.read_csv(base / "data" / "staleness_matched.csv")
_stale_thin = _stale_grid[(_stale_grid.n == _stale_grid.n.max())
                          & (_stale_grid.keep == _stale_grid.keep.min())]
# Three modules cite the two papers by year and only the post pins them by
# DOI, which is the identifier nobody reads and the year is what they do. The
# year is taken out of the DOI the post carries, so the two cannot disagree.
_doi_year = {}
for _doi in re.findall(r"https://doi\.org/(\S+?)[)\s]", post):
    if (_hit := re.search(r"\.((?:19|20)\d{2})\.", _doi)):
        _doi_year[_doi.split("/")[0]] = _hit.group(1)
_gg_year = _doi_year["10.1080"]
_hasbrouck_year = _doi_year["10.1111"]
# cointegration.py names the vector it assumes; vector.py is where the number
# actually lives, as the beta handed to fit_with_vector. Read it off the call
# rather than trusting the sentence, so the two cannot part company.
_imposed_beta = next(
    kw.value.value
    for node in ast.walk(ast.parse((base / "analysis" / "vector.py").read_text()))
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "fit_with_vector"
    for kw in node.keywords
    if kw.arg == "beta" and isinstance(kw.value, ast.Constant))

# Recomputed here rather than read out of dependence.csv, which keeps summary
# statistics and not the pairwise overlaps the sentence is about.
_third_legs = {}
for _sym in pd.read_csv(base / "data" / f"robustness_{THIRD}.csv"
                        ).query("verdict == 'ranked'").symbol:
    _f = pd.read_csv(base / "raw" / THIRD / f"{_sym}.csv", index_col="ts")
    _f.index = pd.to_datetime(_f.index, unit="s", utc=True)
    _third_legs[_sym] = (len(_f), minute_changes(np.log(_f.cex) - np.log(_f.dex)))
_overlaps = sorted(
    (len(pd.concat([_third_legs[a][1], _third_legs[b][1]], axis=1,
                   join="inner").dropna()), a, b)
    for a, b in combinations(sorted(_third_legs), 2))
_widest = _overlaps[-1]
_second = _overlaps[-2]
# The sentence names the two bar counts largest first. Taking them in the order
# the pair happens to be stored gave the right answer here only because the two
# symbols sort the same way their bar counts do, which is a coincidence and not
# a rule.
_widest_bars = sorted((_third_legs[_widest[1]][0], _third_legs[_widest[2]][0]),
                      reverse=True)

_align_best = align[align.best_lag == 1]
_align_widest = align.assign(
    margin=align.corr_at_best - align.corr_at_zero).nlargest(1, "margin").iloc[0]

MODULE_DOCS = [
    ("discovery's calibration run count", "discovery",
     f"{_WORDS_LOW(len(cal))} runs over eight speed pairs"),
    ("discovery's bias", "discovery",
     f"the fit lands {lead.error.mean():.2f} above the truth"),
    ("discovery's scatter", "discovery",
     f"between {abs(lead.error.min()):.2f} below the truth and "
     f"{lead.error.max():.2f} above it"),
    ("discovery's recovery away from an even split", "discovery",
     f"the right leader in {rank_clear * 100:.0f} percent of the {len(far)} runs"),
    ("discovery's recovery near an even split", "discovery",
     f"in {int(round(rank_near * len(near)))} of the {len(near)} at the one "
     f"grid point"),
    # The module writes the weight as 0.8 and the post as 0.80, so the two
    # searches differ in their formatting and agree on their arithmetic.
    ("discovery's worked Hasbrouck example", "discovery",
     f"weight of {0.8:g} corresponds to a Hasbrouck share near "
     f"{0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2):.2f}"),
    ("alignment's lag evidence", "alignment",
     f"plus one rather than zero on {len(_align_best)} of the {len(align)}"),
    ("alignment's widest margin", "alignment",
     f"as wide as {_align_widest.corr_at_best:.2f} against "
     f"{_align_widest.corr_at_zero:.2f}"),
    ("dependence's bar counts and their overlap", "dependence",
     f"{_widest_bars[0]} and {_widest_bars[1]} bars "
     f"share only {_widest[0]} usable minutes"),
    ("dependence's p-value under the coin-flip null", "dependence",
     f"carries p = {sign_test(n_ranked, n_ranked):.4f}"),
    # The sample the p-value is computed on, named in the module that computes
    # it. It said nine, which is the session panel's count, next to a p-value
    # that is the series pass's.
    ("bootstrap names the sample the sign test is run on", "bootstrap",
     f"{_WORDS_LOW(n_ranked).capitalize()} pairs all pointing the same way"),
    ("windows' account of the headline correlation", "windows",
     f"A correlation of {rho:.2f} from a single draw of "
     f"{_WORDS_LOW(len(u))} tokens"),
    # The matched sweep's grid, described in prose in one place and written as
    # a tuple in another. Both ends of it are quoted, so both are read off the
    # committed runs.
    ("staleness's base series length", "staleness",
     f"simulates a {_stale_grid.n.max():,}-minute base series"),
    ("staleness's thinnest fill", "staleness",
     f"a {_stale_grid.keep.min() * 100:.0f} percent fill"),
    ("staleness's shortest case", "staleness",
     f"{_stale_grid.n.min()} stresses the floor"),
    # The one approximation in the paragraph, rounded from the runs it
    # describes rather than from the arithmetic of the grid, since it is the
    # rows that survived the fit and not the rows the sampler drew.
    ("staleness's fitted rows at the thinnest fill", "staleness",
     f"keeps near {round(_stale_thin.rows.median(), -2):.0f} fitted rows"),
    # Both papers are cited by year in three modules and pinned by DOI only in
    # the post. A year is the part a reader checks and the part a search
    # engine uses.
    ("discovery cites Gonzalo-Granger by the year the DOI resolves to",
     "discovery", f"Gonzalo-Granger ({_gg_year}) decomposition"),
    ("discovery cites Hasbrouck by the year the DOI resolves to",
     "discovery", f"Hasbrouck ({_hasbrouck_year}) splits the variance"),
    # A constant the module imports and then restates as a literal in its own
    # first line, which is the arrangement that guarantees a drift.
    ("threshold's floor", "threshold",
     f"Does the {MIN_PAIRED}-minute floor"),
    ("cointegration's imposed vector", "cointegration",
     f"the cointegrating vector is (1, {-_imposed_beta:g})"),
    # What the second day actually holds. The paragraph beside it recounts the
    # attempt that failed, and the two numbers read alike unless the committed
    # one is stated and checked.
    ("collect_raw's second-day coverage", "collect_raw",
     f"holds {len(day2_coverage)} of {len(day2_universe)}"),
    # The newest module was the least guarded one, which is the shape this
    # keeps taking: the docstring written last carries the figures nothing has
    # got round to tying down.
    ("spacing's sample size", "spacing",
     f"is 0.13 across {len(_spacing)} pair-days"),
    ("spacing's withdrawn prediction", "spacing",
     f"even split is "
     f"{abs(spearman(_spacing.mean_step_min, (_spacing.w_cex - 0.5).abs())):.2f}"),
    ("spacing's resolvable correlation", "spacing",
     f"rank correlation of about {_spacing_resolvable:.2f}"),
]

# Docstring claims that are true of a sign rather than of a value, and so take
# the same shape the article's direction checks take. The first version of the
# entry below was a presence check with an unreachable phrase standing in for
# the false case, which fails with a message about a string nobody wrote
# instead of a message about the data.
MODULE_DIRECTIONS = [
    # Spelled out, so the digit sweep cannot see it, and it is the sentence
    # saying the widest overlap is not one case among many. The floor it names
    # is the module's own.
    ("dependence's second-widest overlap", "dependence",
     bool(_second[0] < MIN_OVERLAP),
     f"shares fewer than {_WORDS_LOW(MIN_OVERLAP)}"),
    # The unit on the half-life, at the module that computes it. It read
    # minutes for as long as the field was called half_life_min, which is how
    # the post came to tell a reader a gap was half gone inside four minutes
    # when for the thinnest pair it was twenty-five.
    ("cointegration names the unit its half-life is in", "cointegration",
     bool((_steps > 1).to_numpy().sum() > 0),
     "observations it takes a gap to halve"),
]

# Read from the modules the two lists above actually name, rather than from a
# roll typed beside them. A hand-kept roll goes out of date in one direction
# only: an entry for a module missing from it raises a KeyError deep in the
# driver, which reads in CI as broken tooling rather than as a claim that
# drifted, and that is the third time this file has had that shape of bug.
_docs = {module: _all_docstrings(module)
         for module in sorted({m for _, m, _ in MODULE_DOCS}
                              | {m for _, m, _, _ in MODULE_DIRECTIONS})}

# The page's tables, cell for cell. Written from what each column means rather
# than copied from the builder, so a swapped column fails here while the
# workflow's diff of the regenerated page stays clean.
_TR = re.compile(r"<tr>(.*?)</tr>", re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_TH = re.compile(r"<th>(.*?)</th>", re.S)


def page_table_rows(header: tuple[str, ...]) -> list[list[str]]:
    """Pull one table out of index.html by its full header row.

    Matched on the whole header for the reason the post's version was: three of
    the four tables lead with "token", and a first-column match hands back the
    same table every time while two of them go silently unchecked.
    """
    for block in re.findall(r"<table>.*?</table>", page, re.S):
        if tuple(_TH.findall(block)) == header:
            return [_TD.findall(row) for row in _TR.findall(block)
                    if "<td" in row]
    return []


def check_page_table(name: str, header: tuple[str, ...],
                     expected: list[list[str]]) -> int:
    """The same comparison the post's tables get, on the page's markup."""
    return compare_rows(name, "PAGE", "the page", header,
                        page_table_rows(header), expected)


PAGE_TABLES = (
    ("the page's per-token table",
     ("token", "exchange weight", "exchange corrects", "pool corrects",
      "Hasbrouck bounds", "bootstrap lead", "paired minutes"),
     [[r.symbol, f"{r.w_cex:.2f}", f"{r.speed_cex:+.2f}", f"{r.speed_dex:.2f}",
       f"{r.hasbrouck_low:.2f} to {r.hasbrouck_high:.2f}",
       f"{r.lead_share:.0%}", str(int(r.paired_minutes))]
      for r in ranked_pairs.itertuples()]),
    ("the page's cross-window table",
     ("token", "29 July", "30 July", "31 July", "span"),
     [[sym,
       f"{r[LABEL]:.2f}" if pd.notna(r[LABEL]) else "-",
       f"{r[SECOND]:.2f}" if pd.notna(r[SECOND]) else "-",
       f"{r[THIRD]:.2f}" if pd.notna(r[THIRD]) else "-",
       f"{r.spread_across_windows:.2f}"]
      for sym, r in both_windows.iterrows()]),
    ("the page's dead-token table",
     ("token", "minutes the pool traded", "exchange 24h", "on-chain 24h",
      "on-chain liquidity"),
     [[t, str(int(gdead.loc[t].paired_min)),
       money(gdead.loc[t].cex_volume_24h), money(gdead.loc[t].dex_volume_24h),
       money(gdead.loc[t].dex_liquidity)]
      for t in gdead.index]),
)
for _name, _header, _expected in PAGE_TABLES:
    tally["page"] += sum(len(r) for r in _expected)
    bad += check_page_table(_name, _header, _expected)

# Three sentences whose whole content is a negation, each tied to the fact
# that makes it true. Deleting the "not" from any of them inverts a finding
# without moving a number, and all three passed every gate before this.
_refused_rows = thr[thr.w_cex.isna()]
_refusal_is_thinness = bool(_refused_rows.minutes.max() < thr_below.minutes.min())


# Direction, not just magnitude: a sentence can carry the right figure and state
# the opposite of what the data says. These tie a phrase to a sign, so the
# requirement flips if the finding ever does.
_hold_mean = float(hold_false.mean())
_drop_mean = float(sim[sim.scheme == "drop"].groupby("keep")
                   .apply(lambda x: float((x.w_cex > 0.5).mean()),
                          include_groups=False).mean())

DIRECTIONS = [
    ("quieter pools draw more exchange volume", rho < 0,
     "the quieter a pool the more the exchange prints against it"),
    # The headline itself. Flipping its first "exchange" to "pool" reverses the
    # whole finding and left the guarded half of the same sentence intact, so
    # the claim and not just the qualifier is checked.
    ("the headline names the venue that leads", led_days * 2 > pair_days,
     "Tokenized stocks are priced on the exchange"),
    # Alt text is content, not decoration: it is the whole figure for a reader
    # using a screen reader, and it carried three reversible directions.
    ("the scatter's alt text slopes the way the data does", rho < 0,
     "on log axes, sloping down"),
    ("the controls caption states the control result",
     float(bybit.weight_a) > 0.5 and float(pools.weight_a.max()) < 0.5,
     "A second exchange leads. Two pools on one mint do not behave that way"),
    ("the controls alt text puts the second exchange above the even line",
     float(bybit.weight_a) > 0.5 and float(pools.weight_a.max()) < 0.5,
     "the three pool against pool bars scatter around and below the even line"),
    ("each pass really does reach into the day before it",
     all(pd.to_datetime(lo, unit="s", utc=True).day
         < int(lab[-2:]) for (lo, _hi, _t), lab
         in zip(WINDOWS, (LABEL.rstrip("ab"), SECOND, THIRD))),
     "reaches back into the previous calendar day"),
    # Polarity. Dropping a "not" inverts a finding without moving a number or
    # touching any of the direction words above, and a sweep that removes the
    # negation from each sentence found most of them unguarded. These are the
    # ones where the inverted sentence would contradict the data, so each is
    # required exactly when the data says it.
    ("the ranking survives the market being shut",
     int((shut_pairs.w_shut > 0.5).sum()) == int((shut_pairs.w_all > 0.5).sum()),
     "So the ranking does not depend on the market being open"),
    ("lags and grids leave the leader alone",
     lag_flips == 0 and grid_agree == len(ranked_pairs),
     "changes the leader in **0 of 7** pairs"),
    ("the misalignment did not manufacture the relation",
     abs(float(align.spread_sd_bp_as_collected.median())
         - float(align.spread_sd_bp_realigned.median())) < 1.0
     and int(align.stationary_realigned.sum()) >= len(align) - 2,
     "The relation itself is not an artefact of the misalignment"),
    ("the misalignment favoured the pool, not the exchange",
     float((align_fit.w_realigned - align_fit.w_as_collected).median()) > 0,
     "The error pushes towards calling the pool the leader"),
    # This used to require the post to say the floor "is not choosing the
    # answer". Review was right that a below-floor subset cannot establish
    # that: pairs are refused for thinness, and thinness is the very variable
    # the study relates to leadership, so the fitted 16 are selected too. The
    # check now holds the weaker claim the data supports.
    # Scope repeats the floor claim, and the weaker wording has to hold there
    # too: pairs are refused for thinness, so as long as any were refused the
    # below-floor run probes the floor rather than clearing it.
    ("Scope calls the floor check what it is", thr_refused > 0,
     "a floor the sensitivity check above probes rather than clears"),
    # The paragraph that fixes the unit, checked the way the unit error itself
    # should have been: three of its sentences carry no number a sweep can bump
    # and reverse cleanly, and all three passed every gate as written backwards.
    ("a step is longer than a minute often enough for the unit to matter",
     bool((_steps > 1).to_numpy().sum() > 0),
     "are per observation and not per minute"),
    ("the rows are not evenly spaced",
     bool((_steps > 1).to_numpy().sum() > 0),
     "consecutive rows are not always a minute apart"),
    ("a coarser bar gives a larger coefficient",
     bool(float(_grid_tslax.loc["5min"].speed_dex)
          > float(_grid_tslax.loc["1min"].speed_dex)),
     "because a coarser bar is a longer step"),
    # The spacing check reads as a null, and a null is the easiest thing in an
    # article to state backwards: three of its sentences inverted cleanly and
    # passed every gate. Each is tied to the two facts that decide it, the
    # observed correlations and what a sample of this size can resolve.
    ("no spacing measure is distinguishable from nothing",
     bool(_spacing_strongest < _spacing_resolvable),
     "none of them distinguishable from nothing on a permutation"),
    ("the null is stated as the weak one it is",
     bool(_spacing_strongest < _spacing_resolvable),
     "rules out a strong relation and not a weak one"),
    # The withdrawn prediction. It required the wider-spaced pairs to sit
    # nearer an even split; they sit further from it, which is the sign this
    # reads off rather than the size.
    ("the saturation prediction came out the wrong way",
     bool(spearman(_spacing.mean_step_min,
                   (_spacing.w_cex - 0.5).abs()) > 0),
     "They sit further from it"),
    ("and the article says which way it came out",
     bool(spearman(_spacing.mean_step_min,
                   (_spacing.w_cex - 0.5).abs()) > 0),
     "opposite sign to the prediction"),
    ("the refusals are a function of thinness, not chance",
     _refusal_is_thinness, "Those are not missing at random"),
    ("exactly one pool reading is lost and none gained",
     _pool_before == 1 and _pool_after == 0,
     "One reading does not survive the correction"),
    # Said a second time where the direction of the correction is argued, and
    # the second saying was loose enough to survive being inverted: the clause
    # named a side of a ledger rather than a count, so swapping the venue in it
    # changed the meaning and moved nothing a check could see.
    ("the ledger of the correction, where its direction is argued",
     _pool_before == 1 and _pool_after == 0,
     "takes the one pool reading and hands back none"),
    ("the discount changes the number, so it is called arithmetic",
     round(float(sign_test(round(n_effective), round(n_effective))), 4)
     != round(float(sign_test(n_ranked, n_ranked)), 4),
     "That is arithmetic, not a second test"),
    ("the tally's rule is a weight above an even split",
     led_days * 2 > pair_days,
     "one mechanical rule, a weight above an even split"),
    ("the below-floor sample is itself selected",
     thr_refused > 0,
     "agreement inside them cannot rule out"),
    ("the below-floor pairs lean the same way as the kept ones",
     (float((thr_below.w_cex > 0.5).mean()) > 0.5)
     == (float((thr_kept.w_cex > 0.5).mean()) > 0.5),
     "It is a sensitivity check on the floor, not a demonstration that the "
     "floor is neutral"),
    ("the controls read the close, so they were never misaligned",
     GATE_FIELDS.index("close") != GATE_FIELDS.index("open"),
     "Bybit and MEXC return their closes at field four"),
    ("the below-floor readings are kept out of every tally",
     not (set(thr_below.symbol) & set(ranked_pairs.symbol)
          & set(thr_below[thr_below.window == LABEL].symbol)),
     "Those readings are not evidence and are not counted anywhere"),
    # Tied to the endpoints the collector actually calls, not merely required
    # to be present: "one-minute" is the whole sampling basis, and swapping it
    # for "five-minute" left every check green.
    ("the bar size the study samples at",
     "interval=1m" in _collector and "ohlcv/minute?aggregate=1" in _collector,
     "the last thousand one-minute bars"),
    ("the title says the same", rho < 0,
     "and the quieter the chain the more the exchange prints"),
    ("the exchange is named the leader in words", led_days * 2 > pair_days,
     "the exchange leads and the Solana pool follows"),
    ("the correlation is described in the right direction", rho < 0,
     "between how much a pool trades and how many exchange dollars are "
     "printed against it"),
    ("the second exchange leads its pool too", float(bybit.weight_a) > 0.5,
     "Bybit leads too"),
    ("the spread reverts rather than wanders",
     bool(ranked_pairs.spread_stationary.all()), "the spread is stationary"),
    ("forward-filling is the worse scheme", _drop_mean < _hold_mean,
     "The ranked pairs sit on the lower curve"),
    ("an imposed weight over one is called impossible",
     float(vecrow.loc["GOOGLX"].w_imposed) > 1,
     "is above one and so impossible"),
]

flat_post = _flat(post)
for label, got, want, text in checks:
    drift = abs(got - want) > 0.011
    missing = not _present(text, flat_post)
    tally["post"] += 1
    if drift:
        print(f"  [DATA] {label}: recomputed {got}, pipeline had {want}")
    if missing:
        print(f"  [POST] {label}: post does not contain {text!r}")
    bad += drift + missing

# Per-token volumes as the two tables print them.
tokens = ("VTIX", "ACNX", "NFLXX", "AZNX", "TQQQX", "KOX", "MSTRX",
          "TSLAX", "CRCLX", "NVDAX", "QQQX", "UNHX", "MCDX")
for token in tokens:
    row = u[u.symbol == token].iloc[0]
    for value in (f"${row.cex_volume_24h:,}", f"${row.dex_volume_24h:,}"):
        tally["post"] += 1
        if value not in flat_post:
            print(f"  [POST] {token}: {value} not found in post")
            bad += 1

# The docstring above states how many direction checks there are and what the
# sweep measured. A docstring that reports coverage is a claim like any other,
# and this one was wrong twice before it was checked: it carried the pre-fix
# number, and then a count that had drifted from the list. So it is checked.
# Spelled out for the docstring's own count. A bare dict lookup here crashed
# the file with a KeyError the moment the count left the table, which is the
# same fragility already fixed one table above; a miss now yields digits, so
# the check fails and names itself instead of dying.
_WORDS = dict(_SPELLED)
_WORDS.update({25: "twenty-five", 27: "twenty-seven", 28: "twenty-eight",
               29: "twenty-nine", 30: "thirty", 31: "thirty-one",
               34: "thirty-four", 35: "thirty-five"})
_doc = _flat(__doc__ or "")
# Without the article, so the sentence can start where the prose wants it
# to. Requiring "The N ..." forced a capital letter into mid-sentence.
if _flat(f"{_WORDS.get(len(DIRECTIONS), len(DIRECTIONS))} DIRECTIONS entries below") not in _doc:
    bad += 1
    print(f"  [SELF] the direction-check count: this file's docstring does "
          f"not say there are {len(DIRECTIONS)}")
# This one counts a list in this file rather than numbers in a document, so no
# edit to any document can trip it and a sweep can leave it running.
tally["this file"] += 1

# The universe the sweep runs over, counted the same way the sweep counts it.
# The stated total went stale the moment the post gained six new figures, so it
# is derived here rather than typed; only the caught count stays hand-measured,
# and it cannot move without this total moving first.
# The trailing guard rejects a digit or a letter but must allow a full
# stop: an earlier version rejected "." too, so every number ending a
# sentence was invisible to the count and to the sweep built on it. Six
# were hidden that way, including the discounted p-value and both DOI
# fragments. All six turned out to be guarded, but the denominator the
# docstring reported was wrong.
_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\d])(?![a-zA-Z])")
_SIGNED = re.compile(r"(?<![\w.])-\d+(?:\.\d+)?(?![\d])(?![a-zA-Z])")
_distinct = len(set(_NUMBER.findall(post)))
_signed = sum(len(set(_SIGNED.findall(_t))) for _t in (post, readme, page))
_readme_nums = len(set(_NUMBER.findall(readme)))
_page_nums = len(set(_NUMBER.findall(page)))
# Counted per module and summed, which is how the sweep counts it: the same
# figure in two modules is two chances to drift, not one.
_doc_nums = sum(
    len(set(_NUMBER.findall(_all_docstrings(_p.stem))))
    for _p in sorted((base / "analysis").glob("*.py"))
    if _p.name != "verify.py")

# Every denominator the docstring quotes, counted from the document it
# describes rather than typed. Only the caught counts stay hand-measured, and
# none can move without its denominator moving first. These five are the ones
# `--sweep` drops, for the reason the docstring gives.
_SELF_COUNTS = (
    ("the post's numbers",
     f"Bumping each of the {_distinct} distinct numbers"),
    ("the module docstrings' numbers",
     f"carry {_WORDS.get(_doc_nums, _doc_nums)} figures between them"),
    ("the README's numbers",
     f"each of the {_WORDS.get(_readme_nums, _readme_nums)} numbers in "
     f"the README"),
    ("the page's numbers", f"of its {_page_nums} distinct numbers"),
    ("the signed figures",
     f"each of the {_WORDS.get(_signed, _signed)} signed figures"),
)
SWEEPING = "--sweep" in sys.argv
# Rejected rather than ignored. The one argument this takes exists to keep a
# mutation sweep honest, so a sweep run with it misspelled would quietly go
# back to scoring the counter, which is the failure it was written to end.
_unknown = [a for a in sys.argv[1:] if a != "--sweep"]
if _unknown:
    raise SystemExit(f"verify.py: unknown argument {_unknown[0]!r}\n"
                     f"usage: verify.py [--sweep]\n"
                     f"  --sweep  drop the checks that count distinct numbers, "
                     f"which a mutation sweep trips whatever it is testing")
for _label, _phrase in () if SWEEPING else _SELF_COUNTS:
    tally["this file"] += 1
    if _flat(_phrase) not in _doc:
        bad += 1
        print(f"  [SELF] {_label}: this file's docstring does not say "
              f"{_phrase!r}")

# One pass over every phrase search, in place of the loop-per-list this grew
# into. Six loops meant the failure message written six times, and it had
# already drifted twice. Two lists both printed [DIRECTION] with no way to tell
# which document had failed. [DOC] and [DOCSTRING] sat four characters apart
# meaning the docstring of this file and the docstring of another. A reader
# meets those strings at the one moment they are debugging, so the message is
# built once and always names the file.
_flat_docs = {_name: _flat(_text) for _name, _text in _docs.items()}
_SEARCHES = (
    [("page", "index.html", n, True, p, flat_page) for n, p in PAGE]
    + [("readme", "README.md", n, True, p, flat_readme)
       for n, p in README_CLAIMS]
    + [("readme", "README.md", n, h, p, flat_readme)
       for n, h, p in README_DIRECTIONS]
    + [("module", f"analysis/{m}.py", n, True, p, _flat_docs[m])
       for n, m, p in MODULE_DOCS]
    + [("module", f"analysis/{m}.py", n, h, p, _flat_docs[m])
       for n, m, h, p in MODULE_DIRECTIONS]
    + [("post", "post/index.md", n, h, p, flat_post) for n, h, p in DIRECTIONS]
)
for _surface, _where, _name, _holds, _phrase, _haystack in _SEARCHES:
    tally[_surface] += 1
    if _holds == _present(_phrase, _haystack):
        continue
    bad += 1
    _verb = "does not say" if _holds else "should not say"
    print(f"  [{_surface.upper()}] {_where} {_verb} {_phrase!r} ({_name})")

_WHERE = {"post": "post/index.md", "readme": "README.md",
          "page": "index.html", "module": "module docstrings",
          "this file": "this file's own docstring"}
# A surface counted but not named would leave the parts adding to less than the
# whole, and a reader checking the arithmetic would be right and confused.
_unnamed = sorted(set(tally) - set(_WHERE))
if _unnamed:  # pragma: no cover - a new surface has to be named here
    raise SystemExit(f"verify.py: counted but unnamed surfaces: {_unnamed}")
print(f" searched {sum(tally.values())} claims: "
      + ", ".join(f"{tally[key]} in {name}"
                  for key, name in _WHERE.items() if tally[key]))
print(f"FAILED: {bad}")
# Exit non-zero on any failure. Without this the CI step and the README
# reproduce flow both pass whatever the numbers say.
sys.exit(1 if bad else 0)
