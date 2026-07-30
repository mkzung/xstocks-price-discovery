"""Everything so far was measured on one date. This measures it on another.

The leadership result survives five separate ways of being wrong, but every one
of those checks runs inside windows collected hours apart on one date. And the
headline of the post is not the leadership at all: it is the rank correlation
between how much a pool trades and how many exchange dollars are printed against
it, computed once, on one snapshot. A correlation of -0.93 from a single draw of
twenty-four tokens is a striking number attached to a weak claim.

This compares any set of collection runs on the two things worth repeating: the
correlation, recomputed from each run's own volume snapshot and its own measured
pool activity, and which venue led each token. A finding that moves between days
is a finding about a day.

Each run carries its own `universe.csv` snapshot, so no run borrows another's
volumes. That separation was learned the hard way: a refresh once overwrote the
committed snapshot and silently invalidated every volume figure in the post.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.relation import spearman, test_relation  # noqa: E402

RAW = BASE / "raw"
DATA = BASE / "data"

__all__ = ["ratio_relation", "leadership_across_windows"]


def ratio_relation(label: str, *, draws: int = 20000) -> dict:
    """Recompute the activity-against-volume correlation from one run alone.

    Uses the run's own volume snapshot where it has one, and its own measured
    paired minutes as the activity measure rather than a number carried over
    from another window.
    """
    folder = RAW / label
    universe_path = folder / "universe.csv"
    if not universe_path.exists():
        return {"window": label, "tokens": 0,
                "note": "no volume snapshot for this run"}
    universe = pd.read_csv(universe_path).set_index("symbol")
    coverage = pd.read_csv(folder / "coverage.csv").set_index("symbol")
    shared = sorted(set(universe.index) & set(coverage.index))
    frame = pd.DataFrame({
        "paired_min": coverage.loc[shared].paired_minutes,
        "ratio": (universe.loc[shared].cex_volume_24h
                  / universe.loc[shared].dex_volume_24h.clip(lower=1)),
        "liquidity": universe.loc[shared].dex_liquidity,
    }).reset_index(drop=True)

    rho = spearman(frame.paired_min, frame.ratio)
    test = test_relation(frame.paired_min, frame.ratio, draws=draws, seed=0)

    # Dropping the six most extreme ratios tests whether the correlation is
    # carried by the tail. On a short window that leaves too little to correlate:
    # trimming six of nine left three tokens and flipped the sign, which says
    # nothing about the tail and everything about a sample of three. Report the
    # trimmed figure only when enough remains for it to mean something.
    trimmed = frame.sort_values("ratio").iloc[:-6].reset_index(drop=True)
    rho_trimmed = (round(spearman(trimmed.paired_min, trimmed.ratio), 3)
                   if len(trimmed) >= 10 else None)
    return {
        "window": label,
        "tokens": len(frame),
        "rho": round(rho, 3),
        "p_value": test.p_value,
        "rho_trimmed": rho_trimmed,
        "trimmed_tokens": len(trimmed),
        "rho_liquidity": round(spearman(frame.liquidity, frame.paired_min), 3),
        "median_ratio": round(float(frame.ratio.median()), 2),
        "max_ratio": round(float(frame.ratio.max())),
    }


def leadership_across_windows(labels: list[str]) -> pd.DataFrame:
    """One row per token, one column per window, holding the fitted weight.

    Only series passes appear here, since only they produce a robustness file.
    `sensitivity.replication` handles the other comparison, between a series pass
    and the session panel, which keeps no minute series and so cannot be read the
    same way.
    """
    frames = {}
    for label in labels:
        path = DATA / f"robustness_{label}.csv"
        if not path.exists():
            continue
        rob = pd.read_csv(path)
        ranked = rob[rob.verdict == "ranked"].set_index("symbol")
        frames[label] = ranked.w_cex
    if not frames:
        return pd.DataFrame()
    wide = pd.DataFrame(frames)
    cols = list(frames)
    wide["windows_ranked"] = wide[cols].notna().sum(axis=1)
    # A window where a token was not rankable is missing evidence, not evidence
    # against. Comparing the raw frame counted a missing window as a loss, which
    # reported two tokens as failing to lead when they simply were not collected.
    wide["led_every_window"] = wide[cols].apply(
        lambda row: bool(row.dropna().gt(0.5).all()) and bool(row.notna().any()),
        axis=1)
    wide["spread_across_windows"] = (wide[cols].max(axis=1)
                                     - wide[cols].min(axis=1)).round(3)
    wide.loc[wide.windows_ranked < 2, "spread_across_windows"] = None
    return wide.sort_values(["windows_ranked", "spread_across_windows"],
                            ascending=[False, True])


def run(labels: list[str]) -> None:
    rows = [ratio_relation(label) for label in labels]
    relation = pd.DataFrame(rows)
    relation.to_csv(DATA / "windows_relation.csv", index=False)
    print("The headline correlation, recomputed inside each window.")
    print(relation.to_string(index=False))

    measured = relation.dropna(subset=["rho"]) if "rho" in relation else relation
    if len(measured) > 1:
        print(f"\n  correlation across windows: {measured.rho.min():.2f} to "
              f"{measured.rho.max():.2f}")
        print(f"  every window significant at 0.001: "
              f"{bool((measured.p_value < 0.001).all())}")

    wide = leadership_across_windows(labels)
    if len(wide):
        wide.to_csv(DATA / "windows_leadership.csv")
        print("\nFitted exchange weight per token per window.")
        print(wide.to_string())
        both = wide[wide.windows_ranked >= 2]
        print(f"\n  tokens rankable in more than one window: {len(both)}")
        if len(both):
            print(f"  of those, exchange led in every window they appear in: "
                  f"{int(both.led_every_window.sum())}")
            print(f"  largest spread in a weight across windows: "
                  f"{both.spread_across_windows.max():.3f}")
        once = wide[wide.windows_ranked == 1]
        if len(once):
            print(f"  rankable in one window only, so untested across days: "
                  f"{', '.join(once.index)}")


if __name__ == "__main__":
    run(sys.argv[1:] or ["2026-07-29b", "2026-07-30"])
