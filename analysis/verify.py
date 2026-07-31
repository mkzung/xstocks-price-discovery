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

The current state of that sweep: bumping each of the 135 distinct numbers in
the post by one unit in its last digit turns 120 of them red. The 15 that stay
green are day, month and year components inside URLs and the frontmatter date,
plus the Hasbrouck citation year, which the sweep also hits when it bumps a
two-digit number that first occurs as a substring of 1995. None of them restates
a computed value. The sweep has caught real gaps twice: the whole robustness
table once shipped uncompared, and the lede's joint 21-of-23 tally was
unguarded in both places it is made.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from analysis.bootstrap import sign_test
from analysis.collect import MIN_CEX_VOLUME
from analysis.robustness import MIN_PAIRED
from analysis.relation import spearman, test_relation


def _flat(text: str) -> str:
    """Collapse every run of whitespace to one space.

    Searches run against the flattened post so that a phrase is found wherever
    the line break inside it happens to fall. Matching the raw text made every
    check hostage to the wrap: rewrapping one paragraph reddened a dozen checks
    that were about numbers, not layout, and the fix each time was to move a
    newline inside a search string, which is not verification of anything.
    """
    return re.sub(r"\s+", " ", text)

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
# The later collection days, and the cross-window comparison built from them.
SECOND = "2026-07-30"
THIRD = "2026-07-31"
day2 = (pd.read_csv(base / "data" / "windows_relation.csv")
        .set_index("window").loc[SECOND])
day2_universe = pd.read_csv(base / "raw" / SECOND / "universe.csv")
day2_coverage = pd.read_csv(base / "raw" / SECOND / "coverage.csv")
day2_rob = pd.read_csv(base / "data" / f"robustness_{SECOND}.csv")
day2_ranked = day2_rob[day2_rob.verdict == "ranked"]
day2_vec = pd.read_csv(base / "data" / f"vector_{SECOND}.csv")
day3 = (pd.read_csv(base / "data" / "windows_relation.csv")
        .set_index("window").loc[THIRD])
day3_universe = pd.read_csv(base / "raw" / THIRD / "universe.csv")
day3_coverage = pd.read_csv(base / "raw" / THIRD / "coverage.csv")
day3_rob = pd.read_csv(base / "data" / f"robustness_{THIRD}.csv")
day3_ranked = day3_rob[day3_rob.verdict == "ranked"].set_index("symbol")

# The lede's joint claim: pair-days across every series pass, each day's ranked
# pairs counted once, led where the weight clears an even split. The mutation
# sweep found both numbers unguarded in the description and the lede.
pair_days = len(ranked_pairs) + len(day2_ranked) + len(day3_ranked)
led_days = (int((ranked_pairs.w_cex > 0.5).sum())
            + int((day2_ranked.w_cex > 0.5).sum())
            + int((day3_ranked.w_cex > 0.5).sum()))
both_windows = pd.read_csv(base / "data" / "windows_leadership.csv", index_col=0)
both_windows = (both_windows[both_windows.windows_ranked >= 2]
                .sort_values("spread_across_windows"))

# TSLAX is the token the registry uses to show the four passes disagree.
tslax_counts = [
    int(d.set_index("symbol").loc["TSLAX"].paired_min),
    int(byrow.loc["TSLAX"].minutes),
    int(pd.read_csv(base / "raw" / LABEL / "coverage.csv")
        .set_index("symbol").loc["TSLAX"].paired_minutes),
    int(pd.read_csv(base / "raw" / SECOND / "coverage.csv")
        .set_index("symbol").loc["TSLAX"].paired_minutes),
    int(pd.read_csv(base / "raw" / THIRD / "coverage.csv")
        .set_index("symbol").loc["TSLAX"].paired_minutes),
]

vec = pd.read_csv(base / "data" / f"vector_{LABEL}.csv")
vecrow = vec.set_index("symbol")
sim = pd.read_csv(base / "data" / "staleness.csv")
hold_false = (sim[sim.scheme == "hold"].groupby("keep")
              .apply(lambda s: float((s.w_cex > 0.5).mean()),
                     include_groups=False))

collisions = pd.read_csv(base / "data" / "collisions.csv")

# The strict predeclared tally: only weights outside 0.3 to 0.7 classify.
strict_ex = strict_pool = strict_near = 0
for _day in (ranked_pairs, day2_ranked, day3_ranked.reset_index()):
    strict_ex += int((_day.w_cex > 0.7).sum())
    strict_pool += int((_day.w_cex < 0.3).sum())
    strict_near += int(((_day.w_cex >= 0.3) & (_day.w_cex <= 0.7)).sum())

