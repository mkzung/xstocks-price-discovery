"""Redo the open-against-shut split on data a reader actually has.

The first day's session panel was fitted before the pipeline started keeping
minute series, so its regressions cannot be re-run from anything committed
here. Review put it plainly: an aggregate CSV is a record of a result, not a
way to reproduce it.

The series passes do keep their minutes, and those rows carry epoch timestamps,
so the same split runs on them. This recomputes it per pass: the whole window
against the hours when the US equity market is shut, using the same session
mask the original panel used.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.discovery import information_share  # noqa: E402
from analysis.panel import session_mask  # noqa: E402
from analysis.robustness import MIN_PAIRED  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

__all__ = ["split"]


def split(labels: list[str]) -> pd.DataFrame:
    """Fit each ranked pair on the whole window and on the shut hours."""
    rows = []
    for label in labels:
        ranked = pd.read_csv(DATA / f"robustness_{label}.csv")
        for symbol in ranked[ranked.verdict == "ranked"].symbol:
            paired = pd.read_csv(RAW / label / f"{symbol}.csv", index_col="ts")
            paired.index = pd.to_datetime(paired.index, unit="s", utc=True)
            shut = paired[~session_mask(paired.index).to_numpy()]
            entry = {"window": label, "symbol": symbol,
                     "minutes_all": len(paired), "minutes_shut": len(shut)}
            entry["w_all"] = round(
                information_share(paired.cex, paired.dex).weight_a, 3)
            if len(shut) >= MIN_PAIRED:
                entry["w_shut"] = round(
                    information_share(shut.cex, shut.dex).weight_a, 3)
            rows.append(entry)
    frame = pd.DataFrame(rows)
    frame.to_csv(DATA / "sessions_from_series.csv", index=False)
    return frame


if __name__ == "__main__":
    labels = sys.argv[1:] or ["2026-07-29b", "2026-07-30", "2026-07-31"]
    f = split(labels)
    both = f.dropna(subset=["w_shut"])
    print(f"pairs with enough shut-hours minutes: {len(both)} of {len(f)}")
    print(both[["window", "symbol", "minutes_shut", "w_all", "w_shut"]]
          .to_string(index=False))
    if len(both):
        print(f"\n  exchange leads on shut hours in "
              f"{int((both.w_shut > 0.5).sum())} of {len(both)}")
        print(f"  largest move between regimes: "
              f"{(both.w_shut - both.w_all).abs().max():.2f}")
