"""Does how far apart the rows sit predict what the fit says.

The estimator is fitted on the minutes both venues traded in, and the minutes
neither traded in are dropped rather than filled, so one step is one row and
not one clock minute. `analysis/staleness.py` answers the objection that
follows -- that sparse trading alone could manufacture a follower -- against a
simulation with a known answer. This module answers it against the committed
data instead, which the simulation cannot do: it can say what a dropping scheme
does to a world it built, and not whether the pairs actually measured here read
differently when their pools trade less.

The question is put three ways, because how sparse a pair is has three
reasonable readings: the mean minutes between rows, the count of paired minutes,
and the fill rate. If sparseness were driving the leadership reading, the
weight would move with all three.

One prediction went in and did not come out, which is worth recording.
Reversion over a gap is concave in its length, so a long enough gap saturates
both venues' correction and pulls the ratio between them toward an even split.
That argues the sparser pairs should read nearer 0.5, which would have the
artefact eating the finding rather than feeding it. The data does not show it.
The correlation between spacing and distance from an even split is 0.13 across
23 pair-days, the wrong sign for that story and nothing at this sample size.
The reversion is slow enough against these gaps that the saturation never
arrives, so the argument is unavailable and the measurement is what stands.

The sample bounds what a null here can mean. Twenty-three pair-days can only
resolve a rank correlation of about 0.42, so this rules out a strong relation
and not a weak one.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.relation import test_relation  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

# Draws for the permutation test, and the seed, so the p-values below are the
# same on every machine that runs this.
DRAWS = 20_000
SEED = 0

__all__ = ["spacing_table", "run"]


def spacing_table(label: str) -> pd.DataFrame:
    """One row per ranked pair: how far apart its rows sit, and what it read."""
    ranked = pd.read_csv(DATA / f"robustness_{label}.csv")
    rows = []
    for token in ranked[ranked.verdict == "ranked"].itertuples():
        paired = pd.read_csv(RAW / label / f"{token.symbol}.csv",
                             index_col="ts").sort_index()
        step = pd.Series(paired.index).diff().dropna() / 60
        rows.append({
            "window": label,
            "symbol": token.symbol,
            "mean_step_min": round(float(step.mean()), 2),
            "median_step_min": round(float(step.median()), 1),
            "paired_minutes": int(token.paired_minutes),
            "fill_rate": round(float(token.fill_rate), 3),
            "w_cex": token.w_cex,
        })
    return pd.DataFrame(rows)


def run(labels: list[str]) -> pd.DataFrame:
    # Own the row order rather than inheriting the robustness table's.
    table = pd.concat([spacing_table(x) for x in labels],
                      ignore_index=True).sort_values(
        ["window", "symbol"]).reset_index(drop=True)
    table.to_csv(DATA / "spacing.csv", index=False)
    return table


if __name__ == "__main__":
    windows = sys.argv[1:] or ["2026-07-29b", "2026-07-30", "2026-07-31"]
    table = run(windows)
    print(table.to_string(index=False))

    print(f"\nAcross {len(table)} pair-days, against the exchange weight:")
    for name, column in (("mean minutes between rows", table.mean_step_min),
                         ("paired minutes", table.paired_minutes),
                         ("fill rate", table.fill_rate)):
        result = test_relation(column, table.w_cex, draws=DRAWS, seed=SEED)
        print(f"  {name:26} rho {result.rho:+.3f}   permutation p "
              f"{result.p_value:.3f}")

    half = table.mean_step_min.median()
    tight = table[table.mean_step_min <= half]
    wide = table[table.mean_step_min > half]
    print(f"\n  exchange-led, tighter-spaced half: "
          f"{int((tight.w_cex > 0.5).sum())} of {len(tight)}")
    print(f"  exchange-led, wider-spaced half:   "
          f"{int((wide.w_cex > 0.5).sum())} of {len(wide)}")
    print("\n  A sample this size resolves a rank correlation of about 0.42, "
          "so this\n  rules out a strong relation and not a weak one.")
