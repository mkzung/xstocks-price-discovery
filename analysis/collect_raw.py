"""Pull and keep the paired minute series themselves, not only what was fit to them.

The first version of this study committed the fitted panel and threw the
underlying minute bars away. That made three things impossible to check after
the fact: how often each pool actually printed, how far apart consecutive
observations really were, and whether the spread each error-correction model
rests on is stationary. Every one of those is a live objection to the result, so
the series go in the repository alongside the numbers drawn from them.

The output is one CSV per token under `raw/<run>/`, holding the exchange close,
the pool close, and the epoch second of each paired minute. A run label makes a
second collection an out-of-sample window rather than an overwrite.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.collect import (  # noqa: E402
    build_universe, cex_bars, dex_history, load_universe,
)

RAW = BASE / "raw"

__all__ = ["collect"]


def collect(run: str, *, pages: int = 3, pause: float = 4.0,
            refresh_universe: bool = False) -> pd.DataFrame:
    """Write one paired minute series per token and return a coverage summary.

    Arguments:
        run: Label for this collection, used as the directory name.
        pages: Pages of pool history to walk backwards through.
        pause: Seconds between tokens, since the pool API rate-limits hard.
        refresh_universe: Rebuild the paired universe and snapshot its
            24-hour volumes into the run directory. The volume ratio behind the
            post's headline correlation was measured once, on one snapshot, so a
            second window cannot re-test it without its own snapshot.

    Returns:
        One row per token: how many minutes each venue covered, how many paired,
        and how much of the overlapping window the pool actually printed in.
    """
    out = RAW / run
    out.mkdir(parents=True, exist_ok=True)
    if refresh_universe:
        # build_universe writes data/universe.csv, which the committed panel and
        # every volume figure in the post are keyed to. Snapshot it into the run
        # directory and put the committed file back, or a fresh collection
        # silently invalidates the published numbers. It did once.
        committed = BASE / "data" / "universe.csv"
        keep = committed.read_bytes() if committed.exists() else None
        snapshot = build_universe()
        snapshot.to_csv(out / "universe.csv", index=False)
        if keep is not None:
            committed.write_bytes(keep)
        print(f"  universe snapshot: {len(snapshot)} paired tokens, "
              f"data/universe.csv left untouched", flush=True)
    summary = []
    for _, token in load_universe().iterrows():
        try:
            cex = cex_bars(token.cex_pair, limit=1000)
            dex = dex_history(token.pool, pages=pages)
        except Exception as exc:  # noqa: BLE001 - one bad token must not stop the run
            print(f"  {token.symbol}: {exc}", flush=True)
            continue
        if cex.empty or dex.empty:
            print(f"  {token.symbol}: empty on one side", flush=True)
            continue

        # The window both venues cover. The pool's fill rate is only meaningful
        # against the minutes the exchange was also available for.
        lo = max(cex.index.min(), dex.index.min())
        hi = min(cex.index.max(), dex.index.max())
        window = int((hi - lo) // 60) + 1 if hi > lo else 0
        paired = pd.concat([cex.rename("cex"), dex.rename("dex")],
                           axis=1).dropna()
        paired = paired[(paired.index >= lo) & (paired.index <= hi)]
        if paired.empty or window <= 0:
            print(f"  {token.symbol}: no overlap", flush=True)
            continue
        paired.index.name = "ts"
        paired.to_csv(out / f"{token.symbol}.csv")

        gaps = pd.Series(paired.index).diff().dropna() // 60
        summary.append({
            "symbol": token.symbol,
            "cex_minutes": len(cex), "dex_minutes": len(dex),
            "window_minutes": window, "paired_minutes": len(paired),
            "fill_rate": round(len(paired) / window, 4),
            "median_gap_min": int(gaps.median()) if len(gaps) else 0,
            "max_gap_min": int(gaps.max()) if len(gaps) else 0,
            "consecutive_share": round(float((gaps == 1).mean()), 4) if len(gaps) else 0.0,
            "first_ts": int(paired.index.min()), "last_ts": int(paired.index.max()),
        })
        print(f"  {token.symbol}: {len(paired)} paired of {window} window minutes "
              f"({len(paired) / window:.0%})", flush=True)
        time.sleep(pause)

    frame = pd.DataFrame(summary)
    frame.to_csv(out / "coverage.csv", index=False)
    return frame


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    fresh = "--refresh-universe" in sys.argv
    f = collect(label, refresh_universe=fresh)
    print(f"\nwrote raw/{label}/, {len(f)} tokens")
    if len(f):
        print(f"  fill rate: {f.fill_rate.min():.0%} to {f.fill_rate.max():.0%}, "
              f"median {f.fill_rate.median():.0%}")
        print(f"  consecutive-minute share: median {f.consecutive_share.median():.0%}")
        print(f"  largest gap in any token: {f.max_gap_min.max()} minutes")
