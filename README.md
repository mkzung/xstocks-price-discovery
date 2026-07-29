# xStocks price discovery: the exchange against the chain

A tokenized equity trades at once on a centralised order book and in a Solana
pool, on the same issuer's mint, with arbitrage tying the two quotes together.
That makes it possible to ask which venue actually sets the price, and to check
an exchange's tape against something outside the exchange.

`POST.md` is the write-up. Everything in it is reproducible from this
repository.

## What is here

| path | what it does |
|------|--------------|
| `analysis/discovery.py` | Gonzalo-Granger common-factor weights, plus a simulator whose answer is fixed by construction |
| `analysis/collect.py` | builds the paired universe and pulls minute bars from both venues |
| `analysis/panel.py` | runs the estimator per token, whole window and split by US session |
| `analysis/venues.py` | the controls: a second exchange, and two pools on one mint |
| `analysis/relation.py` | the rank correlation behind the grouping, with a permutation test |
| `analysis/verify_post.py` | reads every number in `POST.md` back out of the CSVs |
| `tests/` | holds the estimator to the answer the simulator already knows |
| `data/` | the exact outputs behind every figure in the post |

## Reproducing

```bash
pip install -r requirements.txt
python -m pytest tests -q                 # the estimator still recovers its known answer
python analysis/verify_post.py            # every number in the post, checked against data/
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

The estimator was calibrated against a simulator with a known answer, and it
has two limits that the post states and that anyone re-running it should keep
in mind. The fit is biased upward by 0.02 to 0.12, so weights slightly above
one are the bias rather than a real reading. And the estimate is unstable when
two venues correct at similar speeds, scattering between 0.19 and 0.60 around a
true 0.5, so a near-even number means shared discovery rather than a measured
lead.

Two provenance notes. The 24-hour volumes in `universe.csv` are a snapshot
taken when the universe was built; the minute bars were pulled afterwards, so
the two are minutes apart rather than simultaneous. And the CSVs carry no
capture timestamp of their own, so the date in the post is the commit date.

## Licence

MIT.
