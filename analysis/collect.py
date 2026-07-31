"""Build the paired universe and pull minute bars from both venues.

A token qualifies only if the same Backed Finance mint trades on a centralised
exchange and in a Solana pool. Symbol search alone is not enough: several
tickers collide with unrelated mints, so every pool is checked against the
`Xs` mint prefix that Backed uses for xStocks.
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

import certifi
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
CTX = ssl.create_default_context(cafile=certifi.where())
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
MINT_PREFIX = "Xs"  # Backed Finance vanity prefix for xStocks mints
# Pairs printing less than this on the exchange in 24 hours are skipped when
# the universe is built: a tape that thin cannot be ranked against anything.
# The post discloses the floor, and verify.py ties its sentence to this value.
MIN_CEX_VOLUME = 20_000.0

__all__ = ["build_universe", "cex_bars", "dex_bars", "load_universe"]


def _get(url: str, timeout: int = 30, retries: int = 4) -> dict | list:
    """GET with a back-off, since the free pool API rate-limits hard."""
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(retries):
        try:
            return json.load(urllib.request.urlopen(req, timeout=timeout, context=CTX))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == retries - 1:
                raise
            time.sleep(8 * (attempt + 1))
    raise RuntimeError("unreachable")


def build_universe(min_cex_volume: float = MIN_CEX_VOLUME) -> pd.DataFrame:
    """Tokens quoted both on Gate and in a Solana pool, with the mint verified.

    Arguments:
        min_cex_volume: Skip pairs below this 24h quote volume on the exchange,
            since a venue with almost no prints cannot be ranked.
    """
    tickers = _get("https://api.gateio.ws/api/v4/spot/tickers")
    listed = {
        t["currency_pair"][:-5]: float(t.get("quote_volume") or 0.0)
        for t in tickers
        if t["currency_pair"].endswith("_USDT")
        and t["currency_pair"][:-5].endswith("X")
        and float(t.get("quote_volume") or 0.0) >= min_cex_volume
    }
    rows = []
    for symbol, cex_volume in sorted(listed.items(), key=lambda kv: -kv[1]):
        try:
            found = _get(f"https://api.dexscreener.com/latest/dex/search?q={symbol}")
        except urllib.error.URLError:
            continue
        pools = [
            p for p in (found.get("pairs") or [])
            if p.get("chainId") == "solana"
            and p["baseToken"]["symbol"].upper() == symbol.upper()
            and p["baseToken"]["address"].startswith(MINT_PREFIX)
        ]
        if not pools:
            continue
        pool = max(pools, key=lambda p: float(p.get("liquidity", {}).get("usd") or 0))
        rows.append({
            "symbol": symbol,
            "cex_pair": f"{symbol}_USDT",
            "cex_volume_24h": round(cex_volume),
            "mint": pool["baseToken"]["address"],
            "pool": pool["pairAddress"],
            "dex": pool["dexId"],
            "dex_liquidity": round(float(pool.get("liquidity", {}).get("usd") or 0)),
            "dex_volume_24h": round(float(pool.get("volume", {}).get("h24") or 0)),
        })
        time.sleep(0.4)
    universe = pd.DataFrame(rows)
    DATA.mkdir(parents=True, exist_ok=True)
    universe.to_csv(DATA / "universe.csv", index=False)
    return universe


def load_universe() -> pd.DataFrame:
    return pd.read_csv(DATA / "universe.csv")


def cex_bars(pair: str, limit: int = 1000) -> pd.Series:
    """Gate 1m closes, indexed by epoch second."""
    rows = _get(
        "https://api.gateio.ws/api/v4/spot/candlesticks"
        f"?currency_pair={pair}&interval=1m&limit={limit}"
    )
    return pd.Series({int(r[0]): float(r[5]) for r in rows}).sort_index()


def dex_bars(pool: str, limit: int = 1000, before: int | None = None) -> pd.Series:
    """GeckoTerminal 1m closes for a Solana pool, indexed by epoch second."""
    url = (f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}"
           f"/ohlcv/minute?aggregate=1&limit={limit}")
    if before is not None:
        url += f"&before_timestamp={before}"
    payload = _get(url)
    bars = payload["data"]["attributes"]["ohlcv_list"]
    return pd.Series({int(r[0]): float(r[4]) for r in bars}).sort_index()


def dex_history(pool: str, pages: int = 4) -> pd.Series:
    """Walk GeckoTerminal backwards to cover more than one page of minutes."""
    out: dict[int, float] = {}
    before = None
    for _ in range(pages):
        chunk = dex_bars(pool, before=before)
        if chunk.empty:
            break
        out.update(chunk.to_dict())
        before = int(chunk.index.min()) - 60
        time.sleep(3.0)
    return pd.Series(out).sort_index()