matched = pd.read_csv(base / "data" / "staleness_matched.csv")
matched = matched[matched.fitted]
matched_1000_50 = matched[(matched.n == 1000) & (matched.keep == 0.5)]
matched_1000_12 = matched[(matched.n == 1000) & (matched.keep == 0.12)]

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
     f"measured on {len(u)} xStocks quoted at once"),
    ("max ratio", round(u.ratio.max()), 7311, f"**{round(u.ratio.max()):,} dollars**"),
    ("min ratio", round(u.ratio.min(), 2), 0.16, f"{u.ratio.min():.2f} cents".replace("0.", "")),
    ("median ratio", round(u.ratio.median(), 1), 6.8, f"The median is {u.ratio.median():.1f}."),
    ("nine rankable", len(allr), 9, f"| {len(allr)} | {ranked.paired_min.median():.0f} |"),
    ("all exchange-led", int((allr.w_cex > 0.5).all()), 1,
     "in that pass the exchange leads every one"),
    ("four weights above one", int((allr.w_cex > 1).sum()), 4,
     f"That is why {'four' if (allr.w_cex > 1).sum() == 4 else 'ERR'} of the nine exchange"),
    ("eight-pair exchange speed", round(rest.speed_cex.abs().max(), 2), 0.08,
     f"moves at most {rest.speed_cex.abs().max():.2f} of the gap per minute"),
    ("pool speed span", round(rest.speed_dex.min(), 2), 0.22,
     f"while the pool closes {rest.speed_dex.min() * 100:.0f} to "
     f"{rest.speed_dex.max() * 100:.0f} percent of it"),
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
     f"at weights of {closed.w_cex.min():.2f} to {closed.w_cex.max():.2f}"),
    ("six dead tokens", int((d.paired_min < 10).sum()), 6,
     f"sit {'six' if (d.paired_min < 10).sum() == 6 else 'ERR'} tokens whose pools are too close"),
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
     f"the deeper one by {pools.speed_a.abs().min():.2f} to {pools.speed_a.abs().max():.2f} of the gap"),
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
     f"with traded minutes at {spearman(g.dex_liquidity, g.paired_min):.2f}"),
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
     f"lands {lead.error.mean():.2f} above the truth on average"),
    ("calibration scatter low", round(lead.error.min(), 2), -0.33,
     f"from {abs(lead.error.min()):.2f} below the truth"),
    ("calibration scatter high", round(lead.error.max(), 2), 0.28,
     f"to {lead.error.max():.2f} above it"),
    ("ranking recovery clear", round(rank_clear, 2), 0.98,
     f"the right leader {rank_clear * 100:.0f} percent of the time"),
    ("ranking recovery near-even", round(rank_near, 2), 0.92,
     f"falling to {rank_near * 100:.0f} percent where the truth sits near even"),
    # The share of the window with the US equity market shut.
    ("closed share of window", round(closed_share, 2), 0.86,
     f"shut, {closed_share * 100:.0f} percent of the window"),
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
    ("permutation draws and p", int(rel.p_value < 0.0001), 1,
     f"p below {0.0001:g} on twenty thousand draws"),
    # The worked example of the Hasbrouck transformation in the prose. It is
    # arithmetic rather than data, and arithmetic in prose is still a claim.
    ("hasbrouck worked example",
     round(0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2), 2), 0.94,
     f"a weight of {0.8:.2f} corresponds to a share near "
     f"{0.8 ** 2 / (0.8 ** 2 + 0.2 ** 2):.2f}."),
    # Cointegration, tested rather than assumed.
    ("spread stationary count", int(ranked_pairs.spread_stationary.sum()), 7,
     f"**{int(ranked_pairs.spread_stationary.sum())} of {len(ranked_pairs)}** rankable pairs"),
    ("spread half-life span",
     round(ranked_pairs.spread_half_life_min.max(), 1), 3.9,
     f"half-lives of {ranked_pairs.spread_half_life_min.min():.1f} to "
     f"{ranked_pairs.spread_half_life_min.max():.1f} minutes"),
    # The collection registry. Four passes, and the sentence that tells them
    # apart quotes all four of TSLAX's minute counts.
    ("TSLAX across the five passes", int(tslax_counts[-1]), 433,
     "TSLAX shows " + ", ".join(str(n) for n in tslax_counts[:-1])
     + f" and {tslax_counts[-1]} paired minutes"),
    # The cointegrating vector: fitted rather than imposed.
    ("GOOGLX imposed weight",
     round(float(vecrow.loc["GOOGLX"].w_imposed), 2), 1.2,
     f"imposed weight of {float(vecrow.loc['GOOGLX'].w_imposed):.2f}"),
    ("fitted beta span", round(vec.beta.min(), 2), 0.85,
     f"between\n{vec.beta.min():.2f} and {vec.beta.max():.2f}, below one in every pair"),
    ("one inside the bracket", int(vec.one_bracketed.sum()), 7,
     f"and it does in **{int(vec.one_bracketed.sum())} of {len(vec)}** pairs"),
    ("same leader either vector", int(vec.same_leader.sum()), 7,
     f"names the same leader in **{int(vec.same_leader.sum())} of {len(vec)}**"),
    ("largest vector weight move",
     round((vec.w_fitted - vec.w_imposed).abs().max(), 2), 0.2,
     f"largest weight by {(vec.w_fitted - vec.w_imposed).abs().max():.2f}"),
    ("GOOGLX imposed vs fitted",
     round(float(vecrow.loc["GOOGLX"].w_fitted), 2), 1.0,
     f"brings it to {float(vecrow.loc['GOOGLX'].w_fitted):.2f}, a more plausible"),
    # The second estimator.
    ("estimators agree", int(ranked_pairs.agree.sum()), 7,
     f"agrees in **{int(ranked_pairs.agree.sum())} of {len(ranked_pairs)}** pairs"),
    ("innovation correlation",
     round(ranked_pairs.innovation_correlation.median(), 2), 0.39,
     f"correlation is a median {ranked_pairs.innovation_correlation.median():.2f} rather"),
    ("bootstrap lead span", round(ranked_pairs.lead_share.min(), 2), 0.99,
     f"leads in\n{ranked_pairs.lead_share.min() * 100:.0f} to "
     f"{ranked_pairs.lead_share.max() * 100:.0f} percent of resamples"),
    # The staleness bound, read at the ranked pairs' own fill rates.
    ("hold scheme errs at every partial fill",
     round(hold_false[hold_false.index < 1.0].min(), 2), 0.95,
     f"the exchange the leader in **{hold_false[hold_false.index < 1.0].min() * 100:.0f} to "
     f"{hold_false[hold_false.index < 1.0].max() * 100:.0f} percent** of runs"),
    ("hold scheme is right at complete fill", round(hold_false.loc[1.0], 2), 0.0,
     "At complete fill the estimator is right"),
    ("drop scheme bound", round(ranked_risk.false_lead_drop.max(), 2), 0.19,
     f"holds the error to **{ranked_risk.false_lead_drop.min() * 100:.0f} to "
     f"{ranked_risk.false_lead_drop.max() * 100:.0f} percent** on a long base"),
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
    # The lede's joint claim, in both places it is made.
    ("pair-days in the lede", led_days * 100 + pair_days, 2123,
     f"follows in {led_days} of the {pair_days} pair-days that can be ranked"),
    ("pair-days in the description", led_days * 100 + pair_days, 2123,
     f"The exchange leads in {led_days} of {pair_days} rankable pair-days"),
    ("pair-days in the limits section", led_days * 100 + pair_days, 2123,
     f"It rests on {led_days} of {pair_days} pair-days pointing the same way"),
    ("universe volume floor", int(MIN_CEX_VOLUME), 20000,
     f"at least {'twenty thousand' if MIN_CEX_VOLUME == 20000 else 'ERR'} "
     "dollars of 24-hour volume"),
    ("floor is below every kept token",
     int((u.cex_volume_24h >= MIN_CEX_VOLUME).all()), 1,
     "printed at least twenty"),
    ("collision screen pools", len(collisions), 13,
     f"found {len(collisions)} Solana pools answering to "
     f"{collisions.symbol.nunique()} of these tickers"),
    ("collision liquidity negligible",
     int(collisions.claimed_liquidity_usd.max() < 1), 1,
     "Their claimed liquidity was negligible that day"),
    ("ACNX seven minutes",
     int(g.set_index("symbol").loc["ACNX"].paired_min), 7,
     f"whose pool overlapped the exchange tape for "
     f"{'seven' if int(g.set_index('symbol').loc['ACNX'].paired_min) == 7 else 'ERR'} minutes"),
    # Every mint in the universe carries the issuer's vanity prefix; the post
    # says the screen enforced it, so the data has to show it.
    ("mint prefix on every token",
     int(u.mint.str.startswith("Xs").sum()), 24,
     "the vanity prefix Backed uses for its issued mints"),
    ("ranking floor in scope", MIN_PAIRED, 120,
     f"pairs with at least {MIN_PAIRED} paired minutes"),
    ("numerator-only control", round(spearman(g.paired_min, g.cex_volume_24h), 2),
     0.64, f"rank positively with pool activity, at "
     f"{spearman(g.paired_min, g.cex_volume_24h):.2f}"),
    ("panel gate names its thin rows",
     int((allr.minutes < MIN_PAIRED).sum()), 2,
     f"GOOGLX at {int(byrow.loc['GOOGLX'].minutes)} and AMZNX at "
     f"{int(byrow.loc['AMZNX'].minutes)}"),
    ("strict tally", strict_ex * 100 + strict_pool * 10 + strict_near, 1715,
     f"**{strict_ex} pair-days are clear exchange leads, {strict_pool} is a "
     f"clear pool lead, and {strict_near} are unclassified**"),
    ("matched-length staleness",
     round(float((matched_1000_12.w_cex > 0.5).mean()), 2), 0.42,
     f"error to about {float((matched_1000_50.w_cex > 0.5).mean()) * 100:.0f} "
     f"percent at half fill and "
     f"{float((matched_1000_12.w_cex > 0.5).mean()) * 100:.0f} percent at an eighth"),
    # The daily replication, three days in.
    ("registry row, second day", len(day2_coverage), 25,
     f"| next day | 30 July, two sessions | {len(day2_coverage)} |"),
    ("registry row, third day", len(day3_coverage), 24,
     f"| third day | 31 July, two sessions | {len(day3_coverage)} |"),
    ("second-day correlation", round(day2.rho, 2), -0.93,
     f"prints {day2.rho:.2f} on {int(day2.tokens)} tokens on the second day"),
    ("third-day correlation", round(day3.rho, 2), -0.93,
     f"**{day3.rho:.2f}** on {int(day3.tokens)} on the third"),
    ("both later days significant",
     int(day2.p_value < 0.0001 and day3.p_value < 0.0001), 1,
     "each with a permutation p below 0.0001"),
    ("third-day tail check", round(day3.rho_trimmed, 2), -0.92,
     f"leaves the third day at {day3.rho_trimmed:.2f} on "
     f"{int(day3.trimmed_tokens)} tokens"),
    ("third-day liquidity rank", round(day3.rho_liquidity, 2), 0.9,
     f"ranks with pool activity at {day3.rho_liquidity:.2f}"),
    ("multi-window leaders", int(both_windows.led_every_window.sum()), 7,
     f"{'Seven' if both_windows.led_every_window.sum() == 7 else 'ERR'} of the "
     f"{'eight' if len(both_windows) == 8 else 'ERR'} tokens rankable in more "
     "than one window"),
    ("second-day rankable", len(day2_ranked), 9,
     f"ranks nine and the exchange leads all nine, at a sign-test p of "
     f"{sign_test(int((day2_ranked.w_cex > 0.5).sum()), len(day2_ranked)):.4f}"),
    ("third-day split", int((day3_ranked.w_cex > 0.5).sum()), 5,
     f"{'five of seven' if (day3_ranked.w_cex > 0.5).sum() == 5 and len(day3_ranked) == 7 else 'ERR'}"),
    ("TSLAX third day", round(float(day3_ranked.loc["TSLAX"].w_cex), 2), 0.47,
     f"TSLAX prints {float(day3_ranked.loc['TSLAX'].w_cex):.2f} on the third "
     "day after 0.89 and 0.92"),
    ("TSLAX third-day exchange speed",
     round(abs(float(day3_ranked.loc["TSLAX"].speed_cex)), 2), 0.21,
     f"correcting meaningfully, at "
     f"{abs(float(day3_ranked.loc['TSLAX'].speed_cex)):.2f} of the gap per minute"),
    ("AMZNX pool lead", round(float(day3_ranked.loc["AMZNX"].w_cex), 2), -0.24,
     f"prints a weight of {float(day3_ranked.loc['AMZNX'].w_cex):.2f} with the "
     "pool ahead in"),
    ("AMZNX bootstrap",
     round(100 - float(day3_ranked.loc["AMZNX"].lead_share) * 100), 98,
     f"pool ahead in {100 - float(day3_ranked.loc['AMZNX'].lead_share) * 100:.0f} "
     "percent of bootstrap resamples"),
    ("GLDX across days",
     round(float(day3_ranked.loc["GLDX"].w_cex), 2), 0.67,
     f"GLDX repeats at "
     f"{float(day2_ranked.set_index('symbol').loc['GLDX'].w_cex):.2f} and "
     f"{float(day3_ranked.loc['GLDX'].w_cex):.2f} across its two days"),
    ("METAX second day",
     round(float(day2_ranked.set_index("symbol").loc["METAX"].w_cex), 2), 0.57,
     f"METAX printed "
     f"{float(day2_ranked.set_index('symbol').loc['METAX'].w_cex):.2f} on the "
     "second day, the one pair where the estimators disagreed"),
    ("METAX went silent",
     int(day2_coverage.set_index("symbol").loc["METAX"].paired_minutes), 142,
     f"after {int(day2_coverage.set_index('symbol').loc['METAX'].paired_minutes)} "
     "paired minutes the day before"),
    ("unpaired counts by day",
     (len(day2_universe) - len(day2_coverage)) * 10
     + (len(day3_universe) - len(day3_coverage)), 23,
     f"numbered {'two' if len(day2_universe) - len(day2_coverage) == 2 else 'ERR'} "
     f"on the second day and "
     f"{'three' if len(day3_universe) - len(day3_coverage) == 3 else 'ERR'} on the third"),
    ("one-minute pairings",
     int(day3_coverage.set_index("symbol").loc[["ABTX", "PMX"]].paired_minutes.max()),
     1, "ABTX and PMX, paired for the first time on the third day"),
    # Out-of-sample.
    ("replication count", int(rep.leads_both.sum()), 7,
     f"In this pass {'seven of seven' if rep.leads_both.sum() == 7 else 'ERR'} "
     "point the same way"),
    ("sign test p-value", round(float(sign_test(len(ranked_pairs), len(ranked_pairs))), 4), 0.0156,
     f"p = {sign_test(len(ranked_pairs), len(ranked_pairs)):.4f}"),
    ("replication drift", round((rep.w_second - rep.w_first).abs().max(), 2), 0.11,
     f"weights moving by at most {(rep.w_second - rep.w_first).abs().max():.2f}"),
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
# The robustness table carries seven tokens across seven columns, all of it
# hand-typed from robustness_<label>.csv. A mutation sweep found every cell of it
# unguarded, which is the same hole the four tables above had.
robust_table = [
    [r.symbol, str(int(r.paired_minutes)), f"{r.fill_rate:.0%}",
     f"{r.w_cex:.2f}", f"{r.hasbrouck_low:.2f} to {r.hasbrouck_high:.2f}",
     f"{r.lead_share:.0%}", f"{r.spread_half_life_min:.1f}"]
    for r in ranked_pairs.itertuples()
]

