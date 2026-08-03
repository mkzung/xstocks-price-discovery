"""Second exchange and second pool: is the lead Gate's, or any order book's.

One venue pair cannot separate two explanations. Gate could be leading because
it is Gate, or because an order book with a maker queue prices faster than a
constant-product pool no matter whose book it is. Adding a second exchange
answers that. Adding a second pool on the same mint answers the mirror
question: whether the pool's lag is the venue or just that particular pool.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from analysis.collect import MINT_PREFIX, _get, dex_history
from analysis.discovery import information_share

DATA = Path(__file__).resolve().parent.parent / "data"

__all__ = ["bybit_bars", "mexc_bars", "pools_for_mint", "run_venue_matrix"]


def bybit_bars(symbol: str, limit: int = 1000) -> pd.Series:
    """Bybit spot 1m closes, indexed by epoch second."""
    payload = _get("https://api.bybit.com/v5/market/kline"
                   f"?category=spot&symbol={symbol}&interval=1&limit={limit}")
    rows = payload["result"]["list"]
    return pd.Series({int(r[0]) // 1000: float(r[4]) for r in rows}).sort_index()


def mexc_bars(symbol: str, limit: int = 1000) -> pd.Series:
    """MEXC spot 1m closes, indexed by epoch second."""
    rows = _get("https://api.mexc.com/api/v3/klines"
                f"?symbol={symbol}&interval=1m&limit={limit}")
    return pd.Series({int(r[0]) // 1000: float(r[4]) for r in rows}).sort_index()


def pools_for_mint(symbol: str, mint_prefix: str = MINT_PREFIX) -> list[dict]:
    """Every Solana pool on the issuer's mint, deepest first.

    The prefix comes from collect rather than a literal here. Three places
    screen on it, this one had its own copy, and a copy of a constant is a
    constant that is right until someone changes the other one.
    """
    found = _get(f"https://api.dexscreener.com/latest/dex/search?q={symbol}")
    pools = [
        p for p in (found.get("pairs") or [])
        if p.get("chainId") == "solana"
        and p["baseToken"]["symbol"].upper() == symbol.upper()
        and p["baseToken"]["address"].startswith(mint_prefix)
    ]
    return sorted(pools,
                  key=lambda p: -float(p.get("liquidity", {}).get("usd") or 0))


def _pair_up(left: pd.Series, right: pd.Series) -> pd.DataFrame:
    return pd.concat([left.rename("a"), right.rename("b")], axis=1).dropna()


def _rank(left: pd.Series, right: pd.Series, label_a: str, label_b: str,
          token: str) -> dict | None:
    paired = _pair_up(left, right)
    moves_a = int((paired.a.diff() != 0).sum())
    moves_b = int((paired.b.diff() != 0).sum())
    row = {"token": token, "venue_a": label_a, "venue_b": label_b,
           "minutes": len(paired), "moves_a": moves_a, "moves_b": moves_b}
    if len(paired) < 80 or moves_a < 20 or moves_b < 20:
        return row
    try:
        result = information_share(paired.a, paired.b)
    except ValueError:
        return row
    row.update(weight_a=round(result.weight_a, 3),
               speed_a=round(result.speed_a, 3),
               speed_b=round(result.speed_b, 3))
    return row


def run_venue_matrix(pause: float = 4.0) -> pd.DataFrame:
    """Rank exchange against pool on a second exchange, and pool against pool."""
    rows: list[dict] = []
    # A second order book against the same token's deepest pool.
    for token, fetch, label in (("TSLAX", lambda: bybit_bars("TSLAXUSDT"), "bybit"),
                                ("AMZNX", lambda: mexc_bars("AMZNXUSDT"), "mexc"),
                                ("METAX", lambda: mexc_bars("METAXUSDT"), "mexc")):
        try:
            cex = fetch()
            pools = pools_for_mint(token)
            if not pools:
                continue
            pool = dex_history(pools[0]["pairAddress"], pages=2)
        except Exception as exc:  # noqa: BLE001
            print(f"  {token} {label}: {exc}", flush=True)
            continue
        rows.append(_rank(cex, pool, label, "pool", token))
        print(f"  done {token} {label} vs pool", flush=True)
        time.sleep(pause)
    # Two pools on the same mint, to see whether the lag is the venue type.
    for token in ("CRCLX", "NVDAX", "TSLAX"):
        try:
            pools = pools_for_mint(token)
            if len(pools) < 2:
                continue
            deep = dex_history(pools[0]["pairAddress"], pages=2)
            second = dex_history(pools[1]["pairAddress"], pages=2)
        except Exception as exc:  # noqa: BLE001
            print(f"  {token} pool pair: {exc}", flush=True)
            continue
        rows.append(_rank(deep, second, "pool_deep", "pool_second", token))
        print(f"  done {token} pool vs pool", flush=True)
        time.sleep(pause)
    matrix = pd.DataFrame([r for r in rows if r])
    DATA.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(DATA / "venue_matrix.csv", index=False)
    return matrix
