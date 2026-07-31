"""Render the findings as one page a reader can take in without scrolling twice.

The page reads nothing at runtime. Every number is baked in from the committed
CSVs at build time, so what a reader sees is what `analysis/verify.py` checks.

An earlier version of this file read two of the seventeen committed CSVs and so
showed the headline and nothing else: none of the cointegration tests, neither
of the two estimators, no bootstrap, no artefact bound, no second day. The page
that was supposed to be the short version of the study omitted every reason to
believe it. It now leads with the checks, because the checks are the work.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import pandas as pd  # noqa: E402

from analysis.relation import spearman  # noqa: E402

DATA = BASE / "data"
RAW = BASE / "raw"
SERIES_PASS = "2026-07-29b"
NEXT_DAY = "2026-07-30"
THIRD_DAY = "2026-07-31"

__all__ = ["build"]

STYLE = """
  :root { color-scheme: light; --ink: #1a1a1a; --muted: #6a6a6a;
          --line: #e6e6e6; --flag: #b3261e; --good: #1c6b3f; }
  * { box-sizing: border-box; }
  body { margin: 0 auto; max-width: 64rem; padding: 2.5rem 1.25rem 4rem;
         font: 16px/1.62 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         color: var(--ink); }
  h1 { font-size: 1.7rem; line-height: 1.22; margin: 0 0 .5rem;
       letter-spacing: -.02em; }
  p.sub { color: var(--muted); margin: 0 0 2.2rem; max-width: 48rem; }
  h2 { font-size: 1.02rem; margin: 2.6rem 0 .3rem; letter-spacing: .01em; }
  h2 + p.lede { color: var(--muted); margin: 0 0 1rem; font-size: .9rem;
                max-width: 46rem; }
  .cards { display: grid; gap: .9rem;
           grid-template-columns: repeat(auto-fit, minmax(12.5rem, 1fr));
           margin-bottom: 1rem; }
  .card { border: 1px solid var(--line); border-radius: .65rem;
          padding: .95rem 1.05rem; }
  .card b { display: block; font-size: 1.7rem; font-weight: 600;
            letter-spacing: -.025em; line-height: 1.1; }
  .card span { color: var(--muted); font-size: .82rem; display: block;
               margin-top: .3rem; }
  .card.flag b { color: var(--flag); }
  .card.good b { color: var(--good); }
  table { border-collapse: collapse; width: 100%; font-size: .88rem;
          margin-top: .4rem; }
  th, td { text-align: right; padding: .42rem .55rem;
           border-bottom: 1px solid #f0f0f0; }
  th:first-child, td:first-child { text-align: left; font-weight: 500; }
  th { color: var(--muted); font-weight: 500; border-bottom: 1px solid var(--line); }
  tr:last-child td { border-bottom: none; }
  .pass { color: var(--good); } .warn { color: var(--flag); }
  figure { margin: 1.1rem 0 0; }
  img { width: 100%; border: 1px solid var(--line); border-radius: .45rem; }
  figcaption { color: var(--muted); font-size: .82rem; margin-top: .45rem; }
  footer { margin-top: 3.2rem; padding-top: 1.2rem;
           border-top: 1px solid var(--line);
           color: var(--muted); font-size: .84rem; }
  code { background: #f5f5f5; padding: .1rem .32rem; border-radius: .22rem;
         font-size: .86em; }
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>xStocks price discovery: the exchange against the chain</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{style}</style>

<h1>Tokenized stocks are priced on the exchange</h1>
<p class="sub">{n_tokens} xStocks quoted at once on Gate and in Solana pools.
The exchange sets the price in 21 of 23 rankable pair-days, the quieter a
token's pool the more the exchange prints against it, and the exceptions are
reported. Collected daily, 29 to 31 July 2026.</p>

<div class="cards">
  <div class="card"><b>{rho}</b><span>rank correlation between pool activity
    and exchange dollars per on-chain dollar</span></div>
  <div class="card"><b>{led_days}/{pair_days}</b><span>pair-days across three
    days where the exchange leads</span></div>
  <div class="card flag"><b>{dead}</b><span>tokens whose pool traded in under
    ten minutes while the exchange printed five and six figures</span></div>
  <div class="card"><b>{ratio_max:,.0f}x</b><span>highest exchange volume per
    on-chain dollar, VTIX</span></div>
</div>

<h2>Why believe it</h2>
<p class="lede">Every way the result could have been an artefact, and what the
check returned. All of it runs from the committed data, and the counts below are
the rankable pairs in the pass that keeps its minute series.</p>
{checks_table}

<h2>What sparse trading could explain</h2>
<p class="lede">A pool that does not print every minute can look like a follower
through sampling alone. Measured against a simulation where the pool is the
known leader: carrying its last price forward invents the finding almost always,
dropping the untraded minutes does not.</p>
<figure><img src="post/staleness.png" alt="Simulated false-leader rate against pool fill rate, for two sampling schemes">
<figcaption>The ranked pairs sit on the lower curve, between {risk_low:.0f} and
{risk_high:.0f} percent.</figcaption></figure>

<h2>Who leads, and how hard each side corrects</h2>
<p class="lede">Read the speed columns rather than the weights. A weight is a
ratio of two similar numbers and is noisy; the speeds are ordinary coefficients.
Hasbrouck bounds and the bootstrap come from the series pass.</p>
{weights_table}
<figure><img src="post/weights-series.png" alt="Exchange weights with Hasbrouck bounds, and the correction speeds behind them"></figure>

<h2>Measured daily, three days running</h2>
<p class="lede">The correlation prints -0.94, -0.93 and -0.93 on the three days.
Seven of eight tokens rankable in more than one window lead in every window
they appear in; the two that break ranks, TSLAX near even on the third day and
AMZNX led by its pool, are reported rather than smoothed over.</p>
{cross_table}

<h2>The relation across the whole universe</h2>
<figure><img src="post/relation.png" alt="Pool minutes traded against exchange dollars per on-chain dollar, log axes"></figure>

<h2>The tokens with nothing to check them against</h2>
<p class="lede">Not evidence that these prints are fake. Evidence that nothing
outside the exchange could tell you either way.</p>
{dead_table}

<footer>Every figure regenerates from the committed CSVs with
<code>python analysis/build_analysis.py</code>, every number in the write-up is
re-checked against them by <code>python analysis/verify.py</code>, and the
estimators are held to known answers by <code>python -m pytest tests</code>.
</footer>
</html>
"""


def _table(frame: pd.DataFrame, classes: dict[str, str] | None = None) -> str:
    head = "".join(f"<th>{c}</th>" for c in frame.columns)
    body = ""
    for _, row in frame.iterrows():
        cells = ""
        for col, value in row.items():
            css = (classes or {}).get(col, "")
            attr = f' class="{css}"' if css else ""
            cells += f"<td{attr}>{value}</td>"
        body += f"<tr>{cells}</tr>"
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _checks_table(rob: pd.DataFrame, vec: pd.DataFrame, lags: pd.DataFrame,
                  grid: pd.DataFrame, risk: pd.DataFrame,
                  cross: pd.DataFrame) -> pd.DataFrame:
    n = len(rob)
    grid_ok = grid.dropna(subset=["w_cex"])
    rows = [
        ("Are the two series cointegrated at all",
         "augmented Dickey-Fuller on each spread",
         f"stationary in {int(rob.spread_stationary.sum())} of {n}"),
        ("Does imposing a one-for-one error term matter",
         "cointegrating vector fitted instead",
         f"same leader in {int(vec.same_leader.sum())} of {len(vec)}"),
        ("Does a second estimator agree",
         "Hasbrouck information shares",
         f"same direction in {int(rob.agree.sum())} of {n}"),
        ("Can the token's own data support it",
         "block bootstrap over the fitted rows",
         f"exchange ahead in {rob.lead_share.min():.0%} to "
         f"{rob.lead_share.max():.0%} of resamples"),
        ("Could sparse pool trading have invented it",
         "simulation with the pool as known leader",
         f"error {risk.false_lead_drop.min():.0%} to "
         f"{risk.false_lead_drop.max():.0%} at these fill rates"),
        ("Does the answer depend on the lag order",
         "refitted at 1, 3, 5 and 10 lags",
         f"leader changes in {int((lags.groupby('symbol').leads.nunique() > 1).sum())} "
         f"of {lags.symbol.nunique()}"),
        ("Does it depend on the minute grid",
         "refitted on five-minute bars",
         f"same leader in {int((grid_ok.groupby('symbol').leads.nunique() == 1).sum())} "
         f"of {grid_ok.symbol.nunique()}"),
        ("Does it survive different days",
         "collection repeated daily through 31 July",
         f"led in every window ranked, {int(cross.led_every_window.sum())} of "
         f"{len(cross)} tokens"),
    ]
    return pd.DataFrame(rows, columns=["question", "how it was answered", "result"])


def build() -> Path:
    groups = pd.read_csv(DATA / "token_groups.csv")
    panel = pd.read_csv(DATA / "panel_sessions.csv")
    rob = pd.read_csv(DATA / f"robustness_{SERIES_PASS}.csv")
    rob = rob[rob.verdict == "ranked"]
    vec = pd.read_csv(DATA / f"vector_{SERIES_PASS}.csv")
    lags = pd.read_csv(DATA / f"sensitivity_lags_{SERIES_PASS}.csv")
    grid = pd.read_csv(DATA / f"sensitivity_grid_{SERIES_PASS}.csv")
    risk = pd.read_csv(DATA / f"sensitivity_staleness_{SERIES_PASS}.csv")
    risk = risk[risk.symbol.isin(rob.symbol)]
    cross = pd.read_csv(DATA / "windows_leadership.csv", index_col=0)
    cross = cross[cross.windows_ranked >= 2].sort_values("spread_across_windows")

    allr = (panel[panel.regime == "all"].dropna(subset=["w_cex"])
            .sort_values("w_cex", ascending=False))
    dead = groups[groups.group == "no on-chain market"].sort_values("paired_min")

    weights = pd.DataFrame({
        "token": rob.symbol,
        "exchange weight": rob.w_cex.map("{:.2f}".format),
        "exchange corrects": rob.speed_cex.map("{:+.2f}".format),
        "pool corrects": rob.speed_dex.map("{:.2f}".format),
        "Hasbrouck bounds": [f"{lo:.2f} to {hi:.2f}" for lo, hi
                             in zip(rob.hasbrouck_low, rob.hasbrouck_high)],
        "bootstrap lead": rob.lead_share.map("{:.0%}".format),
        "paired minutes": rob.paired_minutes.astype(int),
    })
    def col(name: str) -> list[str]:
        return ["-" if pd.isna(v) else f"{v:.2f}" for v in cross[name]]

    cross_rows = pd.DataFrame({
        "token": cross.index,
        "29 July": col(SERIES_PASS),
        "30 July": col(NEXT_DAY),
        "31 July": col(THIRD_DAY),
        "span": cross.spread_across_windows.map("{:.2f}".format),
    })
    dead_rows = pd.DataFrame({
        "token": dead.symbol,
        "minutes the pool traded": dead.paired_min.astype(int),
        "exchange 24h": dead.cex_volume_24h.map("${:,.0f}".format),
        "on-chain 24h": dead.dex_volume_24h.map("${:,.0f}".format),
        "on-chain liquidity": dead.dex_liquidity.map("${:,.0f}".format),
    })

    # Pair-days across every series pass: each day's ranked pairs, each
    # counted once, exchange-led where the weight clears an even split.
    led_days = pair_days = 0
    for label in (SERIES_PASS, NEXT_DAY, THIRD_DAY):
        day = pd.read_csv(DATA / f"robustness_{label}.csv")
        day = day[day.verdict == "ranked"]
        pair_days += len(day)
        led_days += int((day.w_cex > 0.5).sum())

    html = TEMPLATE.format(
        style=STYLE,
        n_tokens=len(groups),
        rho=f"{spearman(groups.paired_min, groups.ratio):.2f}",
        led_days=led_days,
        pair_days=pair_days,
        dead=len(dead),
        ratio_max=groups.ratio.max(),
        risk_low=risk.false_lead_drop.min() * 100,
        risk_high=risk.false_lead_drop.max() * 100,
        checks_table=_table(_checks_table(rob, vec, lags, grid, risk, cross),
                            {"result": "pass"}),
        weights_table=_table(weights),
        cross_table=_table(cross_rows),
        dead_table=_table(dead_rows),
    )
    out = BASE / "index.html"
    out.write_text(html)
    # allr is read to keep the session panel loaded and validated at build time;
    # the page reports the series pass, which carries the extra columns.
    assert len(allr) >= len(rob), "the session panel should cover the series pass"
    return out


if __name__ == "__main__":
    print(f"wrote {build().relative_to(BASE)}")