# The post directory carries its own copy of every dataset behind a figure or
# table, per the wiki's in-directory rule. A copy can drift; a byte comparison
# cannot lie about it.
from analysis.build_analysis import POST_DATA  # noqa: E402

mirror_bad = 0
for name in POST_DATA:
    canonical = (base / "data" / name)
    mirrored = (base / "post" / "data" / name)
    if not mirrored.exists():
        print(f"  [POST] post/data/{name} is missing")
        mirror_bad += 1
    elif mirrored.read_bytes() != canonical.read_bytes():
        print(f"  [POST] post/data/{name} has drifted from data/{name}")
        mirror_bad += 1

bad = mirror_bad
searched = len(POST_DATA)
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
    ("robustness table",
     ("token", "paired minutes", "pool fill", "GG weight",
      "Hasbrouck bounds", "bootstrap lead", "spread half-life"),
     robust_table),
    ("cross-window table",
     ("token", "29 July", "30 July", "31 July", "span"),
     [[sym,
       f"{r['2026-07-29b']:.2f}" if pd.notna(r['2026-07-29b']) else "-",
       f"{r['2026-07-30']:.2f}" if pd.notna(r['2026-07-30']) else "-",
       f"{r['2026-07-31']:.2f}" if pd.notna(r['2026-07-31']) else "-",
       f"{r.spread_across_windows:.2f}"]
      for sym, r in both_windows.iterrows()]),
)
for name, header, expected in tables:
    searched += sum(len(r) for r in expected)
    bad += check_table(name, header, expected)

flat_post = _flat(post)
for label, got, want, text in checks:
    drift = abs(got - want) > 0.011
    missing = _flat(text) not in flat_post
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
        if value not in flat_post:
            print(f"  [POST] {token}: {value} not found in post")
            bad += 1

print(f" searched {searched} claims against {len(post.splitlines())} lines of post")
print(f"FAILED: {bad}")
# Exit non-zero on any failure. Without this the CI step and the README
# reproduce flow both pass whatever the numbers say.
sys.exit(1 if bad else 0)
