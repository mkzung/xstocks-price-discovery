"""How on-chain activity relates to what the exchange prints against it.

The three groups in the post fall out of one measurement rather than three
judgements: rank the tokens by how many minutes their pool traded, rank them by
how many dollars the exchange printed per on-chain dollar, and the two orders
are almost the reverse of each other. This module produces that number and a
permutation test for it, so the grouping in the post is a description of a
measured relation rather than a set of chosen buckets.

Spearman is computed as Pearson on ranks so the package needs no scipy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

__all__ = ["RelationResult", "build_groups", "spearman", "test_relation"]


@dataclass(frozen=True)
class RelationResult:
    rho: float
    p_value: float
    n: int
    draws: int


def spearman(x: pd.Series, y: pd.Series) -> float:
    """Rank correlation, no scipy."""
    return float(np.corrcoef(x.rank(), y.rank())[0, 1])


def test_relation(x: pd.Series, y: pd.Series, *, draws: int = 20_000,
                  seed: int = 0) -> RelationResult:
    """Spearman plus a two-sided permutation test of it."""
    rho = spearman(x, y)
    rng = np.random.default_rng(seed)
    ranks_x, ranks_y = x.rank().to_numpy(), y.rank().to_numpy()
    null = np.empty(draws)
    for i in range(draws):
        null[i] = np.corrcoef(ranks_x, rng.permutation(ranks_y))[0, 1]
    return RelationResult(rho, float((np.abs(null) >= abs(rho)).mean()),
                          len(x), draws)


def build_groups(rankable: set[str], dead_below: int = 10) -> pd.DataFrame:
    """Label every token: ranked, thin, or without an on-chain market.

    Arguments:
        rankable: Symbols the estimator could rank.
        dead_below: A pool that printed in fewer minutes than this over the
            window is treated as having no on-chain market to check against.
    """
    universe = pd.read_csv(DATA / "universe.csv")
    panel = pd.read_csv(DATA / "panel_run1.csv")[["symbol", "paired_min"]]
    merged = universe.merge(panel, on="symbol", how="left")
    merged["ratio"] = merged.cex_volume_24h / merged.dex_volume_24h.clip(lower=1)
    merged["group"] = np.where(
        merged.paired_min < dead_below, "no on-chain market",
        np.where(merged.symbol.isin(rankable), "ranked", "thin"))
    merged = merged.sort_values(
        ["paired_min", "symbol"], ascending=[False, True])
    merged.to_csv(DATA / "token_groups.csv", index=False)
    return merged
