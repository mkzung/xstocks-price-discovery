"""Is the coin-flip null entitled to treat the pairs as separate draws.

The post's only formal significance statement is a sign test: seven of seven
pairs pointing one way carries p = 0.0156 under a null where each pair is an
independent coin. Nothing tested that null's assumption, and there is an
obvious reason to doubt it. These are all US equities. Their prices move
together, so their tokens move together, and seven pairs driven by one market
are not seven pieces of evidence.

The objection is right about the prices and wrong about the object under test.
The error-correction model is not fitted to a price; it is fitted to the gap
between the two venues quoting one mint. A market-wide move enters both sides
of a pair at once and largely cancels in that gap, so what is left is the
arbitrage relation between two venues on one asset. That is a claim about data,
so it is measured rather than argued: cross-token correlation of one-minute
changes on the exchange leg, the pool leg and the spread the model uses.

Two things the measurement has to get right, both of which a first pass got
wrong. A change is only a one-minute change if the previous bar is exactly a
minute earlier; differencing a sparse series silently produces changes across
gaps of any length. And two tokens can only be compared on minutes where both
have such a change, which the pools' sparseness makes much rarer than their
bar counts suggest: on the third pass, two tokens holding 433 and 398 bars
share only 86 usable minutes, and every other pairing shares fewer than sixty.
The overlap counts are reported alongside the correlations so that a number
resting on thin overlap is visible as one.

The measurement does not vindicate the null by itself, so the module also
prices the dependence that remains. Discounting the sample by the mean spread
correlation gives an effective number of independent pairs and the sign test is
recomputed on it. That discount is borrowed from the correlated-mean case and
applied to binary outcomes, which makes it a rough and deliberately harsh
adjustment rather than a replacement p-value: it passes the whole correlation
of the underlying series through to the sign of each fit, when a sign only
moves if the shared component pushes a weight across an even split.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.bootstrap import sign_test  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

# A correlation on a handful of minutes is noise with a decimal point. Pairs
# below this many jointly observed one-minute changes are counted and reported
# but kept out of the summary statistics.
MIN_OVERLAP = 60

__all__ = ["minute_changes", "cross_token_correlation", "effective_pairs", "run"]


def minute_changes(series: pd.Series) -> pd.Series:
    """Changes across exactly one minute, dropping every change across a gap."""
    diffs = series.diff()
    steps = series.index.to_series().diff().dt.total_seconds()
    return diffs[steps.to_numpy() == 60.0].dropna()


def _legs(label: str) -> dict[str, dict[str, pd.Series]]:
    ranked = pd.read_csv(DATA / f"robustness_{label}.csv")
    legs: dict[str, dict[str, pd.Series]] = {"exchange": {}, "pool": {}, "spread": {}}
    for symbol in ranked[ranked.verdict == "ranked"].symbol:
        frame = pd.read_csv(RAW / label / f"{symbol}.csv", index_col="ts")
        frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
        cex, dex = np.log(frame.cex), np.log(frame.dex)
        legs["exchange"][symbol] = minute_changes(cex)
        legs["pool"][symbol] = minute_changes(dex)
        legs["spread"][symbol] = minute_changes(cex - dex)
    return legs


def cross_token_correlation(label: str) -> pd.DataFrame:
    """One row per leg: how much the tokens move together, and on how much data."""
    rows = []
    for leg, columns in _legs(label).items():
        kept, overlaps, thin = [], [], 0
        for a, b in combinations(sorted(columns), 2):
            joined = pd.concat([columns[a], columns[b]], axis=1,
                               join="inner").dropna()
            overlaps.append(len(joined))
            if len(joined) < MIN_OVERLAP:
                thin += 1
                continue
            kept.append(float(np.corrcoef(joined.iloc[:, 0],
                                          joined.iloc[:, 1])[0, 1]))
        vals = pd.Series(kept, dtype=float)
        rows.append({
            "window": label, "leg": leg,
            "token_pairs": len(overlaps),
            "usable_pairs": len(kept),
            "pairs_below_floor": thin,
            "median_overlap": int(np.median(overlaps)) if overlaps else 0,
            "median": round(float(vals.median()), 3) if len(vals) else np.nan,
            "mean": round(float(vals.mean()), 3) if len(vals) else np.nan,
            "low": round(float(vals.min()), 3) if len(vals) else np.nan,
            "high": round(float(vals.max()), 3) if len(vals) else np.nan,
        })
    return pd.DataFrame(rows)


def effective_pairs(n: int, mean_correlation: float) -> float:
    """How many independent pairs `n` correlated ones are worth."""
    rho = max(0.0, float(mean_correlation))
    return n / (1 + (n - 1) * rho)


def run(labels: list[str]) -> pd.DataFrame:
    table = pd.concat([cross_token_correlation(x) for x in labels],
                      ignore_index=True)
    table.to_csv(DATA / "dependence.csv", index=False)
    return table


if __name__ == "__main__":
    windows = sys.argv[1:] or ["2026-07-29b", "2026-07-30", "2026-07-31"]
    table = run(windows)
    print("Cross-token correlation of one-minute changes.\n")
    print(table.to_string(index=False))

    first = windows[0]
    spread = table[(table.window == first) & (table.leg == "spread")].iloc[0]
    exchange = table[(table.window == first) & (table.leg == "exchange")].iloc[0]
    ranked = pd.read_csv(DATA / f"robustness_{first}.csv")
    n = int((ranked.verdict == "ranked").sum())
    n_eff = effective_pairs(n, spread["mean"])
    rounded = int(round(n_eff))

    print(f"\nThe pass the p-value comes from is {first}, where "
          f"{spread['usable_pairs']} of {spread['token_pairs']} token pairs")
    print("clear the overlap floor. On those:")
    print(f"  exchange legs move together at a median "
          f"{exchange['median']:.2f}")
    print(f"  the spreads the model fits do not, at a median "
          f"{spread['median']:.2f}")
    print(f"\nsign test as reported, {n} of {n}: p = {sign_test(n, n):.4f}")
    print(f"discounted by a mean spread correlation of {spread['mean']:.2f}, "
          f"{n} pairs are worth {n_eff:.1f}")
    print(f"sign test on {rounded} of {rounded}: "
          f"p = {sign_test(rounded, rounded):.4f}")
