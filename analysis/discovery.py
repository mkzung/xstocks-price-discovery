"""Which venue moves first: Gonzalo-Granger common-factor weights for a token pair.

Two venues quoting the same asset should share one efficient price, in which
case their log prices are cointegrated and the spread between them is the
stationary error. Each venue's weight in the common factor is then the share of
the permanent price move it contributes, and a venue that only follows carries a
weight near zero however much volume it prints.

Both of those are conditions rather than definitions. `analysis/cointegration.py`
tests the first per pair, and `analysis/vector.py` tests whether imposing the
one-for-one error term below changes any conclusion.

The estimator is the Gonzalo-Granger (1995) decomposition read off a two-venue
vector error-correction model: with error-correction speeds a1 (venue 1) and a2
(venue 2), the common-factor weights are

    w1 = -a2 / (a1 - a2),    w2 = a1 / (a1 - a2)

so the venue that adjusts less to the spread carries more of the permanent
component. `simulate_leader_follower` gives the estimator a known answer to
recover, which is what the test suite checks.

Calibration against that known answer lives in `analysis/calibrate.py` and its
committed output `data/calibration.csv`, ninety-six runs over eight speed pairs.
Three properties came out of it and all three constrain how a weight may be
read.

The bias is upward and small in the mean: the fit lands 0.03 above the truth,
consistently across speed pairs, because a venue's own transitory shock sits in
the residual and in the lagged spread at once.

The scatter is not small. A single run lands between 0.33 below the truth and
0.28 above it, and that range holds across the whole grid rather than only where
the two venues correct at similar speeds. One weight from one sample is weak
evidence whatever it reads.

The ordering survives that scatter. Where the true weight is plainly one-sided
the estimator picks the right leader in 98 percent of the 60 runs, and in 11 of
the 12 at the one grid point near an even split. The second is a count rather
than a rate because twelve runs at one point of the grid do not support a
percentage, and runs whose truth is an even split are excluded from both, having
no leader to recover. So weights are read as a ranking, near-even readings mean
shared discovery rather than a measured lead, and the load is carried by the two
correction speeds, which are ordinary coefficients, rather than by the ratio
built from them.

`hasbrouck_share` is the second decomposition, and it is not a restatement of
the first. Gonzalo-Granger splits the permanent price level; Hasbrouck splits
the variance of the efficient price innovation. With uncorrelated innovations
and equal venue variances the second reduces to w^2 / (w^2 + (1-w)^2), so a
Gonzalo-Granger weight of 0.8 corresponds to a Hasbrouck share near 0.94. The
two agree on direction, never on magnitude, and only direction should be
compared.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = ["DiscoveryResult", "HasbrouckResult", "fit_design", "hasbrouck_share",
           "information_share", "ols", "simulate_leader_follower", "vecm_design"]


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


@dataclass(frozen=True)
class HasbrouckResult:
    """Hasbrouck information shares for venue A, as bounds.

    Hasbrouck (1995) splits the variance of the efficient price innovation
    between the two venues. Where the two venues' innovations are correlated
    the split is not identified, so the method reports the range spanned by the
    two Cholesky orderings rather than one number. A wide range means the
    minute is too coarse to separate the venues; a narrow one means the answer
    does not depend on the ordering.
    """

    lower: float
    upper: float
    correlation: float
    n_obs: int

    @property
    def midpoint(self) -> float:
        return (self.lower + self.upper) / 2

    def __repr__(self) -> str:
        return (f"HasbrouckResult(lower={self.lower:.3f}, "
                f"upper={self.upper:.3f}, rho={self.correlation:.3f})")


def ols(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Least squares, shared with the modules that build their own designs."""
    return np.linalg.lstsq(x, y, rcond=None)[0]


def vecm_design(
    price_a: pd.Series, price_b: pd.Series, *, lags: int = 5
) -> pd.DataFrame:
    """The regression the model is fitted on: both differences and the design.

    Exposed because resampling has to happen here rather than on the price
    levels. Splicing blocks of two cointegrated levels together puts a
    discontinuity in the spread at every block boundary, and those artificial
    jumps swamp the error-correction term; a bootstrap built that way recovers
    nothing. Resampling rows of this frame leaves the spread column exactly as
    the original prices produced it.

    One step here is one row to the next, not one minute to the next. The
    caller passes a series of minutes both venues traded in, and the minutes
    neither of them did are absent rather than filled, so on a sparse pool the
    rows are further apart than the bar they came from. That makes every
    coefficient below a rate per observation. It does not touch which venue
    leads, since both equations are fitted to the same rows. It does mean a
    speed is not a rate per clock minute. Refit the same pair on five-minute
    bars and the coefficients grow, which is the step and not the venue.
    """
    df = pd.concat([np.log(price_a.rename("a")), np.log(price_b.rename("b"))],
                   axis=1).dropna()
    if len(df) < lags * 4 + 20:
        msg = f"need at least {lags * 4 + 20} paired observations, got {len(df)}"
        raise ValueError(msg)

    # The spread is the error-correction term. That imposes a cointegrating
    # vector of (1, -1) rather than fitting one, which buys precision when it
    # holds; analysis/vector.py fits it instead and reports what changes.
    spread = (df["a"] - df["b"]).shift(1)
    d = df.diff()
    design = pd.concat(
        [spread]
        + [d["a"].shift(i).rename(f"da{i}") for i in range(1, lags + 1)]
        + [d["b"].shift(i).rename(f"db{i}") for i in range(1, lags + 1)],
        axis=1,
    )
    design.insert(0, "const", 1.0)
    return pd.concat([d[["a", "b"]], design], axis=1).dropna()


