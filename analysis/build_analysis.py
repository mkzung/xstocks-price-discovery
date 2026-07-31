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
    # Explicit order: groupby sorts alphabetically, which lists the dead tokens
    # first and reads backwards against the gradient the figure shows.
    for name in ("ranked", "thin", "no on-chain market"):
        sub = groups[groups.group == name]
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
    right.set_title("Who moves toward whom", fontsize=10.5, pad=30)
    # Inside the axes this lands on the bottom token's bars; directly above,
    # it landed on the title. The title gets extra padding and the legend sits
    # in the gap between the two.
    right.legend(frameon=False, fontsize=8, loc="lower center",
                 bbox_to_anchor=(0.5, 1.005), ncol=2, handlelength=1.6,
                 columnspacing=1.2)
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
    short = {"bybit": "Bybit", "pool": "pool", "pool_deep": "deep pool",
             "pool_second": "second pool"}
    rows["label"] = rows.apply(
        lambda r: f"{r.token}\n{short[r.venue_a]} vs {short[r.venue_b]}",
        axis=1)
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
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


def figure_weights_series(rob: pd.DataFrame) -> None:
    """The same picture for the pass that carries the extra evidence.

    `figure_weights` draws the session panel, which is what the post's early
    table reports. The dashboard leads with the series pass instead, because
    that is the pass with Hasbrouck bounds and a bootstrap behind it, and a
    figure of nine tokens under a table of seven invites the reader to look for
    two that are not there.
    """
    ranked = rob.sort_values("w_cex")
    fig, (left, right) = plt.subplots(1, 2, figsize=(9.0, 4.1),
                                      gridspec_kw={"width_ratios": [1, 1.05]})
    y = np.arange(len(ranked))

    # A bar implies a magnitude, and the whole point of the surrounding text is
    # that a single weight is a noisy ratio. A point with an interval says that.
    for i, r in enumerate(ranked.itertuples()):
        left.plot([r.hasbrouck_low, r.hasbrouck_high], [i, i], color=MUTED,
                  linewidth=3.0, solid_capstyle="round", zorder=3,
                  label="Hasbrouck bounds" if i == 0 else None)
    left.scatter(ranked.w_cex, y, s=52, color=INK, zorder=4,
                 label="Gonzalo-Granger weight")
    left.axvline(0.5, color=ACCENT, linewidth=1.1, linestyle="--", zorder=2)
    # Below the lowest row, or it collides with the legend above the axes.
    left.text(0.5, -0.75, "even", color=ACCENT, fontsize=8, ha="center")
    left.set_yticks(y, ranked.symbol, fontsize=8.5)
    left.set_xlim(0.35, 1.35)
    left.set_xlabel("exchange share of price discovery", fontsize=9.5)
    left.set_title("Two estimators, one direction", fontsize=10.5, pad=26)
    left.legend(frameon=False, fontsize=8, loc="lower center",
                bbox_to_anchor=(0.5, 1.005), ncol=2, handlelength=1.6,
                columnspacing=1.2)
    _style(left)

    right.barh(y - 0.19, ranked.speed_cex.abs(), height=0.36, color=MUTED,
               label="exchange", zorder=3)
    right.barh(y + 0.19, ranked.speed_dex, height=0.36, color=INK,
               label="pool", zorder=3)
    right.set_yticks(y, ranked.symbol, fontsize=8.5)
    right.set_xlabel("share of the gap closed per minute", fontsize=9.5)
    right.set_title("The pool closes the gap, the book does not",
                    fontsize=10.5, pad=26)
    right.legend(frameon=False, fontsize=8, loc="lower center",
                 bbox_to_anchor=(0.5, 1.005), ncol=2, handlelength=1.6,
                 columnspacing=1.2)
    _style(right)
    fig.tight_layout()
    fig.savefig(FIGS / "weights-series.png", dpi=150)
    plt.close(fig)


