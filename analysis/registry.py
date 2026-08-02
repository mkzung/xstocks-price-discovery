"""Check every kept mint against the issuer's own published list.

The universe screen keeps a pool when its base token carries the issuer's
vanity prefix. A prefix is cheap to grind, so the screen alone cannot say a
mint is the issuer's, and review raised exactly that.

Backed publishes the list at api.xstocks.fi, one record per asset with its
deployment address on each network it has issued to. That is the primary
source: a mint passes when the issuer's own list carries it as a Solana
deployment under the matching symbol. An earlier version of this file checked
Jupiter's verified registry instead, on the belief that no issuer list existed;
that was wrong, and third-party curation is weaker evidence than the issuer's
own record. Jupiter stays as a second opinion, since two independent lists
agreeing is worth more than either alone.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import certifi  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.collect import UA  # noqa: E402

DATA = BASE / "data"
ISSUER = "https://api.xstocks.fi/api/v2/public/assets"
SECOND_OPINION = "https://lite-api.jup.ag/tokens/v2/tag?query=verified"
CTX = ssl.create_default_context(cafile=certifi.where())

__all__ = ["verify_mints"]


def _get(url: str) -> dict | list:
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60, context=CTX))


def issuer_mints() -> dict[str, str]:
    """Solana mint by symbol, from the issuer's paginated asset list."""
    out: dict[str, str] = {}
    page = 0
    while True:
        payload = _get(f"{ISSUER}?page={page}")
        for asset in payload.get("nodes", []):
            for deployment in asset.get("deployments", []):
                if deployment.get("network", "").lower() == "solana":
                    out[asset["symbol"].upper()] = deployment["address"]
        if not payload.get("page", {}).get("hasNextPage"):
            return out
        page += 1


def verify_mints() -> pd.DataFrame:
    """One row per universe token: does the issuer's list carry this mint."""
    issuer = issuer_mints()
    payload = _get(SECOND_OPINION)
    tokens = payload if isinstance(payload, list) else payload.get("tokens", [])
    jup = {t.get("id") or t.get("address"): t for t in tokens}

    rows = []
    for token in pd.read_csv(DATA / "universe.csv").itertuples():
        published = issuer.get(token.symbol.upper())
        entry = jup.get(token.mint)
        rows.append({
            "symbol": token.symbol,
            "mint": token.mint,
            "issuer_lists_symbol": published is not None,
            "issuer_mint": published or "",
            "issuer_mint_matches": published == token.mint,
            "in_jupiter_verified": entry is not None,
            "jupiter_name": str((entry or {}).get("name", "")),
        })
    frame = pd.DataFrame(rows)
    frame["confirmed"] = frame.issuer_mint_matches
    frame.to_csv(DATA / "registry_check.csv", index=False)
    return frame


if __name__ == "__main__":
    f = verify_mints()
    print(f"confirmed against the issuer's list: {int(f.confirmed.sum())} of {len(f)}")
    print(f"also in Jupiter verified: {int(f.in_jupiter_verified.sum())} of {len(f)}")
    bad = f[~f.confirmed]
    if len(bad):
        print(bad[["symbol", "mint", "issuer_lists_symbol", "issuer_mint"]]
              .to_string(index=False))
