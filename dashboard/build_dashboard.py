"""Render the findings as a single self-contained page.

The page reads nothing at runtime: every number is baked in from the committed
CSVs at build time, so what a reader sees is what `analysis/verify.py` checks.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
# Same reason as analysis/calibrate.py: run from the repository root, the
# script's own directory lands on the path rather than the root.
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.relation import spearman  # noqa: E402

DATA = BASE / "data"

__all__ = ["build"]

TEMPLATE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>xStocks price discovery</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 0 auto; max-width: 60rem; padding: 2.5rem 1.25rem 4rem;
         font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         color: #1a1a1a; }}
  h1 {{ font-size: 1.6rem; line-height: 1.25; margin: 0 0 .4rem; }}
  p.sub {{ color: #666; margin: 0 0 2rem; }}
  .cards {{ display: grid; gap: 1rem;
            grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
            margin-bottom: 2.5rem; }}
  .card {{ border: 1px solid #e3e3e3; border-radius: .6rem; padding: 1rem 1.1rem; }}
  .card b {{ display: block; font-size: 1.75rem; font-weight: 600;
             letter-spacing: -.02em; }}
  .card span {{ color: #666; font-size: .85rem; }}
  .card.flag b {{ color: #b3261e; }}
  h2 {{ font-size: 1.05rem; margin: 2.2rem 0 .6rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
  th, td {{ text-align: right; padding: .4rem .55rem;
            border-bottom: 1px solid #ececec; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ color: #666; font-weight: 500; }}
  figure {{ margin: 1.2rem 0 0; }}
  img {{ width: 100%; border: 1px solid #ececec; border-radius: .4rem; }}
  footer {{ margin-top: 3rem; color: #666; font-size: .85rem; }}
  code {{ background: #f5f5f5; padding: .1rem .3rem; border-radius: .2rem; }}
</style>
<h1>Tokenized stocks are priced on the exchange</h1>
<p class="sub">{n_tokens} xStocks quoted at once on Gate and on Solana pools,
29 July 2026. The quieter the chain, the more the exchange prints against it.</p>

<div class="cards">
  <div class="card"><b>{rho}</b><span>rank correlation between on-chain
    minutes traded and exchange dollars per on-chain dollar</span></div>
  <div class="card"><b>{led}/{ranked}</b><span>rankable pairs where the
    exchange leads price discovery</span></div>
  <div class="card flag"><b>{dead}</b><span>tokens whose pool traded in under
    ten minutes while the exchange printed five and six figures</span></div>
  <div class="card"><b>{ratio_max:,.0f}x</b><span>highest exchange volume per
    on-chain dollar, VTIX</span></div>
</div>

<h2>Who leads, and by how much each side corrects</h2>
{weights_table}
<figure><img src="post/weights.png" alt="Exchange weights and correction speeds"></figure>

<h2>The relation across the whole universe</h2>
<figure><img src="post/relation.png" alt="On-chain minutes against exchange dollars per on-chain dollar"></figure>

<h2>The tokens with nothing to check them against</h2>
{dead_table}

<footer>Every figure regenerates from the committed CSVs with
<code>python analysis/build_analysis.py</code>, and every number in the write-up
is re-checked against them by <code>python analysis/verify.py</code>.</footer>
</html>
"""


def _table(frame: pd.DataFrame, headers: list[str]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for _, row in frame.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row)
        body += f"<tr>{cells}</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build() -> Path:
    groups = pd.read_csv(DATA / "token_groups.csv")
    panel = pd.read_csv(DATA / "panel_sessions.csv")
    allr = (panel[panel.regime == "all"].dropna(subset=["w_cex"])
            .sort_values("w_cex", ascending=False))
    dead = groups[groups.group == "no on-chain market"].sort_values("paired_min")

    weights = pd.DataFrame({
        "token": allr.symbol,
        "exchange weight": allr.w_cex.map("{:.2f}".format),
        "exchange corrects": allr.speed_cex.map("{:+.2f}".format),
        "pool corrects": allr.speed_dex.map("{:.2f}".format),
        "paired minutes": allr.minutes.astype(int),
    })
    dead_rows = pd.DataFrame({
        "token": dead.symbol,
        "minutes the pool traded": dead.paired_min.astype(int),
        "exchange 24h": dead.cex_volume_24h.map("${:,.0f}".format),
        "on-chain 24h": dead.dex_volume_24h.map("${:,.0f}".format),
        "on-chain liquidity": dead.dex_liquidity.map("${:,.0f}".format),
    })

    html = TEMPLATE.format(
        n_tokens=len(groups),
        rho=f"{spearman(groups.paired_min, groups.ratio):.2f}",
        led=int((allr.w_cex > 0.5).sum()),
        ranked=len(allr),
        dead=len(dead),
        ratio_max=groups.ratio.max(),
        weights_table=_table(weights, list(weights.columns)),
        dead_table=_table(dead_rows, list(dead_rows.columns)),
    )
    out = BASE / "index.html"
    out.write_text(html)
    return out


if __name__ == "__main__":
    print(f"wrote {build().relative_to(BASE)}")
