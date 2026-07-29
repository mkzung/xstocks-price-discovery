"""Machine-check every quantitative claim in the post against the committed CSVs.

Run this after any change to the data or the text. It reads the numbers back
out of the CSVs rather than out of the analysis in memory, so a stale table
carried over from an earlier run fails here rather than in review.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from analysis.relation import spearman

base = Path("/Users/mkzung/Max/Max/xstocks-price-discovery")
u = pd.read_csv(base / "data" / "universe.csv")
d = pd.read_csv(base / "data" / "panel_run1.csv")
p = pd.read_csv(base / "data" / "panel_sessions.csv")
m = pd.read_csv(base / "data" / "venue_matrix.csv")
g = pd.read_csv(base / "data" / "token_groups.csv")
post = (base / "POST.md").read_text()

u["ratio"] = u.cex_volume_24h / u.dex_volume_24h.clip(lower=1)
allr = p[p.regime == "all"].dropna(subset=["w_cex"])
closed = p[p.regime == "closed"].dropna(subset=["w_cex"])
rest = allr[allr.symbol != "AMZNX"]
gap = p.pivot_table(index="symbol", columns="regime",
                    values="mean_gap_pct").dropna(subset=["open", "closed"])

checks = [
    ("24 tokens", len(u), 24),
    ("max ratio 7311", round(u.ratio.max()), 7311),
    ("min ratio 0.16", round(u.ratio.min(), 2), 0.16),
    ("median 6.8", round(u.ratio.median(), 1), 6.8),
    ("nine rankable", len(allr), 9),
    ("all CEX-led", int((allr.w_cex > 0.5).all()), 1),
    ("four weights >1", int((allr.w_cex > 1).sum()), 4),
    ("eight-pair cex speed <=0.08", round(rest.speed_cex.abs().max(), 2), 0.08),
    ("pool speed 0.22", round(rest.speed_dex.min(), 2), 0.22),
    ("pool speed 0.74", round(rest.speed_dex.max(), 2), 0.74),
    ("four wrong-way", int((allr.speed_cex > 0).sum()), 4),
    ("AMZNX speed 0.35", round(allr.set_index('symbol').loc['AMZNX'].speed_cex, 2), -0.35),
    ("AMZNX weight 0.63", round(allr.set_index('symbol').loc['AMZNX'].w_cex, 2), 0.63),
    ("closed rankable 8", len(closed), 8),
    ("closed all led", int((closed.w_cex > 0.5).all()), 1),
    ("closed min 0.96", round(closed.w_cex.min(), 2), 0.96),
    ("closed max 1.24", round(closed.w_cex.max(), 2), 1.24),
    ("gap open 0.08", round(gap["open"].abs().mean(), 2), 0.08),
    ("gap closed 0.12", round(gap["closed"].abs().mean(), 2), 0.12),
    ("gap five tokens", len(gap), 5),
    ("six dead tokens", int((d.paired_min < 10).sum()), 6),
    ("bybit weight 0.75",
     round(m[m.venue_a == "bybit"].dropna(subset=["weight_a"]).iloc[0].weight_a, 2), 0.75),
    ("bybit minutes 498",
     int(m[m.venue_a == "bybit"].dropna(subset=["weight_a"]).iloc[0].minutes), 498),
    ("bybit speed -0.09",
     round(m[m.venue_a == "bybit"].dropna(subset=["weight_a"]).iloc[0].speed_a, 2), -0.09),
    ("bybit pool speed 0.28",
     round(m[m.venue_a == "bybit"].dropna(subset=["weight_a"]).iloc[0].speed_b, 2), 0.28),
    ("pool-pair weight min 0.06",
     round(m[m.venue_a == "pool_deep"].dropna(subset=["weight_a"]).weight_a.min(), 2), 0.06),
    ("pool-pair weight max 0.43",
     round(m[m.venue_a == "pool_deep"].dropna(subset=["weight_a"]).weight_a.max(), 2), 0.43),
    ("pool-pair speed min 0.58",
     round(m[m.venue_a == "pool_deep"].dropna(subset=["weight_a"]).speed_a.abs().min(), 2), 0.58),
    ("pool-pair speed max 0.88",
     round(m[m.venue_a == "pool_deep"].dropna(subset=["weight_a"]).speed_a.abs().max(), 2), 0.88),
    ("groups cover all 24", len(g), 24),
    ("ranked group 9", int((g.group == "ranked").sum()), 9),
    ("thin group 9", int((g.group == "thin").sum()), 9),
    ("dead group 6", int((g.group == "no on-chain market").sum()), 6),
    ("ranked median ratio 1.1",
     round(g[g.group == "ranked"].ratio.median(), 1), 1.1),
    ("thin median ratio 12.1",
     round(g[g.group == "thin"].ratio.median(), 1), 12.1),
    ("dead median ratio 2056",
     round(g[g.group == "no on-chain market"].ratio.median()), 2056),
    ("ranked median minutes 217",
     int(g[g.group == "ranked"].paired_min.median()), 217),
    ("thin median minutes 23",
     int(g[g.group == "thin"].paired_min.median()), 23),
    ("dead median minutes 4",
     int(g[g.group == "no on-chain market"].paired_min.median()), 4),
    ("thin minutes span 11 to 73",
     int(g[g.group == "thin"].paired_min.min()) * 100
     + int(g[g.group == "thin"].paired_min.max()), 1173),
    ("spearman -0.93", round(spearman(g.paired_min, g.ratio), 2), -0.93),
    ("spearman trimmed -0.92",
     round(spearman(*[c.reset_index(drop=True) for c in
                      (g.sort_values("ratio").iloc[:-6].paired_min,
                       g.sort_values("ratio").iloc[:-6].ratio)]), 2), -0.92),
    ("liquidity rank 0.92",
     round(spearman(g.dex_liquidity, g.paired_min), 2), 0.92),
    ("AMZNX thinnest ranked 79",
     int(g[g.group == "ranked"].paired_min.min()), 79),
]
bad = 0
for label, got, want in checks:
    ok = abs(got - want) <= 0.011
    bad += not ok
    print(f"  [{'OK ' if ok else 'BAD'}] {label}: got {got} want {want}")

for token in ("VTIX", "ACNX", "NFLXX", "AZNX", "TQQQX", "KOX", "MSTRX",
              "TSLAX", "CRCLX", "NVDAX", "QQQX"):
    row = u[u.symbol == token].iloc[0]
    for value in (f"${row.cex_volume_24h:,}", f"${row.dex_volume_24h:,}"):
        if value not in post:
            print(f"  [BAD] {token}: {value} not found in post")
            bad += 1
print(f"\nFAILED: {bad}")
