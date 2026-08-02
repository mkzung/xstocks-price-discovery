"""Can sparse trading manufacture the leadership result on its own?

This is the objection that would sink the study if it went unanswered. A pool
does not trade every minute. Between its trades its last price stands still
while the exchange keeps moving, so when the pool finally prints it jumps most
of the way to the current level. Read through an error-correction model that
looks like the pool closing the gap fast and the exchange not closing it at
all, which is exactly the reported finding. The measured leadership could
therefore be a sampling artefact rather than a fact about either venue.

The objection is testable because the simulator has a known answer. Build a
world where the POOL is the true leader, then sample the pool sparsely and hand
the result to the same estimator. If the estimator flips and calls the exchange
the leader, sparseness alone produces the finding and the study's headline
cannot stand as written. If it holds, the artefact is bounded and the size of
the bound is worth stating.

Sparse sampling here means what the data means: a venue that has not traded
carries its last trade price forward, and only minutes where both venues have a
price enter the fit.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.discovery import information_share, simulate_leader_follower  # noqa: E402

DATA = BASE / "data"

__all__ = ["stale_sample", "run"]


def stale_sample(
    price: pd.Series, keep: float, *, seed: int = 0
) -> pd.Series:
    """Keep a random `keep` share of minutes and hold the last price between them.

    This is what a thin pool's minute series looks like: a print, then a flat
    stretch at that print until the next one.
    """
    rng = np.random.default_rng(seed)
    traded = rng.random(len(price)) < keep
    traded[0] = True
    held = price.where(pd.Series(traded, index=price.index)).ffill()
    return held


def drop_sample(
    price: pd.Series, keep: float, *, seed: int = 0
) -> pd.Series:
    """Keep a random `keep` share of minutes and drop the rest entirely.

    This is what the pipeline actually does. The pool series carries only the
    minutes the pool printed, the pair is an inner join, and the estimator then
    treats surviving rows as consecutive whatever the real gap between them.
    The distortion is different from holding a stale price: no price is stale,
    but a one-row lag can span forty minutes of exchange trading.
    """
    rng = np.random.default_rng(seed)
    traded = rng.random(len(price)) < keep
    traded[0] = True
    return price[traded]


def run(*, draws: int = 40) -> pd.DataFrame:
    """Sweep how sparsely the pool trades, with the pool as the true leader.

    Both sampling schemes are run: holding the last price forward, and dropping
    untraded minutes. The second is the one this pipeline performs, so it is
    the one the study has to answer for.
    """
    rows = []
    # The pool leads by construction: it never corrects, the exchange closes
    # 0.4 of the gap each minute. Truth for the pool's weight is 1.0, so a
    # correct estimator must report the exchange's weight near 0.
    for scheme, sampler in (("hold", stale_sample), ("drop", drop_sample)):
        for keep in (1.0, 0.8, 0.6, 0.45, 0.3, 0.2, 0.1, 0.05):
            for seed in range(draws):
                pool, cex = simulate_leader_follower(
                    adjust_a=0.0, adjust_b=0.4, seed=seed)
                sparse = sampler(pool, keep, seed=seed + 5000)
                paired = pd.concat([cex.rename("cex"),
                                    sparse.rename("pool")], axis=1).dropna()
                try:
                    fit = information_share(paired.cex, paired.pool)
                except ValueError:
                    continue
                rows.append({
                    "scheme": scheme, "keep": keep, "seed": seed,
                    "w_cex": fit.weight_a, "speed_cex": fit.speed_a,
                    "speed_pool": fit.speed_b, "minutes": fit.n_obs,
                })
    frame = pd.DataFrame(rows)
    # Written at ten decimals rather than at full float64 repr. These three files
    # are the only pipeline outputs that stored raw doubles, and a fresh run on
    # Linux reproduced them to about 1e-13 rather than exactly: BLAS differs
    # between platforms, so the last digits of a repr are machine detail, not
    # results. That was enough to redden the workflow's "regenerated artefacts
    # match the committed ones" step on any machine but the one that wrote them.
    # Ten decimals is far past anything read downstream, where the coarsest use is
    # a share of runs whose weight clears an even split.
    frame.round(10).to_csv(DATA / "staleness.csv", index=False)
    return frame


def run_matched(*, draws: int = 40) -> pd.DataFrame:
    """The same test at the sample sizes the real pairs actually have.

    The main sweep simulates a 4,000-minute base series, so a 12 percent fill
    still keeps near 500 fitted rows, while a real pair at that fill holds a
    quarter of that. Error rates at one fill but different lengths are not the
    same number, so the sweep is repeated with the base series shortened to
    match the real windows: about 1,000 minutes gives row counts near the
    ranked pairs', and 250 stresses the floor.
    """
    rows = []
    for n in (4000, 1000, 250):
        for keep in (0.5, 0.25, 0.12):
            for seed in range(draws):
                pool, cex = simulate_leader_follower(
                    n=n, adjust_a=0.0, adjust_b=0.4, seed=seed)
                sparse = drop_sample(pool, keep, seed=seed + 7000)
                paired = pd.concat([cex.rename("cex"),
                                    sparse.rename("pool")], axis=1).dropna()
                try:
                    fit = information_share(paired.cex, paired.pool)
                except ValueError:
                    rows.append({"n": n, "keep": keep, "seed": seed,
                                 "w_cex": float("nan"), "rows": len(paired),
                                 "fitted": False})
                    continue
                rows.append({"n": n, "keep": keep, "seed": seed,
                             "w_cex": fit.weight_a, "rows": fit.n_obs,
                             "fitted": True})
    frame = pd.DataFrame(rows)
    # Ten decimals, for the reason given above.
    frame.round(10).to_csv(DATA / "staleness_matched.csv", index=False)
    return frame


if __name__ == "__main__":
    f = run()
    m = run_matched()
    print("Matched-length check: same fills, shorter base series.")
    ok = m[m.fitted]
    for n in (4000, 1000, 250):
        for keep in (0.5, 0.25, 0.12):
            sub = ok[(ok.n == n) & (ok.keep == keep)]
            if len(sub):
                err = float((sub.w_cex > 0.5).mean())
                print(f"  n={n:>5} keep={keep:.2f}: rows~{int(sub.rows.median()):>4} "
                      f"false-lead {err:.0%} ({len(sub)} fits)")
    print()
    print("The pool is the true leader in every run below, so a correct")
    print("estimator reports an exchange weight near 0. Rising numbers mean")
    print("sparse sampling is inventing exchange leadership.\n")
    for scheme, sub in f.groupby("scheme", sort=False):
        label = ("holding the last price forward" if scheme == "hold"
                 else "dropping untraded minutes, which is what the pipeline does")
        print(f"\n{label}")
        print(f"{'pool trades':>12} {'median w_cex':>13} {'share w_cex>0.5':>16} "
              f"{'median speed_cex':>17} {'median speed_pool':>18}")
        for keep, s in sub.groupby("keep", sort=False):
            print(f"{keep:>11.0%} {s.w_cex.median():>13.2f} "
                  f"{(s.w_cex > 0.5).mean():>15.0%} "
                  f"{s.speed_cex.median():>17.2f} {s.speed_pool.median():>18.2f}")
