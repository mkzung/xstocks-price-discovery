"""Measure what the estimator does to an answer it already knows.

The post states two limits of the fit, an upward bias and a scatter when the two
venues correct at similar speeds. Both were quoted from a calibration run that
lived only in a terminal, so nothing could check them and nothing would notice
if they drifted. This writes that run to `data/calibration.csv`, and
`verify.py` reads the post's numbers back out of it.

The truth is fixed by construction: a venue that never corrects carries all of
the permanent price move, so the weight on venue A is adjust_b / (adjust_a +
adjust_b) whatever the estimator later reports.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
# Run as `python analysis/calibrate.py` from the repository root, which is what
# CI and the README both do. That puts analysis/ on the path, not the root, so
# the package import below needs the root added first.
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.discovery import information_share, simulate_leader_follower  # noqa: E402

DATA = BASE / "data"

# Speed pairs spanning a clear leader, a mild leader, and an even split.
GRID = [(0.0, 0.4), (0.05, 0.4), (0.1, 0.4), (0.2, 0.4),
        (0.4, 0.1), (0.4, 0.05), (0.25, 0.25), (0.3, 0.3)]
SEEDS = range(12)

__all__ = ["run"]


def run() -> pd.DataFrame:
    rows = []
    for adjust_a, adjust_b in GRID:
        truth = adjust_b / (adjust_a + adjust_b)
        for seed in SEEDS:
            a, b = simulate_leader_follower(adjust_a=adjust_a, adjust_b=adjust_b,
                                            seed=seed)
            fit = information_share(a, b)
            rows.append({"adjust_a": adjust_a, "adjust_b": adjust_b,
                         "truth": truth, "seed": seed,
                         "weight_a": fit.weight_a,
                         "error": fit.weight_a - truth,
                         "even": abs(adjust_a - adjust_b) < 1e-9})
    frame = pd.DataFrame(rows)
    # Written at ten decimals rather than at full float64 repr. These three files
    # are the only pipeline outputs that stored raw doubles, and a fresh run on
    # Linux reproduced them to about 1e-13 rather than exactly: BLAS differs
    # between platforms, so the last digits of a repr are machine detail, not
    # results. That was enough to redden the workflow's "regenerated artefacts
    # match the committed ones" step on any machine but the one that wrote them.
    # Ten decimals is far past anything read downstream, where the coarsest use is
    # a share of runs whose weight clears an even split.
    frame.round(10).to_csv(DATA / "calibration.csv", index=False)
    return frame


if __name__ == "__main__":
    f = run()
    lead = f[~f.even]
    even = f[f.even]
    print(f"wrote data/calibration.csv, {len(f)} runs over {len(GRID)} speed pairs")
    print(f"  bias where one venue leads: {lead.error.min():+.2f} to {lead.error.max():+.2f}")
    print(f"  weights where both correct equally: {even.weight_a.min():.2f} to "
          f"{even.weight_a.max():.2f} around a true {even.truth.iloc[0]:.1f}")
    print(f"  ranking recovered in {(lead.weight_a > 0.5) .eq(lead.truth > 0.5).mean():.0%} of runs")
