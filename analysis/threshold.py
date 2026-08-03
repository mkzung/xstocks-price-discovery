"""Does the 120-minute floor choose the answer it reports.

Every ranked tally in the post is drawn from pairs with at least MIN_PAIRED
paired minutes. That floor is defensible on its own terms -- the bootstrap
shows a few hundred rows cannot establish their own leader -- but a cut is only
innocent if it does not select on the outcome, and nothing here had checked
that. If the pairs below the floor leaned the other way, the floor would be
doing the work and the tally would be an artefact of where it was drawn.

So the estimator is run on them too. Not to add them as evidence: at forty to a
hundred paired minutes it scatters badly and several readings land outside the
range a weight can take at all, which is the reason for the floor rather than
an argument against it. The only question asked here is which way they point.

Pairs the estimator refuses outright, under its own forty-row minimum, are
counted separately. A pool that printed three times in sixteen hours has
nothing to say either way and should not be quietly folded into a denominator.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.discovery import information_share  # noqa: E402
from analysis.robustness import MIN_PAIRED  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

__all__ = ["below_the_floor", "run"]


def below_the_floor(label: str) -> pd.DataFrame:
    """Fit every pair in one pass, whichever side of the floor it falls."""
    verdicts = pd.read_csv(DATA / f"robustness_{label}.csv").set_index("symbol")
    rows = []
    for symbol, token in verdicts.iterrows():
        path = RAW / label / f"{symbol}.csv"
        if not path.exists():  # pragma: no cover - coverage lists what exists
            continue
        paired = pd.read_csv(path, index_col="ts")
        entry = {"window": label, "symbol": symbol, "minutes": len(paired),
                 "kept": bool(token.verdict == "ranked")}
        try:
            entry["w_cex"] = round(information_share(paired.cex,
                                                     paired.dex).weight_a, 3)
        except ValueError:
            entry["w_cex"] = None
        rows.append(entry)
    return pd.DataFrame(rows)


def run(labels: list[str]) -> pd.DataFrame:
    # Own the row order rather than inheriting the robustness table's,
    # which pandas produced with an unstable sort.
    table = pd.concat([below_the_floor(x) for x in labels],
                      ignore_index=True).sort_values(
        ["window", "minutes", "symbol"],
        ascending=[True, False, True]).reset_index(drop=True)
    table.to_csv(DATA / "threshold.csv", index=False)
    return table


if __name__ == "__main__":
    windows = sys.argv[1:] or ["2026-07-29b", "2026-07-30", "2026-07-31"]
    table = run(windows)
    fitted = table.dropna(subset=["w_cex"])
    kept = fitted[fitted.kept]
    dropped = fitted[~fitted.kept]
    refused = table[table.w_cex.isna()]

    print(f"The floor is {MIN_PAIRED} paired minutes.\n")
    for name, part in (("kept", kept), ("below the floor", dropped)):
        print(f"  {name:16s} pairs {len(part):2d}   "
              f"exchange-leaning {int((part.w_cex > 0.5).sum()):2d}   "
              f"median weight {part.w_cex.median():.2f}   "
              f"minutes {int(part.minutes.min())} to {int(part.minutes.max())}")
    outside = int(((dropped.w_cex < 0) | (dropped.w_cex > 1)).sum())
    print(f"\n  of the {len(dropped)} below the floor, {outside} print outside "
          f"the range a weight can take,")
    print("  which is the floor's own justification rather than a result.")
    print(f"  {len(refused)} more pairs the estimator refuses outright, on too "
          f"few rows to fit.")
    print(f"\n  Pooled over everything fittable: "
          f"{int((fitted.w_cex > 0.5).sum())} of {len(fitted)} lean to the "
          f"exchange.")
