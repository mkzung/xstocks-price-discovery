"""Separating what a token's own data says from what the method contributes.

The calibration bounds the estimator's scatter on synthetic runs, which answers
a question about the method rather than about any particular token. A token
with eighty paired minutes and a token with five hundred deserve different
amounts of belief, and the calibration cannot say which is which.

A moving-block bootstrap does. Resampling contiguous blocks of the paired
series preserves the serial correlation the error-correction model lives on,
which an observation-by-observation resample would destroy, and refitting on
each resample gives the weight a distribution drawn from that token's own data.

The interval is percentile rather than bias-corrected. The bias is known and
stated separately, and folding a correction into the interval would hide it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.discovery import fit_design, vecm_design  # noqa: E402

__all__ = ["Interval", "block_bootstrap", "sign_test"]


@dataclass(frozen=True)
class Interval:
    """What a token's own data can and cannot pin down.

    The weight interval is reported and is close to useless, on purpose. The
    weight is a ratio whose denominator is the difference between two similar
    error-correction speeds, so a resample that nudges those speeds together
    sends it off to infinity; the interval is wide however long the sample and
    does not narrow with more data. Reporting it and saying so is better than
    quietly not computing it.

    What the same resamples do pin down is the pair of speeds, which are
    ordinary regression coefficients, and the ordering they imply. `lead_share`
    is the direct statement: in what fraction of resamples did the exchange
    come out ahead.
    """

    point: float
    low: float
    high: float
    lead_share: float
    speed_a_low: float
    speed_a_high: float
    speed_b_low: float
    speed_b_high: float
    draws: int

    def speeds_are_separated(self) -> bool:
        """True where the two speed intervals do not overlap in magnitude."""
        return abs(self.speed_a_high) < abs(self.speed_b_low)

    def __repr__(self) -> str:
        return (f"Interval(point={self.point:.2f}, "
                f"weight [{self.low:.2f}, {self.high:.2f}], "
                f"lead in {self.lead_share:.0%} of resamples)")


def block_bootstrap(
    price_a: pd.Series,
    price_b: pd.Series,
    *,
    draws: int = 400,
    block: int | None = None,
    level: float = 0.90,
    seed: int = 0,
) -> Interval:
    """Percentile interval for venue A's weight, resampling contiguous blocks.

    Arguments:
        price_a: Venue A prices, indexed by time.
        price_b: Venue B prices on the same index.
        draws: Bootstrap resamples.
        block: Block length. Defaults to the cube root of the sample, the usual
            rule for a series whose dependence dies out quickly.
        level: Coverage of the returned interval.
        seed: Seed for the resampling.

    Returns:
        The point estimate on the full sample, the interval, and the share of
        resamples putting venue A ahead.
    """
    # Blocks are drawn from the fitted regression rows, not the price levels.
    # Resampling levels splices two cointegrated series at block boundaries and
    # injects a jump into the spread at every seam, which drowns the
    # error-correction term: tested that way the bootstrap put a known leader
    # ahead in 65 percent of resamples and a known follower ahead in 45, which
    # is no signal at all.
    design = vecm_design(price_a, price_b)
    n = len(design)
    size = block or max(10, int(round(n ** (1 / 3))))
    if n < size * 4:
        msg = f"need at least {size * 4} fitted rows, got {n}"
        raise ValueError(msg)

    point = fit_design(design).weight_a
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / size))
    starts_pool = np.arange(0, n - size + 1)

    weights, speeds_a, speeds_b = [], [], []
    for _ in range(draws):
        starts = rng.choice(starts_pool, size=n_blocks, replace=True)
        idx = np.concatenate([np.arange(s, s + size) for s in starts])[:n]
        sample = design.iloc[idx].reset_index(drop=True)
        fit = fit_design(sample)
        if np.isfinite(fit.weight_a):
            weights.append(fit.weight_a)
            speeds_a.append(fit.speed_a)
            speeds_b.append(fit.speed_b)

    if not weights:  # pragma: no cover - only if every resample degenerates
        nan = float("nan")
        return Interval(point, nan, nan, nan, nan, nan, nan, nan, 0)
    tail = (1 - level) / 2

    def band(values: list[float]) -> tuple[float, float]:
        arr = np.array(values)
        return float(np.quantile(arr, tail)), float(np.quantile(arr, 1 - tail))

    weight_low, weight_high = band(weights)
    speed_a_low, speed_a_high = band(speeds_a)
    speed_b_low, speed_b_high = band(speeds_b)
    # The venue that corrects less leads, which is the comparison the weight is
    # a noisy restatement of. Reading it off the speeds avoids the ratio.
    lead = float(np.mean(np.abs(speeds_a) < np.abs(speeds_b)))
    return Interval(
        point=float(point),
        low=weight_low, high=weight_high, lead_share=lead,
        speed_a_low=speed_a_low, speed_a_high=speed_a_high,
        speed_b_low=speed_b_low, speed_b_high=speed_b_high,
        draws=len(weights),
    )


def sign_test(led: int, total: int) -> float:
    """Two-sided probability of `led` or more one-way results under coin flips.

    Seven pairs all pointing the same way is the claim the post rests on. Each
    individual weight is noisy, but the joint outcome is not, and this is the
    number that says by how much. Exact binomial, no library.

    Seven, not nine. Nine is the session panel's count and this is the series
    pass's, and the docstring carried the panel's number beside the series
    pass's p-value for as long as nothing read it.
    """
    if total <= 0:
        return float("nan")
    extreme = max(led, total - led)
    tail = sum(_choose(total, k) for k in range(extreme, total + 1))
    return min(1.0, 2 * tail / 2 ** total)


def _choose(n: int, k: int) -> int:
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result
