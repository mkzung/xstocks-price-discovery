"""Which venue moves first: Gonzalo-Granger common-factor weights for a token pair.

Two venues quoting the same asset share one efficient price. Both quotes track
it, so their log prices are cointegrated with the spread as the stationary
error. Each venue's weight in the common factor is the share of the permanent
price move it contributes; a venue that only follows carries a weight near
zero however much volume it prints.

The estimator is the Gonzalo-Granger (1995) decomposition read off a two-venue
vector error-correction model: with error-correction speeds a1 (venue 1) and a2
(venue 2), the common-factor weights are

    w1 = -a2 / (a1 - a2),    w2 = a1 / (a1 - a2)

so the venue that adjusts less to the spread carries more of the permanent
component. `simulate_leader_follower` gives the estimator a known answer to
recover, which is what the test suite checks.

Calibration against that known answer: the single-equation fit used here
carries a small upward bias in both error-correction speeds, because a venue's
own transitory shock sits in the residual and in the lagged spread at once. On
the synthetic runs the weight comes out 0.02 to 0.12 above the truth, and the
error shrinks as the venue-specific shock grows relative to the common
innovation, which is the better-identified case. The ordering is recovered in
every configuration tested, so the weights are read as a ranking with a stated
tolerance rather than as point estimates.

The ratio is unstable when the two venues correct at similar speeds, because
the denominator is their difference: on synthetic runs where both correct
equally the weight scatters between 0.19 and 0.60 across seeds around a truth
of 0.5. A near-even reading therefore means the venues share discovery, not
that one of them leads by the amount shown. The finding a post can carry is a
venue whose weight is far from even and stays there across days.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = ["DiscoveryResult", "information_share", "simulate_leader_follower"]


@dataclass(frozen=True)
class DiscoveryResult:
    """Common-factor weights and the fitted error-correction speeds."""

    weight_a: float
    weight_b: float
    speed_a: float
    speed_b: float
    n_obs: int

    def __repr__(self) -> str:
        return (f"DiscoveryResult(weight_a={self.weight_a:.3f}, "
                f"weight_b={self.weight_b:.3f}, n={self.n_obs})")


def _ols(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(x, y, rcond=None)[0]


def information_share(
    price_a: pd.Series, price_b: pd.Series, *, lags: int = 5
) -> DiscoveryResult:
    """Common-factor weights of two venues quoting the same asset.

    Arguments:
        price_a: Venue A prices, indexed by time.
        price_b: Venue B prices on the same index.
        lags: Lagged returns included on each side of the VECM.

    Returns:
        The weights, which sum to one, and the error-correction speeds.
    """
    df = pd.concat([np.log(price_a.rename("a")), np.log(price_b.rename("b"))],
                   axis=1).dropna()
    if len(df) < lags * 4 + 20:
        msg = f"need at least {lags * 4 + 20} paired observations, got {len(df)}"
        raise ValueError(msg)

    # The spread is the error-correction term: with both venues quoting one
    # asset the cointegrating vector is (1, -1) by construction, so it does not
    # have to be estimated.
    spread = (df["a"] - df["b"]).shift(1)
    d = df.diff()
    design = pd.concat(
        [spread]
        + [d["a"].shift(i).rename(f"da{i}") for i in range(1, lags + 1)]
        + [d["b"].shift(i).rename(f"db{i}") for i in range(1, lags + 1)],
        axis=1,
    )
    design.insert(0, "const", 1.0)
    frame = pd.concat([d[["a", "b"]], design], axis=1).dropna()
    x = frame.drop(columns=["a", "b"]).to_numpy()
    speed_a = float(_ols(x, frame["a"].to_numpy())[1])
    speed_b = float(_ols(x, frame["b"].to_numpy())[1])

    denom = speed_a - speed_b
    if abs(denom) < 1e-12:
        weight_a = weight_b = float("nan")
    else:
        weight_a = -speed_b / denom
        weight_b = speed_a / denom
    return DiscoveryResult(weight_a, weight_b, speed_a, speed_b, len(frame))


def simulate_leader_follower(
    n: int = 4000,
    *,
    adjust_a: float = 0.0,
    adjust_b: float = 0.4,
    venue_shock: float = 0.0005,
    noise: float = 0.0,
    seed: int = 0,
) -> tuple[pd.Series, pd.Series]:
    """Two venues on one efficient price, each correcting toward the other.

    Venue A closes `adjust_a` of the gap to B each step and B closes
    `adjust_b` of the gap to A, so the venue that corrects less carries more of
    the permanent component. The construction gives the estimator a right
    answer to recover: the common-factor weight of A is

        adjust_b / (adjust_a + adjust_b)

    which is 1 when A never corrects, and 0.5 when both correct equally.
    `venue_shock` is the venue-specific transitory shock that opens the spread
    the two then close; without it the quotes are identical and there is
    nothing to error-correct. `noise` adds observation error on top, which
    attenuates the measured weights toward 0.5 the way real quote noise does.
    """
    if adjust_a + adjust_b <= 0:
        msg = "at least one venue has to correct toward the other"
        raise ValueError(msg)
    rng = np.random.default_rng(seed)
    innov = rng.normal(0, 0.002, n)
    shock_a = rng.normal(0, venue_shock, n)
    shock_b = rng.normal(0, venue_shock, n)
    a = np.empty(n)
    b = np.empty(n)
    a[0] = b[0] = 0.0
    for t in range(1, n):
        a[t] = (a[t - 1] + innov[t] + shock_a[t]
                + adjust_a * (b[t - 1] - a[t - 1]))
        b[t] = (b[t - 1] + innov[t] + shock_b[t]
                + adjust_b * (a[t - 1] - b[t - 1]))
    a = a + rng.normal(0, noise, n)
    b = b + rng.normal(0, noise, n)
    idx = pd.date_range("2026-01-01", periods=n, freq="min")
    return (pd.Series(np.exp(a), index=idx, name="a"),
            pd.Series(np.exp(b), index=idx, name="b"))