def figure_staleness(risk: pd.DataFrame, ranked: list[str]) -> None:
    """How much of the finding sparse trading could explain, per token."""
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    shown = risk.sort_values("fill_rate")
    ax.plot(shown.fill_rate * 100, shown.false_lead_hold * 100, color=ACCENT,
            linewidth=1.8, marker="o", markersize=4,
            label="carrying the last price forward")
    ax.plot(shown.fill_rate * 100, shown.false_lead_drop * 100, color=INK,
            linewidth=1.8, marker="o", markersize=4,
            label="dropping untraded minutes, as done here")
    inside = shown[shown.symbol.isin(ranked)]
    ax.scatter(inside.fill_rate * 100, inside.false_lead_drop * 100, s=70,
               facecolor="white", edgecolor=INK, linewidth=1.6, zorder=4,
               label="the ranked pairs")
    # Several ranked tokens sit within a percentage point of each other on the
    # fill axis, so labels alternate above and below to stay readable.
    for i, r in enumerate(inside.sort_values("fill_rate").itertuples()):
        offset = (7, 7) if i % 2 == 0 else (7, -11)
        ax.annotate(r.symbol, (r.fill_rate * 100, r.false_lead_drop * 100),
                    textcoords="offset points", xytext=offset, fontsize=7.5,
                    color=INK)
    ax.set_xlabel("share of minutes the pool printed in", fontsize=9.5)
    ax.set_ylabel("simulated rate of inventing a leader, percent", fontsize=9.5)
    ax.set_title("What the sampling choice costs, measured against a known answer",
                 fontsize=11, color=INK, pad=12)
    ax.set_ylim(-4, 104)
    ax.legend(frameon=False, fontsize=8.5, loc="center right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(FIGS / "staleness.png", dpi=150)
    plt.close(fig)


def figure_replication(rep: pd.DataFrame) -> None:
    """The same tokens measured on a second window."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(8.6, 4.1))
    y = np.arange(len(rep))
    left.scatter(rep.w_first, y, s=46, color=MUTED, label="first window", zorder=3)
    left.scatter(rep.w_second, y, s=46, color=INK, marker="D",
                 label="second window", zorder=3)
    for i, r in enumerate(rep.itertuples()):
        left.plot([r.w_first, r.w_second], [i, i], color=GRID, linewidth=1.4)
    left.axvline(0.5, color=ACCENT, linestyle="--", linewidth=1.0)
    left.set_yticks(y, rep.symbol, fontsize=8.5)
    left.set_xlabel("exchange weight", fontsize=9.5)
    left.set_title("Weights across two windows", fontsize=10.5, pad=22)
    # Inside the axes the legend lands on the bottom row, so it goes above.
    left.legend(frameon=False, fontsize=8.5, loc="lower center",
                bbox_to_anchor=(0.5, 1.06), ncol=2)
    _style(left)

    lim = max(rep.speed_dex_first.max(), rep.speed_dex_second.max()) * 1.15
    right.plot([0, lim], [0, lim], color=GRID, linewidth=1.2, zorder=1)
    right.scatter(rep.speed_dex_first, rep.speed_dex_second, s=52, color=INK,
                  zorder=3)
    # Three tokens sit almost on top of each other near 0.22, so labels fan out.
    for i, r in enumerate(rep.sort_values("speed_dex_first").itertuples()):
        fan = [(8, -2), (8, -12), (-38, -12), (8, 6)][i % 4]
        right.annotate(r.symbol, (r.speed_dex_first, r.speed_dex_second),
                       textcoords="offset points", xytext=fan, fontsize=7.5,
                       color=INK)
    right.set_xlabel("pool correction speed, first window", fontsize=9.5)
    right.set_ylabel("second window", fontsize=9.5)
    right.set_title("The speeds themselves replicate", fontsize=10.5, pad=10)
    _style(right)
    fig.tight_layout()
    fig.savefig(FIGS / "replication.png", dpi=150)
    plt.close(fig)


# The processed datasets behind every figure and table in the post, mirrored
# into the post's own directory. The wiki maintainer asks for datasets beside
# the article rather than only in the repository around it, and a copy that is
# synced here and byte-checked by verify.py cannot drift from the originals.
POST_DATA = ("universe.csv", "token_groups.csv", "panel_run1.csv",
             "panel_sessions.csv", "venue_matrix.csv", "calibration.csv",
             "staleness.csv", "robustness_2026-07-29b.csv",
             "robustness_2026-07-30.csv", "robustness_2026-07-31.csv",
             "sensitivity_staleness_2026-07-29b.csv",
             "sensitivity_replication_2026-07-29b.csv",
             "windows_relation.csv", "windows_leadership.csv", "collisions.csv")


def sync_post_data() -> None:
    """Mirror the post's datasets into post/data/."""
    target = FIGS / "data"
    target.mkdir(parents=True, exist_ok=True)
    for name in POST_DATA:
        (target / name).write_bytes((DATA / name).read_bytes())


def build_all(label: str = "2026-07-29b") -> list[Path]:
    FIGS.mkdir(parents=True, exist_ok=True)
    groups = pd.read_csv(DATA / "token_groups.csv")
    panel = pd.read_csv(DATA / "panel_sessions.csv")
    matrix = pd.read_csv(DATA / "venue_matrix.csv")
    figure_relation(groups)
    figure_weights(panel)
    figure_sessions(panel)
    figure_controls(matrix)

    risk = pd.read_csv(DATA / f"sensitivity_staleness_{label}.csv")
    robust = pd.read_csv(DATA / f"robustness_{label}.csv")
    robust = robust[robust.verdict == "ranked"]
    figure_weights_series(robust)
    figure_staleness(risk, robust.symbol.tolist())
    sync_post_data()
    figure_replication(pd.read_csv(DATA / f"sensitivity_replication_{label}.csv"))
    return sorted(FIGS.glob("*.png"))


if __name__ == "__main__":
    for path in build_all():
        print(f"wrote {path.relative_to(BASE)}")
