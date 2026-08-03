"""Three ways the leadership result could still be an accident, priced.

The robustness run establishes that the model applies, that a second estimator
agrees, and that each token's own data supports its lead. Three questions
survive that.

How much of each token's lead could sparse trading explain. `staleness.py`
measures, on synthetic data with a known answer, how often the estimator invents
exchange leadership at a given fill rate. Every real token has a measured fill
rate, so that curve can be read at each one: a token filling half its minutes
sits where the simulation almost never errs, a token filling an eighth sits
where it errs about one time in five. This turns the objection into a number per
token instead of a paragraph.

Does the answer depend on the lag order. Five lags was a choice. If the ordering
moves when it becomes one or ten, the result is a specification artefact.

Does it depend on the minute. Pools arbitrage inside a block, so a minute grid
may be too coarse to see the true sequence. Resampling to five minutes coarsens
it deliberately: a result that only exists at one sampling frequency is not a
result.

The window collected here is also not the window the original panel used, so the
overlap between the two is an out-of-sample replication rather than a re-run.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.discovery import information_share  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"
LAGS = (1, 3, 5, 10)
GRID_MINUTES = 5

__all__ = ["lag_sweep", "grid_sweep", "staleness_risk", "replication"]


def _paired(label: str, symbol: str) -> pd.DataFrame:
    frame = pd.read_csv(RAW / label / f"{symbol}.csv", index_col="ts")
    frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
    return frame


def lag_sweep(label: str, symbols: list[str]) -> pd.DataFrame:
    """Refit every ranked pair at each lag order."""
    rows = []
    for symbol in symbols:
        paired = _paired(label, symbol)
        for lags in LAGS:
            try:
                fit = information_share(paired.cex, paired.dex, lags=lags)
            except ValueError:
                continue
            rows.append({"symbol": symbol, "lags": lags,
                         "w_cex": round(fit.weight_a, 3),
                         "speed_cex": round(fit.speed_a, 3),
                         "speed_dex": round(fit.speed_b, 3),
                         "leads": bool(fit.weight_a > 0.5)})
    return pd.DataFrame(rows)


def grid_sweep(label: str, symbols: list[str]) -> pd.DataFrame:
    """Refit every ranked pair on a deliberately coarser grid.

    The pool side is resampled by last observation, which is what a coarser bar
    means for a venue that does not print every minute.
    """
    rows = []
    for symbol in symbols:
        paired = _paired(label, symbol)
        coarse = paired.resample(f"{GRID_MINUTES}min").last().dropna()
        for name, frame in (("1min", paired), (f"{GRID_MINUTES}min", coarse)):
            try:
                fit = information_share(frame.cex, frame.dex)
            except ValueError:
                rows.append({"symbol": symbol, "grid": name,
                             "rows": len(frame), "w_cex": np.nan,
                             "leads": None})
                continue
            rows.append({"symbol": symbol, "grid": name, "rows": len(frame),
                         "w_cex": round(fit.weight_a, 3),
                         "speed_cex": round(fit.speed_a, 3),
                         "speed_dex": round(fit.speed_b, 3),
                         "leads": bool(fit.weight_a > 0.5)})
    return pd.DataFrame(rows)


def staleness_risk(label: str) -> pd.DataFrame:
    """Read the simulated false-leader rate at each token's measured fill rate.

    The simulation sweeps fill rates on a grid, so a token's rate is placed by
    linear interpolation between the two nearest grid points. Only the sampling
    scheme the pipeline uses is read, which is dropping untraded minutes; the
    forward-filling figure is reported alongside to show what the pipeline
    avoids by not doing that.
    """
    sim = pd.read_csv(DATA / "staleness.csv")
    curves = {}
    for scheme, sub in sim.groupby("scheme"):
        by_keep = (sub.groupby("keep")
                   .apply(lambda s: float((s.w_cex > 0.5).mean()),
                          include_groups=False)
                   .sort_index())
        curves[scheme] = by_keep

    coverage = pd.read_csv(RAW / label / "coverage.csv")
    rows = []
    for _, token in coverage.iterrows():
        entry = {"symbol": token.symbol, "fill_rate": token.fill_rate,
                 "consecutive_share": token.consecutive_share}
        for scheme, curve in curves.items():
            entry[f"false_lead_{scheme}"] = round(
                float(np.interp(token.fill_rate, curve.index.to_numpy(),
                                curve.to_numpy())), 3)
        rows.append(entry)
    # Sorted with an explicit tie-break. pandas' default sort is not
    # stable, so rows sharing a key came out in a different order on the
    # CI runner than on the machine that wrote the file, and the workflow's
    # artefact diff failed on nothing but row order.
    return pd.DataFrame(rows).sort_values(
        ["fill_rate", "symbol"], ascending=[False, True])


def replication(label: str) -> pd.DataFrame:
    """Compare this pass's weights against the session panel's.

    Distinct from `windows.leadership_across_windows`, which lines up two series
    passes against each other. This one crosses the two pipelines: the session
    panel keeps no minute series, so it cannot go through the same comparison and
    needs its own. Both are kept because they answer different questions, and the
    duplication is named here so the next reader does not have to work it out.
    """
    old = pd.read_csv(DATA / "panel_sessions.csv")
    old = (old[old.regime == "all"].dropna(subset=["w_cex"])
           .set_index("symbol")[["w_cex", "speed_cex", "speed_dex", "minutes"]])
    new = pd.read_csv(DATA / f"robustness_{label}.csv")
    new = new[new.verdict == "ranked"].set_index("symbol")
    shared = sorted(set(old.index) & set(new.index))
    rows = []
    for symbol in shared:
        rows.append({
            "symbol": symbol,
            "w_first": round(float(old.loc[symbol].w_cex), 3),
            "w_second": round(float(new.loc[symbol].w_cex), 3),
            "speed_cex_first": round(float(old.loc[symbol].speed_cex), 3),
            "speed_cex_second": round(float(new.loc[symbol].speed_cex), 3),
            "speed_dex_first": round(float(old.loc[symbol].speed_dex), 3),
            "speed_dex_second": round(float(new.loc[symbol].speed_dex), 3),
            "leads_both": bool(old.loc[symbol].w_cex > 0.5
                               and new.loc[symbol].w_cex > 0.5),
        })
    return pd.DataFrame(rows)


def run(label: str) -> None:
    robust = pd.read_csv(DATA / f"robustness_{label}.csv")
    ranked = robust[robust.verdict == "ranked"].symbol.tolist()

    lags = lag_sweep(label, ranked)
    lags.to_csv(DATA / f"sensitivity_lags_{label}.csv", index=False)
    print("Lag order. The ordering must not depend on it.")
    wide = lags.pivot(index="symbol", columns="lags", values="w_cex")
    print(wide.to_string())
    flips = lags.groupby("symbol").leads.nunique()
    print(f"  tokens whose leader changes with the lag order: "
          f"{int((flips > 1).sum())} of {len(flips)}\n")

    grid = grid_sweep(label, ranked)
    grid.to_csv(DATA / f"sensitivity_grid_{label}.csv", index=False)
    print(f"Sampling grid. One minute against {GRID_MINUTES}.")
    print(grid.pivot(index="symbol", columns="grid",
                     values="w_cex").to_string())
    fitted = grid.dropna(subset=["w_cex"])
    agree = (fitted.groupby("symbol").leads.nunique() == 1).sum()
    print(f"  tokens giving the same leader on both grids: {agree} of "
          f"{fitted.symbol.nunique()}\n")

    risk = staleness_risk(label)
    risk.to_csv(DATA / f"sensitivity_staleness_{label}.csv", index=False)
    print("Sparse trading. Simulated rate of inventing exchange leadership,")
    print("read at each token's own fill rate, for both sampling schemes.")
    print(risk.to_string(index=False))
    ranked_risk = risk[risk.symbol.isin(ranked)]
    print(f"  across the ranked pairs, the pipeline's scheme errs "
          f"{ranked_risk.false_lead_drop.min():.0%} to "
          f"{ranked_risk.false_lead_drop.max():.0%} of the time")
    print(f"  forward-filling instead would err "
          f"{ranked_risk.false_lead_hold.min():.0%} to "
          f"{ranked_risk.false_lead_hold.max():.0%}\n")

    rep = replication(label)
    rep.to_csv(DATA / f"sensitivity_replication_{label}.csv", index=False)
    print("Out-of-sample. The first window against this one.")
    print(rep.to_string(index=False))
    if len(rep):
        print(f"  exchange leads in both windows for {int(rep.leads_both.sum())} "
              f"of {len(rep)} shared tokens")
        print(f"  largest weight change: "
              f"{(rep.w_second - rep.w_first).abs().max():.3f}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "2026-07-29b")
