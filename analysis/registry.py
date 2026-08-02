"""Check every kept mint against a registry outside this study.

The universe screen keeps a pool when its base token carries the issuer's
vanity prefix. A prefix is cheap to grind, so the screen alone cannot say a
mint is the issuer's, and review raised exactly that. Backed publishes no
machine-readable token list, so the check runs against Jupiter's verified tag,
which is a curated Solana registry maintained independently of this work and of
the issuer.

A mint passes when the registry carries it, its symbol matches, and the
registry's own name for it says xStock. That is corroboration by a third party,
not proof of issuance; the article says so.
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
REGISTRY = "https://lite-api.jup.ag/tokens/v2/tag?query=verified"
CTX = ssl.create_default_context(cafile=certifi.where())

__all__ = ["verify_mints"]


def verify_mints() -> pd.DataFrame:
    """One row per universe token: does an outside registry corroborate it."""
    req = urllib.request.Request(REGISTRY, headers=UA)
    payload = json.load(urllib.request.urlopen(req, timeout=60, context=CTX))
    tokens = payload if isinstance(payload, list) else payload.get("tokens", [])
    by_mint = {t.get("id") or t.get("address"): t for t in tokens}

    rows = []
    for token in pd.read_csv(DATA / "universe.csv").itertuples():
        entry = by_mint.get(token.mint)
        name = str((entry or {}).get("name", ""))
        symbol = str((entry or {}).get("symbol", ""))
        rows.append({
            "symbol": token.symbol,
            "mint": token.mint,
            "in_registry": entry is not None,
            "registry_symbol": symbol,
            "registry_name": name,
            "symbol_matches": symbol.upper() == token.symbol.upper(),
            "named_xstock": "xstock" in name.lower(),
        })
    frame = pd.DataFrame(rows)
    frame["corroborated"] = (frame.in_registry & frame.symbol_matches
                             & frame.named_xstock)
    frame.to_csv(DATA / "registry_check.csv", index=False)
    return frame


if __name__ == "__main__":
    f = verify_mints()
    print(f"corroborated by the registry: {int(f.corroborated.sum())} of {len(f)}")
    bad = f[~f.corroborated]
    if len(bad):
        print(bad[["symbol", "mint", "in_registry", "registry_name"]]
              .to_string(index=False))
