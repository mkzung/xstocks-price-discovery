"""Build every figure in the post from the committed CSVs.

Each figure is drawn from `data/` and from nothing else, so a figure and the
prose that quotes it cannot drift apart: re-running this after a data refresh
redraws all of them, and `verify.py` then re-checks the numbers in the text
against the same files.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
FIGS = BASE / "post"

INK = "#1a1a1a"
ACCENT = "#b3261e"
MUTED = "#8a8a8a"
GRID = "#dcdcdc"

__all__ = ["build_all"]


def _style(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=INK, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def figure_relation(groups: pd.DataFrame) -> None:
    """The headline: on-chain activity against what the exchange prints."""
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    colours = {"ranked": INK, "thin": MUTED, "no on-chain market": ACCENT}
    for name, sub in groups.groupby("group"):
        ax.scatter(sub.paired_min.clip(lower=1), sub.ratio.clip(lower=0.1),
                   s=46, color=colours[name], label=name, zorder=3,
                   edgecolor="white", linewidth=0.8)
    for _, r in groups[groups.ratio > 400].iterrows():
        ax.annotate(r.symbol, (max(r.paired_min, 1), r.ratio),
                    textcoords="offset points", xytext=(7, -3),
                    fontsize=8, color=ACCENT)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("minutes the pool traded during the window", fontsize=9.5)
    ax.set_ylabel("exchange dollars per on-chain dollar", fontsize=9.5)
    ax.set_title("The quieter the chain, the more the exchange prints",
                 fontsize=11.5, color=INK, pad=12)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "relation.png", dpi=150)
    plt.close(fig)


def figure_weights(panel: pd.DataFrame) -> None:
    """Who leads, and how hard each side corrects."""
    allr = (panel[panel.regime == "all"].dropna(subset=["w_cex"])
            .sort_values("w_cex"))
    fig, (left, right) = plt.subplots(1, 2, figsize=(8.6, 4.2),
                                      gridspec_kw={"width_ratios": [1, 1.1]})
    y = np.arange(len(allr))
    left.barh(y, allr.w_cex, color=INK, height=0.62, zorder=3)
    left.axvline(0.5, color=ACCENT, linewidth=1.1, linestyle="--", zorder=4)
    left.set_yticks(y, allr.symbol, fontsize=8.5)
    left.set_xlabel("exchange weight in the common factor", fontsize=9.5)
    left.set_title("Exchange share of price discovery", fontsize=10.5, pad=10)
    left.text(0.5, -1.15, "even", color=ACCENT, fontsize=8, ha="center")
    _style(left)

    right.barh(y - 0.19, allr.speed_cex.abs(), height=0.36, color=MUTED,
               label="exchange", zorder=3)
    right.barh(y + 0.19, allr.speed_dex, height=0.36, color=INK,
               label="pool", zorder=3)
    right.set_yticks(y, allr.symbol, fontsize=8.5)
    right.set_xlabel("share of the gap closed per minute", fontsize=9.5)
    right.set_title("Who moves toward whom", fontsize=10.5, pad=10)
    right.legend(frameon=False, fontsize=8.5, loc="lower right")
    _style(right)
    fig.tight_layout()
    fig.savefig(FIGS / "weights.png", dpi=150)
    plt.close(fig)


def figure_sessions(panel: pd.DataFrame) -> None:
    """The ranking holds when the underlying equity is shut."""
    wide = panel.pivot_table(index="symbol", columns="regime", values="w_cex")
    wide = wide.dropna(subset=["all", "closed"]).sort_values("all")
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    y = np.arange(len(wide))
    ax.scatter(wide["all"], y, s=44, color=INK, label="whole window", zorder=3)
    ax.scatter(wide["closed"], y, s=44, color=ACCENT, marker="D",
               label="US market shut", zorder=3)
    for i, (_, r) in enumerate(wide.iterrows()):
        ax.plot([r["all"], r["closed"]], [i, i], color=GRID, linewidth=1.4,
                zorder=2)
    ax.axvline(0.5, color=MUTED, linewidth=1.0, linestyle="--")
    ax.set_yticks(y, wide.index, fontsize=8.5)
    ax.set_xlabel("exchange weight in the common factor", fontsize=9.5)
    ax.set_title("The lead survives the closing bell", fontsize=11, pad=12)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "sessions.png", dpi=150)
    plt.close(fig)


def figure_controls(matrix: pd.DataFrame) -> None:
    """A second exchange leads too; two pools on one mint do not."""
    rows = matrix.dropna(subset=["weight_a"]).copy()
    rows["label"] = rows.apply(
        lambda r: f"{r.token}\n{r.venue_a} vs {r.venue_b}", axis=1)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    colours = [ACCENT if r.venue_a in ("bybit", "mexc") else INK
               for _, r in rows.iterrows()]
    x = np.arange(len(rows))
    ax.bar(x, rows.weight_a, color=colours, width=0.55, zorder=3)
    ax.axhline(0.5, color=MUTED, linestyle="--", linewidth=1.0)
    ax.set_xticks(x, rows.label, fontsize=8)
    ax.set_ylabel("weight of the first venue", fontsize=9.5)
    ax.set_title("A second exchange leads; two pools on one mint do not",
                 fontsize=11, pad=12)
    _style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "controls.png", dpi=150)
    plt.close(fig)


def build_all() -> list[Path]:
    FIGS.mkdir(parents=True, exist_ok=True)
    groups = pd.read_csv(DATA / "token_groups.csv")
    panel = pd.read_csv(DATA / "panel_sessions.csv")
    matrix = pd.read_csv(DATA / "venue_matrix.csv")
    figure_relation(groups)
    figure_weights(panel)
    figure_sessions(panel)
    figure_controls(matrix)
    return sorted(FIGS.glob("*.png"))


if __name__ == "__main__":
    for path in build_all():
        print(f"wrote {path.relative_to(BASE)}")
