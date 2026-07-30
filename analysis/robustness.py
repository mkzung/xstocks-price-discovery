"""Put every leadership claim through the checks that could overturn it.

The first version of this study reported one estimator on one window and
declared the exchange the leader. Four things could have produced that result
without it being true, and each is answered here against the raw paired series
rather than against the fitted panel.

Is the model even applicable. The error-correction framework assumes the two
log prices are cointegrated. That is asserted rather than tested in the
original, so the spread of each pair gets an augmented Dickey-Fuller test and a
pair whose spread wanders is reported as such rather than quietly fitted.

Does the second standard estimator agree. Gonzalo-Granger reads leadership off
the correction speeds alone. Hasbrouck splits the innovation variance instead
and can disagree. Where the two agree the finding does not depend on the choice.

Can the token's own data support the claim. A block bootstrap over the fitted
regression rows says in what share of resamples the exchange still comes out
ahead, which is a statement about this token rather than about the method.

Is it an artefact of how sparsely the pool trades. `staleness.py` answers that
on synthetic data with a known answer; the fill rate and gap structure recorded
here say where each real token sits on that curve.

Everything reads `raw/<run>/`, so a second window is a second run rather than
an overwrite.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.bootstrap import block_bootstrap, sign_test  # noqa: E402
from analysis.cointegration import adf  # noqa: E402
from analysis.discovery import hasbrouck_share, information_share  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

# A pair needs enough paired minutes for the fit to mean anything. The estimator
# refuses fewer than 40 rows outright, and the bootstrap shows a sample of 300
# rows cannot establish its own leader, so nothing here is a clean threshold.
# 120 is chosen to sit above the estimator's own floor with room for the lags,
# and every ranked pair is reported with its sample size so a reader can
# discount the short ones rather than trust the cut.
MIN_PAIRED = 120

__all__ = ["run"]


def _one(symbol: str, paired: pd.DataFrame, coverage: pd.Series) -> dict:
    row: dict[str, object] = {
        "symbol": symbol,
        "paired_minutes": len(paired),
        "fill_rate": float(coverage.fill_rate),
        "consecutive_share": float(coverage.consecutive_share),
        "median_gap_min": int(coverage.median_gap_min),
        "max_gap_min": int(coverage.max_gap_min),
    }
    if len(paired) < MIN_PAIRED:
        row["verdict"] = "too few paired minutes"
        return row

    cex, dex = paired["cex"], paired["dex"]
    # Demeaned, because the Dickey-Fuller regression used here carries no
    # constant and so tests reversion to zero. A pool sitting at a persistent
    # premium leaves a non-zero mean in the spread, and leaving it in costs real
    # power: on TSLAX the statistic moves from -4.71 to -6.00 once it is
    # removed. The direction is safe, an undemeaned test under-rejects, but the
    # numbers reported should be the right ones.
    spread = np.log(cex) - np.log(dex)
    unit_root = adf(spread - spread.mean())
    row.update(adf_statistic=round(unit_root.statistic, 2),
               spread_stationary=bool(unit_root.rejects_unit_root()),
               spread_half_life_min=round(unit_root.half_life_min, 1))

    gg = information_share(cex, dex)
    row.update(w_cex=round(gg.weight_a, 3),
               speed_cex=round(gg.speed_a, 3),
               speed_dex=round(gg.speed_b, 3))

    hb = hasbrouck_share(cex, dex)
    row.update(hasbrouck_low=round(hb.lower, 3),
               hasbrouck_high=round(hb.upper, 3),
               innovation_correlation=round(hb.correlation, 3))

    boot = block_bootstrap(cex, dex, draws=400, seed=0)
    row.update(lead_share=round(boot.lead_share, 3),
               speed_cex_low=round(boot.speed_a_low, 3),
               speed_cex_high=round(boot.speed_a_high, 3),
               speed_dex_low=round(boot.speed_b_low, 3),
               speed_dex_high=round(boot.speed_b_high, 3),
               speeds_separated=bool(boot.speeds_are_separated()))

    # The two estimators agree when both put the exchange on the same side of
    # an even split. Hasbrouck is compared at its midpoint, with the width of
    # its bounds reported separately so a meaningless agreement is visible.
    row["agree"] = bool((gg.weight_a > 0.5) == (hb.midpoint > 0.5))
    row["verdict"] = "ranked"
    return row


def run(label: str) -> pd.DataFrame:
    """Apply every check to one collection run."""
    folder = RAW / label
    coverage = pd.read_csv(folder / "coverage.csv").set_index("symbol")
    rows = []
    for symbol in coverage.index:
        path = folder / f"{symbol}.csv"
        if not path.exists():  # pragma: no cover - coverage lists what exists
            continue
        paired = pd.read_csv(path, index_col="ts")
        rows.append(_one(symbol, paired, coverage.loc[symbol]))
    frame = pd.DataFrame(rows).sort_values("paired_minutes", ascending=False)
    DATA.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATA / f"robustness_{label}.csv", index=False)
    return frame


if __name__ == "__main__":
    run_label = sys.argv[1] if len(sys.argv) > 1 else "2026-07-29b"
    f = run(run_label)
    ranked = f[f.verdict == "ranked"]
    print(f"tokens collected: {len(f)}, ranked: {len(ranked)}\n")
    if not len(ranked):
        raise SystemExit(0)

    cols = ["symbol", "paired_minutes", "fill_rate", "spread_stationary",
            "w_cex", "speed_cex", "speed_dex", "hasbrouck_low",
            "hasbrouck_high", "innovation_correlation", "lead_share", "agree"]
    print(ranked[cols].to_string(index=False))

    stationary = ranked[ranked.spread_stationary]
    led = int((stationary.w_cex > 0.5).sum())
    print(f"\nspread stationary in {len(stationary)} of {len(ranked)} ranked pairs")
    print(f"exchange leads in {led} of those {len(stationary)}")
    print(f"sign test on that split: p = {sign_test(led, len(stationary)):.4f}")
    print(f"both estimators agree in {int(stationary.agree.sum())} of {len(stationary)}")
    print(f"bootstrap lead share: median {stationary.lead_share.median():.0%}, "
          f"min {stationary.lead_share.min():.0%}")
    print(f"innovation correlation: median {stationary.innovation_correlation.median():.2f}")
