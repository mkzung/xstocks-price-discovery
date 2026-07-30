---
title: "Tokenized stocks are priced on the exchange, and the quieter the chain the more the exchange prints"
description: "Gonzalo-Granger price discovery for 24 xStocks quoted at once on Gate and on Solana pools, with the rank correlation between on-chain activity and exchange volume per on-chain dollar."
date: 2026-07-29
entities: [Gate, Bybit, Raydium, Orca, TSLAX, NVDAX, CRCLX, ACNX]
---

A tokenized equity is the rare asset where one instrument, on one issuer's
mint, trades at the same moment on a centralised order book and in an on-chain
pool. Arbitrage ties the two quotes together. That allows a market-health
question a single-venue study cannot ask: when the two disagree, which one
moves, and which one follows.

Volume can be manufactured on either side. A permanent price move cannot. It
has to come from someone who knows something, and the venue where it appears
first is the venue doing the pricing. Measuring that separates a market from a
tape.

This wiki has read Gate before. The [2021 Gate.io article](https://github.com/1712n/dn-institute/tree/main/content/research/market-health/posts/2021-01-19-Gate-io)
tested the digit distribution of the venue's own executed sizes, and the
[Bybit low-cap tape](https://github.com/1712n/dn-institute/tree/main/content/research/market-health/posts/2026-06-13-bybit)
read one book's cadence and clip sizes. Both check a venue against a statistical
expectation. This one checks it against a second venue quoting the same mint,
which is what makes the leadership question answerable at all.

The answer for Backed Finance's xStocks, measured on 29 July 2026, is that the
exchange leads and the Solana pool follows in every pair that can be ranked. It
holds when the sample is cut to the hours when the US equity market is shut,
and it holds on a second exchange, so the pricing belongs to the venue type
rather than to one listing venue.

The more useful finding sits underneath it. Rank the twenty-four tokens by how
much their pool trades, and by how many exchange dollars are printed per
on-chain dollar, and the two orders come out close to reversed: the quieter the
chain, the more the exchange prints against it. At the bottom of that ordering
sit six tokens with no on-chain market to check the exchange against at all.

{{< figure src="relation.png" alt="Scatter of minutes the pool traded against exchange dollars per on-chain dollar, on log axes, sloping down across four and a half orders of magnitude" caption="Each point is one token quoted on both venues. Rank correlation -0.93 across all twenty-four." >}}

## The universe

Every Gate USDT pair whose ticker ends in X was matched to a Solana pool.
Ticker matching alone is not safe here: several of these symbols collide with
unrelated mints, and two of the collisions carry hundreds of millions of
dollars of phantom liquidity. Each pool was therefore checked against the mint
prefix Backed uses for its issued tokens, and only exact-symbol pools on that
issuer's mint were kept.

That leaves **24 tokens quoted on both venues**. Per dollar of on-chain volume
in the same mint, Gate's 24-hour volume ranges from 16 cents to **7,311
dollars**:

| token | Gate 24h | on-chain 24h | on-chain liquidity | Gate per on-chain dollar |
|-------|---------:|-------------:|-------------------:|-------------------------:|
| VTIX  | $29,243  | $4           | $1,329     | 7,311 |
| ACNX  | $127,448 | $24          | $225       | 5,310 |
| NFLXX | $116,413 | $33          | $6,003     | 3,528 |
| AZNX  | $35,041  | $60          | $3,674     | 584   |
| TQQQX | $303,700 | $1,680       | $72,215    | 181   |
| KOX   | $161,289 | $1,020       | $5,464     | 158   |
| MSTRX | $264,316 | $245,646     | $649,381   | 1.08  |
| TSLAX | $351,310 | $1,031,172   | $1,836,823 | 0.34  |
| CRCLX | $778,717 | $2,876,636   | $2,558,149 | 0.27  |
| NVDAX | $436,620 | $1,981,590   | $2,293,003 | 0.22  |
| QQQX  | $263,542 | $1,683,226   | $2,489,640 | 0.16  |

Eleven of the twenty-four are shown; all of them are in
`data/token_groups.csv`. Four and a half orders of magnitude, inside one asset
class, one issuer, and one pair of venues. The median is 6.8.

## Which venue moves first

The two log price series are cointegrated by construction: they quote one
asset, so their difference is the error, and each venue's speed of correcting
it says who is anchoring whom. The Gonzalo-Granger common-factor weights fall
out of those speeds, and the venue that corrects less carries more of the
permanent price move.

Nine pairs had enough overlapping minutes with both sides moving. The exchange
leads every one:

{{< figure src="weights.png" alt="Left panel, exchange weight in the common factor for nine tokens, all at or above 0.63. Right panel, the share of the gap each side closes per minute, with the pool bars far longer than the exchange bars" caption="The exchange weight, and underneath it the reason: the pool closes the gap, the book does not." loading="lazy" >}}

| token  | Gate weight | Gate correction speed | pool correction speed |
|--------|------------:|----------------------:|----------------------:|
| GOOGLX | 1.19 | +0.08 | 0.49 |
| GLDX   | 1.15 | +0.04 | 0.28 |
| QQQX   | 1.04 | +0.01 | 0.22 |
| NVDAX  | 1.01 | +0.00 | 0.22 |
| MSTRX  | 0.93 | -0.06 | 0.74 |
| SPYX   | 0.92 | -0.02 | 0.22 |
| TSLAX  | 0.92 | -0.03 | 0.33 |
| CRCLX  | 0.85 | -0.07 | 0.40 |
| AMZNX  | 0.63 | -0.35 | 0.59 |

Read the speed columns rather than the weights. In eight of the nine pairs Gate
moves at most 0.08 of the gap per minute, while the pool closes 22 to 74
percent of it. The pool is chasing a price set somewhere else, and the
somewhere else is the order book.

Four of the exchange coefficients come out positive, which is the wrong sign:
the book drifting away from the pool rather than toward it. Two are noise, at
0.002 and 0.008. The other two, GLDX at 0.04 and GOOGLX at 0.08, are small but
real, and they are the pairs whose weights print above one. A weight above one
is the decomposition saying the pool contributed negatively, which it cannot
really do, so those two readings are worth no more than a rank.

AMZNX is the exception and it points the right way: the only pair where the
exchange itself corrects meaningfully, at 0.35, and also the pair with the
lowest exchange weight at 0.63. A venue that adjusts to the other side is a
venue giving up some of the pricing, which is what the decomposition is meant
to show. It is also the thinnest sample in the table, 82 paired minutes against
480 for TSLAX, so it is the row to lean on least.

The ranking is not an artefact of the hours covered. Cutting the sample to the
minutes when the US equity market is shut, which is 86 percent of the window,
leaves eight pairs measurable and the exchange ahead in all eight, at weights
of 0.96 to 1.24.

{{< figure src="sessions.png" alt="Exchange weights for eight tokens measured on the whole window and on the closed-market hours, both sets sitting near or above one" caption="Whatever sets these prices overnight is doing it on the order book." loading="lazy" >}}

A pool tracking a deeper venue is a pool doing its job, and the exchange volume
in these nine names is buying real price discovery. The question is what the
other fifteen are buying.

## Is it Gate, or is it the order book

One exchange against one pool cannot separate the two explanations. Gate could
lead because it is Gate, or because a book with a resting maker queue prices
faster than a constant-product pool whoever runs it.

Bybit lists TSLAX, so the same test runs against a different book on the same
pool. Bybit leads too, at a weight of 0.75 over 498 paired minutes: it corrects
at 0.09 of the gap per minute while the pool closes 0.28.

The mirror control is two pools on the same mint, where the pattern disappears.
Both pools correct hard against each other, the deeper one by 0.58 to 0.88 of
the gap per minute, against at most 0.08 for a listing exchange in eight of the
nine pairs above. Two of the three weights, 0.41 and 0.43, sit in the range the
calibration calls shared discovery rather than a lead; the third, NVDAX at
0.06, points the other way and is also the pair where the deeper pool corrects
hardest.

{{< figure src="controls.png" alt="Bar chart of first-venue weights: the Bybit against pool bar sits at 0.75, the three pool against pool bars scatter around and below the even line" caption="A second exchange leads. Two pools on one mint do not behave that way at all." loading="lazy" >}}

Pools on one chain arbitrage against each other inside a block, so a minute
grid cannot resolve which moved first, and these three readings are a scale
rather than a ranking. What they establish is the size of the effect: pool
against pool, correction runs both ways and runs fast, which is not what the
exchange-against-pool pairs look like.

## The less chain there is, the more the exchange prints

The twenty-four tokens sort into three groups on one measurement, how many
minutes their pool traded during the window, and those groups sort the volume
ratio too:

| group | tokens | median minutes the pool traded | median exchange dollars per on-chain dollar |
|-------|-------:|-------------------------------:|--------------------------------------------:|
| rankable | 9 | 217 | 1.1 |
| thin | 9 | 23 | 12.1 |
| no on-chain market | 6 | 4 | 2,056 |

Those are not three buckets chosen to make a point. Across all twenty-four
tokens the rank correlation between minutes traded on-chain and exchange
dollars printed per on-chain dollar is **-0.93**, with a two-sided permutation
p below 0.0001 on twenty thousand draws, and it holds at -0.92 after the six
most extreme ratios are dropped. On-chain liquidity ranks with traded minutes
at 0.92, so the plain reading is that thin pools trade rarely, which is the
same statement rather than a competing one.

The six at the bottom of the ordering are the ones whose exchange tape has
nothing to check it against:

| token | minutes the pool traded | exchange 24h volume | on-chain 24h volume | on-chain liquidity |
|-------|------------------------:|--------------------:|--------------------:|-------------------:|
| VTIX  | 1 | $29,243  | $4   | $1,329  |
| AZNX  | 3 | $35,041  | $60  | $3,674  |
| UNHX  | 4 | $82,147  | $535 | $11,379 |
| NFLXX | 5 | $116,413 | $33  | $6,003  |
| ACNX  | 7 | $127,448 | $24  | $225    |
| MCDX  | 8 | $81,439  | $900 | $14,551 |

ACNX is the sharpest. The exchange reports a hundred and twenty-seven thousand
dollars of turnover in a token whose entire on-chain market is two hundred and
twenty-five dollars of liquidity, and whose pool printed in eleven minutes
across the last fifty-one hours.

This is a flag, not a verdict. Nothing here shows those prints are fake. What
it shows is that they cannot be checked. For CRCLX or NVDAX an outside observer
can ask whether the exchange price is the one a wider market believes, because
there is a wider market. For ACNX there is nothing on the other side of the
arbitrage, so the exchange's tape is the only evidence that the exchange's tape
is real. That is the condition under which fabricated volume stays
undetectable, and on this venue it currently describes a quarter of the
tokenized equities listed.

The nine in the middle sit between the two: their pools printed in eleven to
seventy-three minutes of the window, too few to rank a leader but enough to
show a market exists. They are named in `data/token_groups.csv` with the rest.

## Four ways this could be wrong

Every number above comes from one estimator on one window, and four things
could produce it without the exchange leading anything. Each is answered
against the minute series themselves, which are committed under `raw/`, rather
than against the fitted panel.

### The model might not apply

The error-correction framework assumes the two log prices are cointegrated, and
the earlier draft called that true by construction. It is not. It is true if
arbitrage binds, and arbitrage cannot bind on a pool holding two hundred
dollars of liquidity. Tested rather than assumed, with an augmented Dickey-
Fuller regression on each pair's spread, it holds: the spread is stationary in
**7 of 7** rankable pairs, with half-lives of 2 to 6 minutes.

### A second estimator might disagree

Gonzalo-Granger reads leadership off the correction speeds and ignores how
correlated the two venues' innovations are. Hasbrouck (1995) splits the
variance of the efficient price innovation instead, and the two are different
quantities rather than two names for one: with uncorrelated innovations and
equal variances the second reduces to the square of the first over the sum of
squares, so a weight of 0.80 corresponds to a share near 0.94. Only the
direction can be compared, and it agrees in **7 of 7** pairs. Hasbrouck's
bounds are informative here because the innovation correlation is a median 0.39
rather than the near-collinear case that makes them useless, and every interval
sits entirely above an even split.

| token | paired minutes | pool fill | GG weight | Hasbrouck bounds | bootstrap lead | spread half-life |
|-------|---------------:|----------:|----------:|:----------------:|---------------:|-----------------:|
| TSLAX | 503 | 50% | 0.89 | 0.74 to 0.96 | 100% | 3 |
| NVDAX | 493 | 49% | 0.96 | 0.80 to 1.00 | 100% | 5 |
| QQQX | 457 | 46% | 1.06 | 0.98 to 1.00 | 100% | 6 |
| CRCLX | 378 | 38% | 0.90 | 0.60 to 0.98 | 99% | 2 |
| MSTRX | 244 | 25% | 0.90 | 0.56 to 0.99 | 100% | 2 |
| GOOGLX | 134 | 13% | 1.20 | 0.88 to 0.94 | 100% | 3 |
| SPYX | 124 | 12% | 1.03 | 0.94 to 0.99 | 100% | 4 |

The bootstrap column is each token's own data speaking rather than the method:
resampling blocks of the fitted regression rows, the exchange still leads in
99 to 100 percent of resamples. The weight's own interval is deliberately not shown,
because it is useless. The weight is a ratio whose denominator is the
difference between two similar speeds, so a resample that nudges them together
sends it to infinity and the interval stays wide however long the sample.

Nine of nine agreeing in the first window and 7 of 7 in the second is the
claim, not any single weight. Under a coin-flip null, 7 of 7 one way is p =
0.0156.

### Sparse trading might have invented it

This is the objection that would sink the study. A pool does not print every
minute. Its last price stands still while the exchange keeps moving, so when it
finally prints it jumps most of the way to the current level, which through an
error-correction model is indistinguishable from the pool chasing the exchange.

The simulator settles it, because there the answer is known. Build a world
where the **pool** is the true leader, sample the pool sparsely, and see what
the estimator says. Carrying the last price forward destroys it. At complete
fill the estimator is right, and it fails the moment a minute goes missing: at
every partial fill rate tested it calls the exchange the leader in **95 to 100
percent** of runs, and at the fill rates the real pools actually show it is 100
percent every time. Dropping the untraded minutes instead, which is what this
pipeline does, does not: across the ranked pairs' measured fill rates the same
test errs **2 to 19 percent** of the time.

{{< figure src="staleness.png" alt="Two curves against pool fill rate. The forward-filling curve sits flat at one hundred percent. The drop curve falls from thirty-eight percent at the sparsest fills to two percent at half, with the seven ranked tokens marked along it" caption="The sampling choice is doing load-bearing work. The ranked pairs sit on the lower curve, between 2 and 19 percent." loading="lazy" >}}

So the finding is not an artefact, but the residual risk is not zero and it is
not uniform. TSLAX at half its minutes filled sits at 2 percent; SPYX at an eighth
sits at 19 percent. The thin tokens further down the universe, at one to nine percent
fill, sit where the test errs up to 38 percent of the time, which is why none of them
is ranked here and why the volume finding below rests on their trading
frequency rather than on any leadership claim about them.

### It might be a specification choice

Five lags and one-minute bars were choices. Refitting every pair at one, three,
five and ten lags changes the leader in **0 of 7** pairs. Coarsening the grid
to five minutes, which is a deliberate handicap given pools arbitrage inside a
block, leaves the same leader in **7 of 7**.

### And it repeats out of sample

The window here is not the window the leadership table above was measured on.
Across the 7 tokens rankable in both, the exchange leads in both every time,
and the weights move by at most 0.11. The correction speeds, which are what the
ordering actually rests on, come back closer still.

{{< figure src="replication.png" alt="Left, exchange weights for seven tokens in two windows, all well above the even line in both. Right, pool correction speed in the first window against the second, with the points sitting on the diagonal" caption="Two windows, seven tokens, same answer." loading="lazy" >}}



## How this was measured

Both sides are free and need no key: Gate's public candlestick endpoint and
Bybit's spot kline endpoint for the exchange minutes, GeckoTerminal's pool
OHLCV endpoint for the on-chain minutes, and Dexscreener for pool discovery
with the mint prefix check.

### Mapping to the DN market-health metrics

The [market-health metric family](https://dn.institute/market-health/docs/market-health-metrics/)
covers this study as follows.

- `vwap` is the average price of an asset weighted by its trading volume over
  a period. This post uses the one-minute close from each venue instead,
  because the estimator needs both series on one clock and the close is the
  value both public endpoints expose. This is a real substitution and the
  committed data cannot bound it: the bars carry no intra-minute detail, so how
  far a close sits from that minute's VWAP is unmeasured here. The gaps the
  estimator works on are small, a median of 0.10 percent and at most 0.14
  percent across the nine ranked pairs, so a large enough intra-minute move
  would matter. It would have to move both venues in opposite directions to
  change the ranking, since a common move cancels in the difference.
- `tradecount` is the total number of trades in a timeframe. It appears here
  in a coarser form, the number of minutes in which a venue printed at all,
  because the public minute endpoints expose bars rather than a trade feed.
  That is the form that matters when one venue prints in four minutes out of
  four hundred and eighty.
- `volumedist` analyses the distribution of trading volumes. This post does not
  use a fixed-bin histogram; it uses each venue's 24-hour quote volume as a
  single total, because the question is the ratio between two venues rather
  than the shape within one.
- `timeoftrade` identifies abnormal accumulation of trades executed at the same
  minute or second. This post does not compute it. The session split above cuts
  the sample by hour of day, which is a different question: it asks whether the
  leadership result survives when the underlying equity is shut, not whether
  trades cluster on a schedule.

The leadership statistic itself is not a DN metric. It is the Gonzalo-Granger
common-factor decomposition of a two-venue error-correction model, where the
weights are read off the two error-correction speeds.

### The estimator and its limits

The estimator is calibrated against a simulator whose answer is fixed by
construction, so it can be checked rather than trusted. The calibration is
`analysis/calibrate.py`, ninety-six runs over eight speed pairs, and it is
committed as `data/calibration.csv`. It says the fit is worse than a single
weight makes it look.

The bias is small and consistent: the fit lands 0.03 above the truth on
average, in every speed pair tested. That is why four of the nine exchange
weights sit slightly above one, a value the decomposition cannot really take.

The scatter is not small. A single run lands anywhere from 0.33 below the truth
to 0.28 above it, and that holds across the whole grid rather than only where
the two venues correct at similar speeds. One token's weight is therefore a
weak reading on its own, and no weight in this post should be read as a point
estimate.

What survives that scatter is the ordering. Across the runs where the true
weight is plainly one-sided the estimator picks the right leader 98 percent of
the time, falling to 92 percent where the truth sits near even. The claim this
post rests on is not any single weight but that nine of nine pairs point the
same way, and underneath the weights, that the two correction speeds are far
apart: the pool closes 22 to 74 percent of the gap per minute while the
exchange closes at most 8. Those speeds are read straight off the fit rather
than through the ratio that forms the weight, and they are what the ordering is
built on. Pool-against-pool weights land near even, where the estimator is
weakest, which is why they are reported as a scale and not a ranking.

### Provenance

The 24-hour volumes are a snapshot taken when the universe was built, and the
minute bars were pulled afterwards, so the two are minutes apart rather than
simultaneous. Two panel runs are committed. The grouping and the rank
correlation use `panel_run1.csv`; the leadership weights and the session split
use the later `panel_sessions.csv`, which caught a few more minutes per token as
the window advanced. Where a sentence quotes a sample size, it quotes the run
that produced the table it sits under. The committed CSVs carry no capture timestamp of their own, so
the date on this post is the date the files were committed.

### Reproducing

The companion repository, pinned at `34d1464753`, holds the code, the tests that hold the estimator to
its known answer, the CSVs behind every figure, and `analysis/verify.py`, which
reads each number in this post back out of those CSVs.

```bash
git clone <companion-repo> && cd xstocks-price-discovery
git checkout 34d1464753
pip install -r requirements.txt
python -m pytest tests -q
python analysis/verify.py
python analysis/build_analysis.py
```
