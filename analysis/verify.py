"""Machine-check every quantitative claim in post/index.md against the committed CSVs.

Each check has two legs. The first recomputes a value from `data/` and compares
it to what the pipeline produced, which catches a data refresh that moved a
number. The second searches the post for that value formatted the way the prose
writes it, which catches the case the first leg cannot see: the data is fine and
the sentence is stale.

The second leg is the point. An earlier version of this file had only the first,
so it compared computed values against hardcoded constants and never opened the
post at all. Every number in the text could have been wrong and it would still
have printed FAILED: 0. Whenever a check is added here, mutate the post and
confirm the check goes red before trusting it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from analysis.relation import spearman, test_relation

base = Path(__file__).resolve().parent.parent
u = pd.read_csv(base / "data" / "universe.csv")
d = pd.read_csv(base / "data" / "panel_run1.csv")
p = pd.read_csv(base / "data" / "panel_sessions.csv")
m = pd.read_csv(base / "data" / "venue_matrix.csv")
g = pd.read_csv(base / "data" / "token_groups.csv")
post = (base / "post" / "index.md").read_text()

u["ratio"] = u.cex_volume_24h / u.dex_volume_24h.clip(lower=1)
allr = p[p.regime == "all"].dropna(subset=["w_cex"])
closed = p[p.regime == "closed"].dropna(subset=["w_cex"])
rest = allr[allr.symbol != "AMZNX"]
byrow = allr.set_index("symbol")
gap = p.pivot_table(index="symbol", columns="regime",
                    values="mean_gap_pct").dropna(subset=["open", "closed"])
bybit = m[m.venue_a == "bybit"].dropna(subset=["weight_a"]).iloc[0]
pools = m[m.venue_a == "pool_deep"].dropna(subset=["weight_a"])
ranked = g[g.group == "ranked"]
thin = g[g.group == "thin"]
dead = g[g.group == "no on-chain market"]
trimmed = g.sort_values("ratio").iloc[:-6]
rho = spearman(g.paired_min, g.ratio)
rel = test_relation(g.paired_min, g.ratio, draws=20000, seed=0)

# The four wrong-sign exchange coefficients split into two that are noise and
# two that are small but real; the post names all four values.
wrong = allr[allr.speed_cex > 0].speed_cex.sort_values()
noise, real_wrong = wrong.iloc[:2], wrong.iloc[2:]

# Share of the paired window with the US equity market shut.
closed_share = (p[p.regime == "closed"].minutes.sum()
                / p[p.regime == "all"].minutes.sum())

# The robustness section restates a second window's results and the sensitivity
# sweeps. It is the same hand-typed layer as the tables above and gets the same
# treatment.
LABEL = "2026-07-29b"
rob = pd.read_csv(base / "data" / f"robustness_{LABEL}.csv")
ranked_pairs = rob[rob.verdict == "ranked"]
stale_risk = pd.read_csv(base / "data" / f"sensitivity_staleness_{LABEL}.csv")
ranked_risk = stale_risk[stale_risk.symbol.isin(ranked_pairs.symbol)]
rep = pd.read_csv(base / "data" / f"sensitivity_replication_{LABEL}.csv")
lag_sweep = pd.read_csv(base / "data" / f"sensitivity_lags_{LABEL}.csv")
grid_sweep = pd.read_csv(base / "data" / f"sensitivity_grid_{LABEL}.csv")
grid_fitted = grid_sweep.dropna(subset=["w_cex"])
lag_flips = int((lag_sweep.groupby("symbol").leads.nunique() > 1).sum())
grid_agree = int((grid_fitted.groupby("symbol").leads.nunique() == 1).sum())
sim = pd.read_csv(base / "data" / "staleness.csv")
hold_false = (sim[sim.scheme == "hold"].groupby("keep")
              .apply(lambda s: float((s.w_cex > 0.5).mean()),
                     include_groups=False))

cal = pd.read_csv(base / "data" / "calibration.csv")
lead = cal[~cal.even]
near = lead[(lead.truth - 0.5).abs() < 0.2]
far = lead[(lead.truth - 0.5).abs() >= 0.2]
rank_clear = ((far.weight_a > 0.5) == (far.truth > 0.5)).mean()
rank_near = ((near.weight_a > 0.5) == (near.truth > 0.5)).mean()

# label, computed value, the value the pipeline produced, and the exact string
# the post must contain for that value. The string is built from the computed
# value, so a data refresh that moves a number also moves what the post has to
# say before this passes.
checks = [
    ("24 paired tokens", len(u), 24, f"**{len(u)} tokens quoted on both venues**"),
    ("token count in the description", len(u), 24,
     f"description: \"Gonzalo-Granger price discovery for {len(u)} xStocks"),
    ("max ratio", round(u.ratio.max()), 7311, f"**{round(u.ratio.max()):,}\ndollars**"),
    ("min ratio", round(u.ratio.min(), 2), 0.16, f"{u.ratio.min():.2f} cents".replace("0.", "")),
    ("median ratio", round(u.ratio.median(), 1), 6.8, f"The median is {u.ratio.median():.1f}."),
    ("nine rankable", len(allr), 9, f"| {len(allr)} | {ranked.paired_min.median():.0f} |"),
    ("all exchange-led", int((allr.w_cex > 0.5).all()), 1, "The exchange\nleads every one"),
    ("four weights above one", int((allr.w_cex > 1).sum()), 4,
     f"That is why {'four' if (allr.w_cex > 1).sum() == 4 else 'ERR'} of the nine exchange"),
    ("eight-pair exchange speed", round(rest.speed_cex.abs().max(), 2), 0.08,
     f"moves at most {rest.speed_cex.abs().max():.2f} of the gap per minute"),
    ("pool speed span", round(rest.speed_dex.min(), 2), 0.22,
     f"while the pool closes {rest.speed_dex.min() * 100:.0f} to "
     f"{rest.speed_dex.max() * 100:.0f}\npercent of it"),
    ("four wrong-way", int((allr.speed_cex > 0).sum()), 4,
     f"{'Four' if (allr.speed_cex > 0).sum() == 4 else 'ERR'} of the exchange coefficients come out positive"),
    ("AMZNX speed", round(byrow.loc["AMZNX"].speed_cex, 2), -0.35,
     f"corrects meaningfully, at {abs(byrow.loc['AMZNX'].speed_cex):.2f}"),
    ("AMZNX weight", round(byrow.loc["AMZNX"].w_cex, 2), 0.63,
     f"lowest exchange weight at {byrow.loc['AMZNX'].w_cex:.2f}"),
    ("AMZNX minutes vs TSLAX", int(byrow.loc["AMZNX"].minutes), 82,
     f"{int(byrow.loc['AMZNX'].minutes)} paired minutes against\n"
     f"{int(byrow.loc['TSLAX'].minutes)} for TSLAX"),
    ("closed-session rankable", len(closed), 8, f"leaves {'eight' if len(closed) == 8 else 'ERR'} pairs measurable"),
    ("closed-session weight span", round(closed.w_cex.min(), 2), 0.96,
     f"at weights\nof {closed.w_cex.min():.2f} to {closed.w_cex.max():.2f}"),
    ("six dead tokens", int((d.paired_min < 10).sum()), 6,
     f"sit {'six' if (d.paired_min < 10).sum() == 6 else 'ERR'} tokens with no on-chain market"),
    ("bybit weight", round(bybit.weight_a, 2), 0.75, f"at a weight of {bybit.weight_a:.2f}"),
    ("bybit minutes", int(bybit.minutes), 498, f"over {int(bybit.minutes)} paired minutes"),
    ("bybit speeds", round(bybit.speed_a, 2), -0.09,
     f"at {abs(bybit.speed_a):.2f} of the gap per minute while the pool closes {bybit.speed_b:.2f}"),
    ("pool-pair weights", round(pools.weight_a.max(), 2), 0.43,
     f"Two of the three weights, {pools.weight_a.nsmallest(2).max():.2f} and "
     f"{pools.weight_a.max():.2f}"),
    ("pool-pair lowest", round(pools.weight_a.min(), 2), 0.06,
     f"NVDAX at\n{pools.weight_a.min():.2f}"),
    ("pool-pair speeds", round(pools.speed_a.abs().min(), 2), 0.58,
     f"the deeper one by {pools.speed_a.abs().min():.2f} to {pools.speed_a.abs().max():.2f} of\nthe gap"),
    ("groups cover all", len(g), 24, "The twenty-four tokens sort into three groups"),
    ("ranked group row", len(ranked), 9,
     f"| rankable | {len(ranked)} | {ranked.paired_min.median():.0f} | {ranked.ratio.median():.1f} |"),
    ("thin group row", len(thin), 9,
     f"| thin | {len(thin)} | {thin.paired_min.median():.0f} | {thin.ratio.median():.1f} |"),
    ("dead group row", len(dead), 6,
     f"| no on-chain market | {len(dead)} | {dead.paired_min.median():.0f} | "
     f"{dead.ratio.median():,.0f} |"),
    ("thin minutes span", int(thin.paired_min.max()), 73,
     f"printed in {'eleven' if thin.paired_min.min() == 11 else 'ERR'} to\n"
     f"seventy-three minutes"),
    ("spearman", round(rho, 2), -0.93, f"is **{rho:.2f}**"),
    ("spearman trimmed", round(spearman(trimmed.paired_min.reset_index(drop=True),
                                        trimmed.ratio.reset_index(drop=True)), 2), -0.92,
     f"holds at {spearman(trimmed.paired_min.reset_index(drop=True), trimmed.ratio.reset_index(drop=True)):.2f}"),
    ("liquidity rank", round(spearman(g.dex_liquidity, g.paired_min), 2), 0.92,
     f"with traded minutes\nat {spearman(g.dex_liquidity, g.paired_min):.2f}"),
    ("gap median", round(allr.mean_gap_pct.median(), 2), 0.10,
     f"median of {allr.mean_gap_pct.median():.2f} percent"),
    ("gap max", round(allr.mean_gap_pct.max(), 2), 0.14,
     f"at most {allr.mean_gap_pct.max():.2f}\n  percent"),
    # The two wrong-sign coefficients the post dismisses as noise, named.
    ("noise coefficients", round(noise.max(), 3), 0.008,
     f"{noise.min():.3f} and {noise.max():.3f}"),
    ("real wrong-sign", round(real_wrong.max(), 2), 0.08,
     f"GLDX at {real_wrong.min():.2f} and GOOGLX at {real_wrong.max():.2f}"),
    # Calibration, recomputed from the committed grid.
    ("calibration runs", len(cal), 96, "ninety-six runs over eight speed pairs"),
    ("calibration bias", round(lead.error.mean(), 2), 0.03,
     f"lands {lead.error.mean():.2f} above the truth on\naverage"),
    ("calibration scatter low", round(lead.error.min(), 2), -0.33,
     f"from {abs(lead.error.min()):.2f} below the truth"),
    ("calibration scatter high", round(lead.error.max(), 2), 0.28,
     f"to {lead.error.max():.2f} above it"),
    ("ranking recovery clear", round(rank_clear, 2), 0.98,
     f"the right leader {rank_clear * 100:.0f} percent of\nthe time"),
    ("ranking recovery near-even", round(rank_near, 2), 0.92,
     f"falling to {rank_near * 100:.0f} percent where the truth sits near even"),
    # The share of the window with the US equity market shut.
    ("closed share of window", round(closed_share, 2), 0.86,
     f"which is {closed_share * 100:.0f} percent of the window"),
    # Figure captions and alt text restate computed numbers. Nothing checked
    # them until a mutation sweep changed the caption correlation from -0.93 to
    # -0.94 and verify.py stayed green.
    ("caption correlation", round(rho, 2), -0.93,
     f"Rank correlation {rho:.2f} across all twenty-four."),
    ("alt text lowest weight", round(allr.w_cex.min(), 2), 0.63,
     f"all at or above {allr.w_cex.min():.2f}."),
    ("alt text bybit weight", round(bybit.weight_a, 2), 0.75,
     f"pool bar sits at {bybit.weight_a:.2f}"),
    # The permutation test behind the headline correlation.
    ("permutation draws and p", rel.p_value < 0.0001, True,
     f"p below {0.0001:g} on twenty thousand draws"),
    # Cointegration, tested rather than assumed.
    ("spread stationary count", int(ranked_pairs.spread_stationary.sum()), 7,
     f"**{int(ranked_pairs.spread_stationary.sum())} of {len(ranked_pairs)}** rankable pairs"),
    ("spread half-life span",
     round(ranked_pairs.spread_half_life_min.max()), 6,
     f"half-lives of {ranked_pairs.spread_half_life_min.min():.0f} to "
     f"{ranked_pairs.spread_half_life_min.max():.0f} minutes"),
    # The second estimator.
    ("estimators agree", int(ranked_pairs.agree.sum()), 7,
     f"agrees in **{int(ranked_pairs.agree.sum())} of {len(ranked_pairs)}** pairs"),
    ("innovation correlation",
     round(ranked_pairs.innovation_correlation.median(), 2), 0.39,
     f"correlation is a median {ranked_pairs.innovation_correlation.median():.2f}\nrather"),
    ("bootstrap lead span", round(ranked_pairs.lead_share.min(), 2), 0.99,
     f"leads in\n{ranked_pairs.lead_share.min() * 100:.0f} to "
     f"{ranked_pairs.lead_share.max() * 100:.0f} percent of resamples"),
    # The staleness bound, read at the ranked pairs' own fill rates.
    ("hold scheme errs at every partial fill",
     round(hold_false[hold_false.index < 1.0].min(), 2), 0.95,
     f"the exchange the leader in **{hold_false[hold_false.index < 1.0].min() * 100:.0f} to "
     f"{hold_false[hold_false.index < 1.0].max() * 100:.0f}\npercent** of runs"),
    ("hold scheme is right at complete fill", round(hold_false.loc[1.0], 2), 0.0,
     "At complete\nfill the estimator is right"),
    ("drop scheme bound", round(ranked_risk.false_lead_drop.max(), 2), 0.19,
     f"errs **{ranked_risk.false_lead_drop.min() * 100:.0f} to "
     f"{ranked_risk.false_lead_drop.max() * 100:.0f} percent** of the time"),
    ("thinnest tokens bound", round(stale_risk.false_lead_drop.max(), 2), 0.38,
     f"errs up to {stale_risk.false_lead_drop.max() * 100:.0f} percent of the time"),
    ("TSLAX risk",
     round(float(ranked_risk.set_index("symbol").loc["TSLAX"].false_lead_drop), 2),
     0.02,
     "TSLAX at half its minutes filled sits at "
     f"{float(ranked_risk.set_index('symbol').loc['TSLAX'].false_lead_drop) * 100:.0f} percent"),
    # Specification sweeps.
    ("lag flips", lag_flips, 0,
     f"changes the leader in **{lag_flips} of {lag_sweep.symbol.nunique()}**"),
    ("grid agreement", grid_agree, 7,
     f"leaves the same leader in **{grid_agree} of {grid_fitted.symbol.nunique()}**"),
    # Out-of-sample.
    ("replication count", int(rep.leads_both.sum()), 7,
     f"{int(rep.leads_both.sum())} of {len(rep)} in the second"),
    ("replication drift", round((rep.w_second - rep.w_first).abs().max(), 2), 0.11,
     f"the weights move by at most {(rep.w_second - rep.w_first).abs().max():.2f}"),
]

def table_rows(header: tuple[str, ...]) -> list[list[str]]:
    """Pull one markdown table out of the post by its full header row.

    Matching on the first column alone is not enough: three of the four tables
    lead with "token", so a first-column match returned the same table for all
    three and two of them silently went unchecked.

    Tables are the largest hand-typed restatement of the data in the post, and
    nothing checked them until every cell was compared here. A mutation sweep
    over the post found 55 of 69 numbers unguarded, almost all of them table
    cells.
    """
    for block in post.split("\n\n"):
        lines = [ln for ln in block.strip().splitlines() if ln.startswith("|")]
        cells = tuple(c.strip() for c in lines[0].split("|")[1:-1]) if lines else ()
        if len(lines) > 2 and cells == header:
            return [[c.strip() for c in ln.split("|")[1:-1]] for ln in lines[2:]]
    return []


def check_table(name: str, header: tuple[str, ...],
                expected: list[list[str]]) -> int:
    """Compare every cell of a post table against the recomputed values."""
    got = table_rows(header)
    if not got:
        print(f"  [POST] {name}: no table in the post with header {header}")
        return 1
    if got != expected:
        print(f"  [POST] {name}: table does not match the data")
        for i, want_row in enumerate(expected):
            have = got[i] if i < len(got) else None
            if have != want_row:
                print(f"         row {i}: post {have} expected {want_row}")
        return 1
    return 0


money = "${:,.0f}".format
uni = u.set_index("symbol")
universe_table = [
    [t, money(uni.loc[t].cex_volume_24h), money(uni.loc[t].dex_volume_24h),
     money(uni.loc[t].dex_liquidity),
     f"{uni.loc[t].ratio:,.0f}" if uni.loc[t].ratio >= 100 else f"{uni.loc[t].ratio:.2f}"]
    for t in ("VTIX", "ACNX", "NFLXX", "AZNX", "TQQQX", "KOX", "MSTRX",
              "TSLAX", "CRCLX", "NVDAX", "QQQX")
]
weights_table = [
    [t, f"{byrow.loc[t].w_cex:.2f}", f"{byrow.loc[t].speed_cex:+.2f}",
     f"{byrow.loc[t].speed_dex:.2f}"]
    for t in allr.sort_values("w_cex", ascending=False).symbol
]
groups_table = [
    [name, str(len(sub)), f"{sub.paired_min.median():.0f}",
     f"{sub.ratio.median():,.0f}" if sub.ratio.median() >= 100
     else f"{sub.ratio.median():.1f}"]
    for name, sub in (("rankable", ranked), ("thin", thin),
                      ("no on-chain market", dead))
]
gdead = dead.set_index("symbol").sort_values("paired_min")
dead_table = [
    [t, str(int(gdead.loc[t].paired_min)), money(gdead.loc[t].cex_volume_24h),
     money(gdead.loc[t].dex_volume_24h), money(gdead.loc[t].dex_liquidity)]
    for t in gdead.index
]

bad = 0
searched = 0
tables = (
    ("universe table",
     ("token", "Gate 24h", "on-chain 24h", "on-chain liquidity",
      "Gate per on-chain dollar"), universe_table),
    ("weights table",
     ("token", "Gate weight", "Gate correction speed", "pool correction speed"),
     weights_table),
    ("groups table",
     ("group", "tokens", "median minutes the pool traded",
      "median exchange dollars per on-chain dollar"), groups_table),
    ("dead-token table",
     ("token", "minutes the pool traded", "exchange 24h volume",
      "on-chain 24h volume", "on-chain liquidity"), dead_table),
)
for name, header, expected in tables:
    searched += sum(len(r) for r in expected)
    bad += check_table(name, header, expected)

for label, got, want, text in checks:
    drift = abs(got - want) > 0.011
    missing = text not in post
    searched += 1
    if drift:
        print(f"  [DATA] {label}: recomputed {got}, pipeline had {want}")
    if missing:
        print(f"  [POST] {label}: post does not contain {text!r}")
    bad += drift + missing

# Per-token volumes as the two tables print them.
tokens = ("VTIX", "ACNX", "NFLXX", "AZNX", "TQQQX", "KOX", "MSTRX",
          "TSLAX", "CRCLX", "NVDAX", "QQQX", "UNHX", "MCDX")
for token in tokens:
    row = u[u.symbol == token].iloc[0]
    for value in (f"${row.cex_volume_24h:,}", f"${row.dex_volume_24h:,}"):
        searched += 1
        if value not in post:
            print(f"  [POST] {token}: {value} not found in post")
            bad += 1

print(f"\nsearched {searched} claims against {len(post.splitlines())} lines of post")
print(f"FAILED: {bad}")
# Exit non-zero on any failure. Without this the CI step and the README
# reproduce flow both pass whatever the numbers say.
sys.exit(1 if bad else 0)
