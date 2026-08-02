"""The two venues' minute bars were not describing the same instant.

Both endpoints stamp a minute bar with the moment it opens, and both were read
for a price, but not for the same one. Gate's candlestick array is
`[timestamp, quote volume, close, high, low, open, base volume, closed]`, and
the collector took field five, the open, which is the price at the stamp.
GeckoTerminal's is `[timestamp, open, high, low, close, volume]`, and the
collector took field four, the close, which is the price sixty seconds after
the stamp. So at every timestamp the pool series held a price one minute newer
than the exchange series beside it.

Two independent confirmations. Gate's own tape shows the open of a bar equal to
the close of the one before it, and GeckoTerminal's shows the same, which fixes
what each field is. And the study's own committed minutes show it: correlate
one-minute exchange returns against pool returns at lags of minus three to plus
three, and the largest correlation sits at plus one rather than zero on 14 of the
23 ranked pairs, by margins as wide as 0.88 against 0.12.

The direction matters for how much trouble this is. A pool carrying newer
information than the venue it is compared against is a pool given a head start,
so the misalignment favours the conclusion that the pool leads, which is the
opposite of what the study reports. It is still an error and it still has to be
corrected rather than argued away.

Correcting it needs no new collection. Gate's close for minute t is Gate's open
for minute t plus one, which is the next row of the same committed file, so the
exchange series can be moved onto the same instant as the pool series.
Rows whose following minute was never collected are dropped rather than
interpolated. This module refits every ranked pair both ways and reports the
difference, so the size of the error is a number rather than an argument.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.cointegration import adf  # noqa: E402
from analysis.discovery import information_share  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

# Below this many rows a spread standard deviation and a unit-root test
# are noise with a decimal point, so they are left blank instead.
MIN_SPREAD_ROWS = 20

__all__ = ["realign", "lag_profile", "run"]


def realign(paired: pd.DataFrame) -> pd.DataFrame:
    """Put both venues on the close of the same minute.

    The pool column already is that close. The exchange column is the open, and
    the open of the next minute is the close of this one, so the exchange
    column is taken from the following row. Only rows whose following minute was
    collected survive, because a gap would otherwise be crossed silently.
    """
    frame = paired.sort_index()
    nxt = frame.index.to_series().shift(-1)
    usable = (nxt - frame.index.to_series()) == 60
    out = pd.DataFrame({
        "cex": frame.cex.shift(-1)[usable.to_numpy()],
        "dex": frame.dex[usable.to_numpy()],
    })
    return out.dropna()


def lag_profile(paired: pd.DataFrame, span: int = 3) -> dict[int, float]:
    """Correlation of one-minute returns at each lag, on a gapless reindex."""
    frame = paired.sort_index()
    stamps = pd.to_datetime(frame.index, unit="s", utc=True)
    dense = frame.set_axis(stamps).reindex(
        pd.date_range(stamps.min(), stamps.max(), freq="1min"))
    dc, dd = np.log(dense.cex).diff(), np.log(dense.dex).diff()
    return {k: float(dc.corr(dd.shift(k))) for k in range(-span, span + 1)}


def run(labels: list[str]) -> pd.DataFrame:
    rows = []
    for label in labels:
        ranked = pd.read_csv(DATA / f"robustness_{label}.csv")
        for symbol in ranked[ranked.verdict == "ranked"].symbol:
            paired = pd.read_csv(RAW / label / f"{symbol}.csv", index_col="ts")
            fixed = realign(paired)
            entry = {"window": label, "symbol": symbol,
                     "rows_as_collected": len(paired), "rows_realigned": len(fixed)}
            entry["w_as_collected"] = round(
                information_share(paired.cex, paired.dex).weight_a, 3)
            try:
                entry["w_realigned"] = round(
                    information_share(fixed.cex, fixed.dex).weight_a, 3)
            except ValueError:
                entry["w_realigned"] = None
            # A realigned frame can come back empty, when no two collected
            # minutes were adjacent, and a flat pair gives a correlation of
            # nothing at every lag. Both are answered with a blank cell rather
            # than a traceback: a run that dies on one thin token tells a
            # reader less than a table that says which token had nothing to
            # say.
            for name, frame in (("as_collected", paired), ("realigned", fixed)):
                if len(frame) < MIN_SPREAD_ROWS:
                    entry[f"spread_sd_bp_{name}"] = None
                    entry[f"stationary_{name}"] = None
                    continue
                spread = np.log(frame.cex) - np.log(frame.dex)
                entry[f"spread_sd_bp_{name}"] = round(float(spread.std()) * 1e4, 1)
                unit_root = adf(spread - spread.mean())
                entry[f"stationary_{name}"] = bool(unit_root.rejects_unit_root())
            profile = lag_profile(paired)
            usable = [(v, k) for k, v in profile.items() if pd.notna(v)]
            best = max(usable) if usable else (None, None)
            entry["best_lag"] = best[1]
            entry["corr_at_zero"] = (round(profile[0], 3)
                                     if pd.notna(profile[0]) else None)
            entry["corr_at_best"] = round(best[0], 3) if usable else None
            rows.append(entry)
    table = pd.DataFrame(rows)
    table.to_csv(DATA / "alignment.csv", index=False)
    return table


if __name__ == "__main__":
    windows = sys.argv[1:] or ["2026-07-29b", "2026-07-30", "2026-07-31"]
    table = run(windows)
    print(table.to_string(index=False))

    both = table.dropna(subset=["w_realigned"])
    print(f"\npairs refitted on the corrected alignment: {len(both)} of {len(table)}")
    print(f"  exchange leads, as collected: "
          f"{int((both.w_as_collected > 0.5).sum())} of {len(both)}")
    print(f"  exchange leads, realigned:    "
          f"{int((both.w_realigned > 0.5).sum())} of {len(both)}")
    moved = (both.w_realigned - both.w_as_collected)
    print(f"  median weight {both.w_as_collected.median():.2f} -> "
          f"{both.w_realigned.median():.2f}, largest single move "
          f"{moved.abs().max():.2f}")
    print(f"  pairs whose leader changes: "
          f"{int(((both.w_as_collected > 0.5) != (both.w_realigned > 0.5)).sum())}")
    print(f"\n  best lag was +1 on {int((table.best_lag == 1).sum())} of "
          f"{len(table)} pairs before the correction")
    print(f"  spread size barely moves: median "
          f"{table.spread_sd_bp_as_collected.median():.1f} bp as collected "
          f"against {table.spread_sd_bp_realigned.median():.1f} realigned")
    print(f"  spread stationary in {int(table.stationary_realigned.sum())} of "
          f"{len(table)} realigned, against "
          f"{int(table.stationary_as_collected.sum())} as collected")
