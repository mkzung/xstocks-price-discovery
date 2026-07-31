# xStocks price discovery: the exchange against the chain

[![tests](https://github.com/mkzung/xstocks-price-discovery/actions/workflows/test.yml/badge.svg)](https://github.com/mkzung/xstocks-price-discovery/actions/workflows/test.yml)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

The findings render as a single page at
[mkzung.github.io/xstocks-price-discovery](https://mkzung.github.io/xstocks-price-discovery/),
built from the committed CSVs by `python dashboard/build_dashboard.py`.

A tokenized equity trades at once on a centralised order book and in a Solana
pool, on the same issuer's mint, with arbitrage tying the two quotes together.
That makes it possible to ask which venue actually sets the price, and to check
an exchange's tape against something outside the exchange.

`post/index.md` is the write-up and `index.html` is the same findings on one
page. Everything in both is reproducible from this repository, and
`analysis/verify.py` fails if a number in the text stops matching the data.

## What is here

| path | what it does |
|------|--------------|
| `analysis/discovery.py` | Gonzalo-Granger weights and Hasbrouck information shares, plus a simulator whose answer is fixed by construction |
| `analysis/collect.py` | builds the paired universe and pulls minute bars from both venues |
| `analysis/collect_raw.py` | keeps the paired minute series themselves under `raw/<run>/`, with per-token fill rates and gap structure |
| `analysis/panel.py` | runs the estimator per token, whole window and split by US session |
| `analysis/venues.py` | the controls: a second exchange, and two pools on one mint |
| `analysis/cointegration.py` | the augmented Dickey-Fuller test on each pair's spread, which the model needs and the first draft assumed |
| `analysis/bootstrap.py` | block bootstrap over the fitted regression rows, and the exact binomial for the joint result |
| `analysis/staleness.py` | whether sparse pool trading can invent the finding, measured against a known answer |
| `analysis/robustness.py` | every check above applied to one collection run |
| `analysis/sensitivity.py` | lag order, sampling grid, per-token artefact risk, and the second window against the first |
| `analysis/vector.py` | whether imposing a cointegrating vector of one to minus one changes any conclusion |
| `analysis/windows.py` | the headline correlation and the per-token leadership, recomputed inside each collection day |
| `analysis/calibrate.py` | what the estimator does to an answer it already knows |
| `analysis/collisions.py` | records the ticker collisions the universe screen filters out |
| `analysis/relation.py` | the rank correlation behind the grouping, with a permutation test |
| `analysis/verify.py` | reads every number in `post/index.md` back out of the CSVs |
| `analysis/check_post.py` | the post's formatting, spelling and link rules |
| `analysis/format_post.py` | settles the line wrapping, so phrase checks stop moving under the text |
| `analysis/build_analysis.py` | redraws every figure from `data/` |
| `tests/` | holds every estimator to an answer it was not told |
| `data/` | the exact outputs behind every figure in the post |
| `post/data/` | the same datasets mirrored beside the article, per the wiki's in-directory convention; verify.py fails if the copy drifts |
| `raw/` | the paired minute series, so fill rates and spreads can be rechecked |
| `dashboard/build_dashboard.py` | rebuilds `index.html`, the single-page view of the findings |

## Reproducing

```bash
pip install -r requirements.txt
python -m pytest tests -q                     # every estimator recovers a known answer
python analysis/verify.py                     # every number in the post, checked against data/
python analysis/calibrate.py                  # what the fit does to a known answer
python analysis/staleness.py                  # whether sparse trading can invent the finding
python analysis/robustness.py 2026-07-29b     # cointegration, Hasbrouck, bootstrap, per token
python analysis/sensitivity.py 2026-07-29b    # lags, grid, artefact risk, second window
python analysis/vector.py 2026-07-29b         # imposed vector against fitted
python analysis/robustness.py 2026-07-30      # the second collection day
python analysis/vector.py 2026-07-30          # its cointegrating vector
python analysis/robustness.py 2026-07-31      # the third collection day
python analysis/vector.py 2026-07-31          # its cointegrating vector
python analysis/windows.py 2026-07-29b 2026-07-30 2026-07-31  # what survives the calendar
python analysis/build_analysis.py             # redraw the figures
python analysis/format_post.py --check        # wrapping is settled
python analysis/check_post.py                 # formatting, spelling, links
```

To collect a new window, which becomes its own directory under `raw/` rather
than overwriting anything:

```bash
python analysis/collect_raw.py 2026-08-01 --refresh-universe
```

The `--refresh-universe` flag snapshots the paired universe and its 24-hour
volumes into that run's directory, and puts `data/universe.csv` back afterwards,
because the published volume figures are keyed to the committed snapshot.
Collection takes the better part of an hour and can lose its network part way
through, in which case the run finishes with fewer tokens and says so in
`coverage.csv`.

To rebuild the original panel, in this order:

```python
from analysis.collect import build_universe
from analysis.panel import run_panel
from analysis.venues import run_venue_matrix
from analysis.relation import build_groups

build_universe()        # data/universe.csv
run_panel()             # data/panel_sessions.csv, about 55 minutes
run_venue_matrix()      # data/venue_matrix.csv
build_groups(rankable)  # data/token_groups.csv
```

Both data sources are free and need no key. GeckoTerminal rate-limits hard, so
`collect._get` backs off on 429 and the panel sleeps between tokens; a full
pass over the universe takes the better part of an hour.

## Reading the numbers

The estimator was calibrated against a simulator with a known answer. Run
`python analysis/calibrate.py` to reproduce it; the committed result is
`data/calibration.csv`.

Read a single weight as weak evidence. The fit sits 0.03 above the truth on
average, so weights slightly above one are the bias rather than a real reading,
and a single run lands anywhere from 0.33 below the truth to 0.28 above it
across the whole grid. What holds up is the ordering: the estimator picks the
right leader in 98 percent of runs where the true weight is plainly one-sided,
92 percent where it is near even. The post therefore leans on the pattern
across pairs and days and on the correction speeds, not on any one weight, and
it reports the pair-days where the exchange does not lead instead of smoothing
them over.

Two things are easy to get wrong when reusing this code.

A Hasbrouck information share is not a Gonzalo-Granger weight. They decompose
different objects, and with uncorrelated innovations the second is the square of
the first over the sum of squares, so a weight of 0.80 goes with a share near
0.94. Compare their direction, never their magnitude.

Do not carry a pool's last price forward across minutes it did not trade in.
`staleness.py` measures what that costs on data with a known answer: at every
partial fill rate the estimator then calls the exchange the leader in 95 to 100
percent of runs, whoever actually leads. Dropping the untraded minutes, which is
what the pipeline does, keeps the error to 2 to 19 percent at the fill rates the
ranked pairs show.

Two provenance notes. The 24-hour volumes in `universe.csv` are a snapshot
taken when the universe was built; the minute bars were pulled afterwards, so
the two are minutes apart rather than simultaneous. And the CSVs carry no
capture timestamp of their own, so the date in the post is the commit date.

## Licence

MIT.
