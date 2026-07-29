"""Run the discovery test per token per session, and split by market hours.

The underlying equity stops trading at the closing bell while the token does
not, so the two venues are quoting different things overnight: on-chain the
token is whatever the pool says, on the exchange it is whatever the book says,
and neither is anchored to a live equity price. Leadership measured across that
boundary mixes two regimes, so every run is reported open and closed as well as
whole.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from analysis.collect import cex_bars, dex_history, load_universe
from analysis.discovery import information_share

DATA = Path(__file__).resolve().parent.parent / "data"

# Regular US equity session in UTC. The DST boundary matters: on US summer time
# the session is 13:30 to 20:00 UTC, which covers the window used here.
OPEN_UTC = (13, 30)
CLOSE_UTC = (20, 0)

__all__ = ["run_panel", "session_mask"]


def session_mask(index: pd.DatetimeIndex) -> pd.Series:
    """True where the US equity market is open (weekday, regular session)."""
    minute = index.hour * 60 + index.minute
    start = OPEN_UTC[0] * 60 + OPEN_UTC[1]
    end = CLOSE_UTC[0] * 60 + CLOSE_UTC[1]
    weekday = index.dayofweek < 5
    return pd.Series((minute >= start) & (minute < end) & weekday, index=index)


def _measure(paired: pd.DataFrame, label: str, symbol: str) -> dict | None:
    moves_cex = int((paired.cex.diff() != 0).sum())
    moves_dex = int((paired.dex.diff() != 0).sum())
    row = {
        "symbol": symbol, "regime": label, "minutes": len(paired),
        "cex_moves": moves_cex, "dex_moves": moves_dex,
        "mean_gap_pct": round(float(((paired.cex / paired.dex - 1) * 100).mean()), 3),
    }
    if len(paired) < 80 or moves_cex < 20 or moves_dex < 20:
        return row
    try:
        result = information_share(paired.cex, paired.dex)
    except ValueError:
        return row
    row.update(w_cex=round(result.weight_a, 3),
               speed_cex=round(result.speed_a, 3),
               speed_dex=round(result.speed_b, 3))
    return row


def run_panel(pages: int = 3, pause: float = 4.0) -> pd.DataFrame:
    """Pull both venues for every paired token and measure per regime."""
    universe = load_universe()
    rows: list[dict] = []
    for _, token in universe.iterrows():
        try:
            cex = cex_bars(token.cex_pair, limit=1000)
            dex = dex_history(token.pool, pages=pages)
        except Exception as exc:  # noqa: BLE001 - one bad token must not stop the run
            print(f"  {token.symbol}: {exc}", flush=True)
            continue
        paired = pd.concat([cex.rename("cex"), dex.rename("dex")], axis=1).dropna()
        if paired.empty:
            continue
        paired.index = pd.to_datetime(paired.index, unit="s", utc=True)
        open_now = session_mask(paired.index)
        for label, frame in (("all", paired),
                             ("open", paired[open_now.to_numpy()]),
                             ("closed", paired[~open_now.to_numpy()])):
            if len(frame) >= 30:
                rows.append(_measure(frame, label, token.symbol))
        print(f"  done {token.symbol} ({len(paired)} paired minutes)", flush=True)
        time.sleep(pause)
    panel = pd.DataFrame([r for r in rows if r])
    DATA.mkdir(parents=True, exist_ok=True)
    panel.to_csv(DATA / "panel_sessions.csv", index=False)
    return panel
