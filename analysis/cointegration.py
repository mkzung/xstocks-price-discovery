"""Test the assumption the whole error-correction model rests on.

The study asserts that two venues quoting one mint are cointegrated with the
spread as the stationary error, and calls that true by construction. It is not
true by construction. It is true if arbitrage actually binds, and arbitrage can
fail to bind: a pool with two hundred dollars of liquidity cannot be arbitraged
against an exchange in any size, and its price is free to wander. Where the
spread is not stationary the error-correction model is misspecified and its
speeds mean nothing, so this has to be tested per pair rather than assumed
across the board.

The test is the augmented Dickey-Fuller regression on the spread, with no
constant and no trend, since the cointegrating vector is (1, -1) and imposed
rather than estimated. Because it is imposed, the critical values are the
standard Dickey-Fuller ones rather than the Engle-Granger ones that apply when
the vector is fitted.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

__all__ = ["AdfResult", "adf", "critical_values"]

# Dickey-Fuller critical values for the no-constant, no-trend case, from the
# response surface in MacKinnon (2010) table 1 evaluated at the large-sample
# limit. Sample sizes here are in the hundreds, where the asymptotic values are
# close enough that the conclusions do not turn on the correction.
CRITICAL = {0.01: -2.567, 0.05: -1.941, 0.10: -1.617}


def critical_values() -> dict[float, float]:
    """The thresholds a statistic has to fall below to reject a unit root."""
    return dict(CRITICAL)


@dataclass(frozen=True)
class AdfResult:
    """An augmented Dickey-Fuller statistic and what it implies."""

    statistic: float
    lags: int
    n_obs: int
    half_life_min: float

    def rejects_unit_root(self, level: float = 0.05) -> bool:
        """True where the spread looks stationary at the given level."""
        return self.statistic < CRITICAL[level]

    def __repr__(self) -> str:
        return (f"AdfResult(statistic={self.statistic:.2f}, "
                f"n={self.n_obs}, half_life={self.half_life_min:.1f}min)")


def adf(series: pd.Series, *, lags: int = 5) -> AdfResult:
    """Augmented Dickey-Fuller on a series, no constant and no trend.

    Arguments:
        series: The spread to test, already in logs.
        lags: Lagged differences included to soak up serial correlation.

    Returns:
        The statistic, and the half-life implied by the fitted decay, which is
        the more readable form: how many minutes it takes a gap to halve.
    """
    y = series.dropna()
    if len(y) < lags + 20:
        msg = f"need at least {lags + 20} observations, got {len(y)}"
        raise ValueError(msg)
    dy = y.diff()
    cols = [y.shift(1).rename("level")]
    cols += [dy.shift(i).rename(f"d{i}") for i in range(1, lags + 1)]
    frame = pd.concat([dy.rename("dy"), *cols], axis=1).dropna()
    x = frame.drop(columns=["dy"]).to_numpy()
    target = frame["dy"].to_numpy()

    coef, *_ = np.linalg.lstsq(x, target, rcond=None)
    resid = target - x @ coef
    dof = len(frame) - x.shape[1]
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(x.T @ x)
    se = float(np.sqrt(sigma2 * xtx_inv[0, 0]))
    gamma = float(coef[0])
    statistic = gamma / se if se > 0 else float("nan")

    # dy = gamma * y[t-1] means the level decays by (1 + gamma) each minute.
    decay = 1.0 + gamma
    half_life = (np.log(0.5) / np.log(decay)
                 if 0 < decay < 1 else float("inf"))
    return AdfResult(statistic, lags, len(frame), float(half_life))
