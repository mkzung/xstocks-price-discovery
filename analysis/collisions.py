"""Record the ticker collisions the universe screen filtered out.

The post says symbol matching alone is unsafe because several of these tickers
collide with unrelated mints, two of them carrying hundreds of millions of
dollars of claimed liquidity. That was true when the universe was first built,
and it was also unverifiable: the screen dropped the impostors and kept no
record, so the sentence rested on a memory of a terminal. A claim about
discarded data needs the discarded data.

This searches each universe symbol on Dexscreener, keeps every Solana pool
whose base token does not carry the issuer's mint prefix, and writes what it
finds with the claimed liquidity attached. The committed CSV is a snapshot of
the day it was run, like every other snapshot here, and `verify.py` reads the
post's collision sentence back out of it.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.collect import CTX, MINT_PREFIX, UA  # noqa: E402

DATA = BASE / "data"

__all__ = ["screen"]


def screen(pause: float = 1.5) -> pd.DataFrame:
    """One row per non-issuer Solana pool answering to a universe ticker."""
    universe = pd.read_csv(DATA / "universe.csv")
    rows = []
    for symbol in universe.symbol:
        url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"
        req = urllib.request.Request(url, headers=UA)
        payload = json.load(urllib.request.urlopen(req, timeout=30, context=CTX))
        for pair in payload.get("pairs") or []:
            if pair.get("chainId") != "solana":
                continue
            token = pair.get("baseToken") or {}
            if token.get("symbol", "").upper() != symbol.upper():
                continue
            mint = token.get("address", "")
            if mint.startswith(MINT_PREFIX):
                continue
            rows.append({
                "symbol": symbol,
                "impostor_mint": mint,
                "dex": pair.get("dexId"),
                "claimed_liquidity_usd": float(
                    (pair.get("liquidity") or {}).get("usd") or 0),
            })
        time.sleep(pause)
    frame = (pd.DataFrame(rows)
             .sort_values("claimed_liquidity_usd", ascending=False)
             .reset_index(drop=True))
    frame.to_csv(DATA / "collisions.csv", index=False)
    return frame


if __name__ == "__main__":
    f = screen()
    print(f"wrote data/collisions.csv, {len(f)} impostor pools across "
          f"{f.symbol.nunique() if len(f) else 0} tickers")
    if len(f):
        big = f[f.claimed_liquidity_usd >= 1e8]
        print(f"  claiming $100M or more: {len(big)} pools, "
              f"{big.symbol.nunique()} distinct tickers")
        print(f.head(8).to_string(index=False))
