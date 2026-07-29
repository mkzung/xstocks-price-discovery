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

`post/index.md` is the write-up, with its figures beside it. Everything in it is reproducible from this
repository.

## What is here

| path | what it does |
|------|--------------|
| `analysis/discovery.py` | Gonzalo-Granger common-factor weights, plus a simulator whose answer is fixed by construction |
| `analysis/collect.py` | builds the paired universe and pulls minute bars from both venues |
| `analysis/panel.py` | runs the estimator per token, whole window and split by US session |
| `analysis/venues.py` | the controls: a second exchange, and two pools on one mint |
| `analysis/relation.py` | the rank correlation behind the grouping, with a permutation test |
| `analysis/verify.py` | reads every number in `post/index.md` back out of the CSVs |
| `analysis/build_analysis.py` | redraws every figure from `data/` |
| `tests/` | holds the estimator to the answer the simulator already knows |
| `data/` | the exact outputs behind every figure in the post |
| `dashboard/build_dashboard.py` | rebuilds `index.html`, the single-page view of the findings |

## Reproducing

```bash
pip install -r requirements.txt
python -m pytest tests -q                 # the estimator still recovers its known answer
python analysis/verify.py                 # every number in the post, checked against data/
python analysis/build_analysis.py         # redraw the figures
```

To pull fresh data, in this order:

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
right leader in 98 percent of runs where the true weight is clearly one-sided,
92 percent where it is near even. The post therefore leans on nine of nine
pairs agreeing and on the correction speeds, not on any one weight.

Two provenance notes. The 24-hour volumes in `universe.csv` are a snapshot
taken when the universe was built; the minute bars were pulled afterwards, so
the two are minutes apart rather than simultaneous. And the CSVs carry no
capture timestamp of their own, so the date in the post is the commit date.

## Licence

MIT.