def fit_design(
    frame: pd.DataFrame, *, _with_residuals: bool = False
) -> DiscoveryResult | tuple[DiscoveryResult, np.ndarray]:
    """Fit the two error-correction equations on an already-built design."""
    x = frame.drop(columns=["a", "b"]).to_numpy()
    coef_a = ols(x, frame["a"].to_numpy())
    coef_b = ols(x, frame["b"].to_numpy())
    speed_a, speed_b = float(coef_a[1]), float(coef_b[1])

    denom = speed_a - speed_b
    if abs(denom) < 1e-12:
        weight_a = weight_b = float("nan")
    else:
        weight_a = -speed_b / denom
        weight_b = speed_a / denom
    result = DiscoveryResult(weight_a, weight_b, speed_a, speed_b, len(frame))
    if not _with_residuals:
        return result
    resid = np.column_stack([frame["a"].to_numpy() - x @ coef_a,
                             frame["b"].to_numpy() - x @ coef_b])
    return result, resid


def information_share(
    price_a: pd.Series, price_b: pd.Series, *, lags: int = 5,
    _with_residuals: bool = False,
) -> DiscoveryResult | tuple[DiscoveryResult, np.ndarray]:
    """Common-factor weights of two venues quoting the same asset.

    Arguments:
        price_a: Venue A prices, indexed by time.
        price_b: Venue B prices on the same index.
        lags: Lagged returns included on each side of the VECM.
        _with_residuals: Also return the two equations' residuals, which
            `hasbrouck_share` needs and no caller outside this module does.

    Returns:
        The weights, which sum to one, and the error-correction speeds.
    """
    frame = vecm_design(price_a, price_b, lags=lags)
    return fit_design(frame, _with_residuals=_with_residuals)


def hasbrouck_share(
    price_a: pd.Series, price_b: pd.Series, *, lags: int = 5
) -> HasbrouckResult:
    """Hasbrouck (1995) information share of venue A, as a lower and upper bound.

    Gonzalo-Granger reads leadership off the error-correction speeds alone and
    ignores how correlated the two venues' innovations are. Hasbrouck splits the
    variance of the efficient price innovation instead, which uses that
    correlation, and the two can disagree. Reporting both is the check: where
    they agree the conclusion does not depend on which decomposition is
    preferred, and where they diverge the data cannot settle the question.

    The share is not identified when the innovations are correlated, so the two
    Cholesky orderings give a range and both ends are returned.

    Arguments:
        price_a: Venue A prices, indexed by time.
        price_b: Venue B prices on the same index.
        lags: Lagged returns included on each side of the VECM.

    Returns:
        The bounds on venue A's share, and the residual correlation that sets
        how wide those bounds are.
    """
    gg, resid = information_share(price_a, price_b, lags=lags,
                                  _with_residuals=True)
    omega = np.cov(resid, rowvar=False)
    sd = np.sqrt(np.diag(omega))
    if not np.all(np.isfinite(sd)) or np.any(sd <= 0):
        return HasbrouckResult(float("nan"), float("nan"), float("nan"),
                               gg.n_obs)
    rho = float(omega[0, 1] / (sd[0] * sd[1]))
    rho = float(np.clip(rho, -0.999999, 0.999999))

    # The row of the moving-average impact matrix is common to both variables
    # and equals the Gonzalo-Granger weights, so the two methods share a
    # numerator and differ only in how the innovation covariance enters.
    psi = np.array([gg.weight_a, gg.weight_b])
    total = float(psi @ omega @ psi)
    if not np.isfinite(total) or total <= 0:
        return HasbrouckResult(float("nan"), float("nan"), rho, gg.n_obs)

    shares = []
    for first in (0, 1):
        order = [first, 1 - first]
        chol = np.linalg.cholesky(omega[np.ix_(order, order)])
        # Venue A sits at position 0 or 1 depending on the ordering.
        pos = order.index(0)
        contribution = float((psi[order] @ chol)[pos])
        shares.append(contribution ** 2 / total)
    return HasbrouckResult(min(shares), max(shares), rho, gg.n_obs)


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
