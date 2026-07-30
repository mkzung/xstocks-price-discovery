"""Is the cointegrating vector really (1, -1), or was that convenient?

The error-correction model imposes the vector rather than estimating it: two
venues quoting one mint should move one for one, so the spread of log prices is
taken as the error and the coefficient is never fitted. That is an assumption
with teeth. If a pool sits at a systematic proportional discount that widens
with the price, or if one venue's quote is scaled, the true relation is
log(cex) = a + b log(dex) with b away from one, the imposed spread is not
stationary, and the speeds read off it mean something else.

Imposing the vector is the right choice when it holds, because estimating it
costs precision and puts the Engle-Granger critical values in play instead of
the plain Dickey-Fuller ones. So the test is not whether the fitted b is exactly
one, but whether it is close enough that imposing one changes no conclusion:
does the fitted b sit near one, and does the leader change when the spread is
built from the fitted b instead.

A constant offset needs no test. The error-correction regression already carries
an intercept, so a pool trading at a flat premium is absorbed rather than
mistaken for drift.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.cointegration import adf  # noqa: E402
from analysis.discovery import DiscoveryResult, _ols  # noqa: E402

__all__ = ["VectorResult", "estimate_vector", "fit_with_vector"]


@dataclass(frozen=True)
class VectorResult:
    """The fitted cointegrating coefficient and what it does to the answer."""

    beta: float
    beta_se: float
    bracket_low: float
    bracket_high: float
    adf_imposed: float
    adf_fitted: float
    weight_imposed: float
    weight_fitted: float

    def beta_is_near_one(self, tolerance: float = 0.05) -> bool:
        """True where imposing one is within tolerance of the fitted value."""
        return abs(self.beta - 1.0) <= tolerance

    def one_is_bracketed(self) -> bool:
        """True where one lies between the two one-sided regressions.

        The looser and more honest test. A fitted slope below one is what noise
        in the regressor produces whatever the truth is, so the question is
        whether one survives inside the bracket the two regressions define.
        """
        return self.bracket_low <= 1.0 <= self.bracket_high

    def same_leader(self) -> bool:
        """True where imposing the vector and fitting it name the same leader."""
        return (self.weight_imposed > 0.5) == (self.weight_fitted > 0.5)

    def __repr__(self) -> str:
        return (f"VectorResult(beta={self.beta:.4f}, "
                f"weight {self.weight_imposed:.2f} imposed vs "
                f"{self.weight_fitted:.2f} fitted)")


def estimate_vector(
    price_a: pd.Series, price_b: pd.Series
) -> tuple[float, float, float]:
    """Regress one log price on the other for the cointegrating coefficient.

    Returns the slope, its standard error, and the intercept. The intercept
    matters: the residual whose stationarity is worth testing is
    log(a) - const - beta log(b), and testing log(a) - beta log(b) instead
    leaves a large non-zero mean in a series the no-constant Dickey-Fuller
    regression then has almost no power against. That mistake made the fitted
    residuals look like random walks when they are not.
    """
    frame = pd.concat([np.log(price_a.rename("a")), np.log(price_b.rename("b"))],
                      axis=1).dropna()
    x = np.column_stack([np.ones(len(frame)), frame["b"].to_numpy()])
    y = frame["a"].to_numpy()
    coef = _ols(x, y)
    resid = y - x @ coef
    dof = max(len(frame) - 2, 1)
    sigma2 = float(resid @ resid) / dof
    se = float(np.sqrt(sigma2 * np.linalg.pinv(x.T @ x)[1, 1]))
    return float(coef[1]), se, float(coef[0])


def attenuation_bounds(
    price_a: pd.Series, price_b: pd.Series
) -> tuple[float, float]:
    """Bracket the true slope between the two one-sided regressions.

    A pool's quote carries noise, and noise in a regressor pulls its slope
    toward zero. So regressing the exchange on the pool understates the slope,
    and regressing the pool on the exchange understates the reciprocal, which
    overstates it. The truth lies between the forward slope and the inverse of
    the reverse slope. If one lies inside that bracket, the data is consistent
    with the venues moving one for one and a fitted slope below one is the noise
    rather than a real scaling.
    """
    forward, _, _ = estimate_vector(price_a, price_b)
    reverse, _, _ = estimate_vector(price_b, price_a)
    upper = 1.0 / reverse if abs(reverse) > 1e-12 else float("inf")
    return (min(forward, upper), max(forward, upper))


def fit_with_vector(
    price_a: pd.Series, price_b: pd.Series, *, beta: float, lags: int = 5
) -> DiscoveryResult:
    """Refit the error-correction model with an arbitrary cointegrating vector.

    Identical to `information_share` except the error term is
    log(a) - beta * log(b) rather than the difference.
    """
    frame = pd.concat([np.log(price_a.rename("a")), np.log(price_b.rename("b"))],
                      axis=1).dropna()
    if len(frame) < lags * 4 + 20:
        msg = f"need at least {lags * 4 + 20} paired observations, got {len(frame)}"
        raise ValueError(msg)
    error = (frame["a"] - beta * frame["b"]).shift(1)
    d = frame.diff()
    design = pd.concat(
        [error]
        + [d["a"].shift(i).rename(f"da{i}") for i in range(1, lags + 1)]
        + [d["b"].shift(i).rename(f"db{i}") for i in range(1, lags + 1)],
        axis=1,
    )
    design.insert(0, "const", 1.0)
    fitted = pd.concat([d[["a", "b"]], design], axis=1).dropna()
    x = fitted.drop(columns=["a", "b"]).to_numpy()
    speed_a = float(_ols(x, fitted["a"].to_numpy())[1])
    speed_b = float(_ols(x, fitted["b"].to_numpy())[1])
    denom = speed_a - speed_b
    if abs(denom) < 1e-12:
        weight_a = weight_b = float("nan")
    else:
        weight_a, weight_b = -speed_b / denom, speed_a / denom
    return DiscoveryResult(weight_a, weight_b, speed_a, speed_b, len(fitted))


def check(price_a: pd.Series, price_b: pd.Series) -> VectorResult:
    """Compare the imposed vector against the fitted one, end to end."""
    beta, se, const = estimate_vector(price_a, price_b)
    low, high = attenuation_bounds(price_a, price_b)
    log_a, log_b = np.log(price_a), np.log(price_b)
    imposed = fit_with_vector(price_a, price_b, beta=1.0)
    fitted = fit_with_vector(price_a, price_b, beta=beta)
    # Both residuals are demeaned so the no-constant Dickey-Fuller regression
    # tests reversion to zero, which is the hypothesis of interest, rather than
    # reversion to some level it cannot see.
    imposed_error = (log_a - log_b).dropna()
    fitted_error = (log_a - const - beta * log_b).dropna()
    return VectorResult(
        beta=beta, beta_se=se,
        bracket_low=low, bracket_high=high,
        adf_imposed=adf(imposed_error - imposed_error.mean()).statistic,
        adf_fitted=adf(fitted_error - fitted_error.mean()).statistic,
        weight_imposed=imposed.weight_a,
        weight_fitted=fitted.weight_a,
    )


def run(label: str) -> pd.DataFrame:
    raw = BASE / "raw" / label
    ranked = pd.read_csv(BASE / "data" / f"robustness_{label}.csv")
    ranked = ranked[ranked.verdict == "ranked"].symbol.tolist()
    rows = []
    for symbol in ranked:
        paired = pd.read_csv(raw / f"{symbol}.csv", index_col="ts")
        result = check(paired.cex, paired.dex)
        rows.append({
            "symbol": symbol,
            "beta": round(result.beta, 4),
            "beta_se": round(result.beta_se, 4),
            "bracket_low": round(result.bracket_low, 4),
            "bracket_high": round(result.bracket_high, 4),
            "one_bracketed": result.one_is_bracketed(),
            "beta_near_one": result.beta_is_near_one(),
            "adf_imposed": round(result.adf_imposed, 2),
            "adf_fitted": round(result.adf_fitted, 2),
            "w_imposed": round(result.weight_imposed, 3),
            "w_fitted": round(result.weight_fitted, 3),
            "same_leader": result.same_leader(),
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(BASE / "data" / f"vector_{label}.csv", index=False)
    return frame


if __name__ == "__main__":
    f = run(sys.argv[1] if len(sys.argv) > 1 else "2026-07-29b")
    print("Imposing the vector against fitting it.\n")
    print(f.to_string(index=False))
    print(f"\n  beta within 0.05 of one: {int(f.beta_near_one.sum())} of {len(f)}")
    print(f"  beta range: {f.beta.min():.4f} to {f.beta.max():.4f}")
    print(f"  one inside the attenuation bracket: "
          f"{int(f.one_bracketed.sum())} of {len(f)}")
    print(f"  same leader either way: {int(f.same_leader.sum())} of {len(f)}")
    print(f"  largest weight change: {(f.w_fitted - f.w_imposed).abs().max():.3f}")
