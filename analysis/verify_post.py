"""Machine-check every quantitative claim in the post against the committed CSVs.

Run this after any change to the data or the text. It reads the numbers back
out of the CSVs rather than out of the analysis in memory, so a stale table
carried over from an earlier run fails here rather than in review.
"""
from pathlib import Path

import pandas as pd

base = Path("/Users/mkzung/Max/Max/xstocks-price-discovery")
u = pd.read_csv(base / "data" / "universe.csv")
d = pd.read_csv(base / "data" / "panel_run1.csv")
p = pd.read_csv(base / "data" / "panel_sessions.csv")
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
