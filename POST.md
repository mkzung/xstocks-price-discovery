# Tokenized stocks are priced on the exchange, and the quieter the chain the more the exchange prints

A tokenized equity is the rare asset where the same instrument, the same
issuer's mint, trades at once on a centralised order book and in an on-chain
pool. Arbitrage should tie the two quotes together. That gives a market-health
question a single-venue study cannot ask: when the two disagree, which one
moves, and which one follows.

Volume can be manufactured on either side. A permanent price move cannot: it
has to come from someone who knows something, and the venue where it appears
first is the venue doing the pricing. Measuring that separates a market from a
tape.

The answer for Backed Finance's xStocks, measured on 29 July 2026, is that
the exchange leads and the Solana pool follows in every pair that can be
ranked. It holds when the sample is cut to the hours when the US equity market
is shut, and it holds on a second exchange, so it is the venue type doing the
pricing rather than one listing venue. The more useful finding is the one underneath it. Rank the
twenty-four tokens by how much their pool trades and by how many exchange
dollars are printed per on-chain dollar, and the two orders are almost exactly
reversed: the quieter the chain, the more the exchange prints against it. At
the bottom of that ordering sit six tokens with no on-chain market to check
the exchange against at all.

## The universe

Every Gate USDT pair whose ticker ends in X was matched to a Solana pool.
Ticker matching alone is not safe here, since several of these symbols collide
with unrelated mints, and two of the collisions carry hundreds of millions of
dollars of phantom liquidity. Each pool was therefore checked against the mint
prefix Backed uses for its issued tokens, and only exact-symbol pools on that
issuer's mint were kept.

That leaves **24 tokens quoted on both venues**. The first thing they show is
how far apart the two sides can be. Per dollar of on-chain volume in the same
mint, Gate's 24-hour volume ranges from 16 cents to **7,300 dollars**:

| token | Gate 24h | on-chain 24h | on-chain liquidity | Gate per on-chain dollar |
|-------|---------:|-------------:|-------------------:|-------------------------:|
| VTIX  | $29,243  | $4           | $1,329   | 7,311 |
| ACNX  | $127,448 | $24          | $225     | 5,310 |
| NFLXX | $116,413 | $33          | $6,003   | 3,528 |
| AZNX  | $35,041  | $60          | $3,674   | 584   |
| TQQQX | $303,700 | $1,680       | $72,215  | 181   |
| KOX   | $161,289 | $1,020       | $5,464   | 158   |
| ...   |          |              |          |       |
| MSTRX | $264,316 | $245,646     | $649,381 | 1.08  |
| TSLAX | $351,310 | $1,031,172   | $1,836,823 | 0.34 |
| CRCLX | $778,717 | $2,876,636   | $2,558,149 | 0.27 |
| NVDAX | $436,620 | $1,981,590   | $2,293,003 | 0.22 |
| QQQX  | $263,542 | $1,683,226   | $2,489,640 | 0.16 |

Four and a half orders of magnitude, inside one asset class, one issuer, and
one pair of venues. The median is 6.8.

## Which venue moves first

For the tokens where both sides actually trade, the two log price series are
cointegrated by construction: they quote one asset, so their difference is the
error and each venue's speed of correcting it says who is anchoring whom. The
Gonzalo-Granger common-factor weights fall straight out of those speeds, and
the venue that corrects less carries more of the permanent price move.

Nine pairs had enough overlapping minutes with both sides moving. Every one of
them is led by the exchange:

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

Read the speed columns rather than the weights. In eight of the nine pairs
Gate moves at most 0.08 of the gap per minute, while the pool closes 22 to 74
percent of it. The pool is chasing a price set somewhere else, and the
somewhere else is the order book.

Four of the exchange coefficients come out positive, which is the wrong sign:
the book drifting away from the pool rather than toward it. Two are noise at
0.002 and 0.008. The other two, GLDX at 0.04 and GOOGLX at 0.08, are small but
real, and they are exactly the pairs whose weights print above one. A weight
above one is the decomposition saying the pool contributed negatively, which it
cannot really do, so those two readings are worth no more than a rank.

AMZNX is the exception and it points the right way: it is the only pair where
the exchange itself corrects meaningfully, at 0.35, and also the pair with the
lowest exchange weight at 0.63. A venue that adjusts to the other side is a
venue giving up some of the pricing, which is what the decomposition is meant
to show. It is also the thinnest sample in the table at 79 paired minutes
against 477 for TSLAX, so it is the one row here to lean on least.

The ranking is not an artefact of the hours covered. Cutting the sample to the
minutes when the US equity market is closed, which is most of the window, leaves
eight pairs measurable and the exchange ahead in all eight, at weights of 0.96
to 1.24. Whatever is setting these prices overnight is doing it on the order
book.

That is not damning by itself. A pool tracking a deeper venue is a pool doing
its job, and the exchange volume in these nine names is buying real price
discovery. The question is what the other fifteen are buying.

## Is it Gate, or is it the order book

One exchange against one pool cannot tell the two apart. Gate could be leading
because it is Gate, or because a book with a resting maker queue prices faster
than a constant-product pool whoever runs it.

Bybit lists TSLAX, so the same test runs against a different exchange and the
same pool. Bybit leads too, at a weight of 0.75 over 498 paired
minutes: it corrects at 0.09 of the gap per minute while the pool closes
0.28. The lead belongs to the venue type rather than to one exchange.

The mirror control is two pools on the same mint. Here the exchange-against-pool
pattern disappears. Both pools correct hard against each other, the deeper one
by 0.58 to 0.88 of the gap per minute, where a
listing exchange moves at most 0.08 against a pool in eight of the nine
pairs above. Two of the three weights, 0.41 and
0.43, sit in the range the calibration calls shared discovery rather
than a lead. The third, NVDAX at 0.06, points the other way, and it is
also the pair where the deeper pool corrects hardest, at 0.88.

Pools on one chain arbitrage against each other inside a block, so a minute
grid cannot resolve which of them moved first and these three readings should
not be read as a ranking. What they do establish is the size of the effect:
pool against pool, correction runs both ways and runs fast, which is not what
the exchange-against-pool pairs look like at all.

## The less chain there is, the more the exchange prints

The twenty-four tokens sort into three groups on one measurement, how many
minutes their pool traded during the window, and the groups turn out to sort
the volume ratio too:

| group | tokens | median minutes the pool traded | median exchange dollars per on-chain dollar |
|-------|-------:|-------------------------------:|--------------------------------------------:|
| rankable | 9 | 217 | 1.1 |
| thin | 9 | 23 | 12.1 |
| no on-chain market | 6 | 4 | 2,056 |

That is not three buckets chosen to make a point. Across all twenty-four
tokens the rank correlation between minutes traded on-chain and exchange
dollars printed per on-chain dollar is **-0.93**, with a two-sided permutation
p below 0.0001 on twenty thousand draws, and it holds at -0.92 after dropping
the six most extreme ratios. On-chain liquidity ranks with traded minutes at
0.92, so the plain reading is that thin pools trade rarely, which is the same
statement rather than a competing one.

The six tokens at the bottom of that ordering are the ones where the exchange
tape has nothing to check it against:

| token | minutes the pool traded | exchange 24h volume | on-chain 24h volume | on-chain liquidity |
|-------|------------------------:|--------------------:|--------------------:|-------------------:|
| VTIX | 1 | $29,243 | $4 | $1,329 |
| AZNX | 3 | $35,041 | $60 | $3,674 |
| UNHX | 4 | $82,147 | $535 | $11,379 |
| NFLXX | 5 | $116,413 | $33 | $6,003 |
| ACNX | 7 | $127,448 | $24 | $225 |
| MCDX | 8 | $81,439 | $900 | $14,551 |

ACNX is the sharpest. The exchange reports a hundred and twenty-seven thousand
dollars of turnover in a token whose entire on-chain market is two hundred and
twenty-five dollars of liquidity, and whose pool printed in eleven minutes
across the last fifty-one hours.

Nothing here proves those prints are fake. What it does prove is that they
cannot be checked. For CRCLX or NVDAX an outside observer can ask whether the
exchange price is the one a wider market believes, because there is a wider
market. For ACNX there is nothing on the other side of the arbitrage, so the
exchange's tape is the only evidence that the exchange's tape is real. That is
the condition under which fabricated volume stays undetectable, and on this
venue it currently describes a quarter of the tokenized equities listed.

The nine in the middle sit between the two: their pools printed in eleven to
seventy-three minutes of the window, too few to rank a leader but enough to
show a market exists. They are named in `data/token_groups.csv` with the rest.

## What would change the reading

- **A wider window.** This is a single day, covering eight hours of overlap on
  the busiest tokens and less on the rest. A token quiet on-chain today may be
  active tomorrow, and the nine rankings need to hold across days before the
  leadership claim is more than a snapshot. The one cut available inside the
  day, open against closed, does hold.
- **The two venues agree on price.** On aligned minute bars the exchange quote
  sits about a tenth of a percent above the pool: 0.08 to 0.14 percent on
  average across the five tokens with enough data on both sides of the bell,
  and it narrows when the underlying equity is trading, from 0.12 percent
  closed to 0.08 percent open. The arbitrage is working, which is what makes
  the leadership question meaningful rather than a comparison of two unrelated
  prices.

## How the numbers were produced

Both sides are free and keyless: Gate's public candlestick endpoint for the
exchange minutes, GeckoTerminal's pool OHLCV endpoint for the on-chain
minutes, and Dexscreener for pool discovery with the mint prefix check.

The estimator is calibrated against a simulator whose answer is fixed by
construction, so it can be checked rather than trusted, and two limits came out
of that calibration.

The fit is biased upward by roughly 0.02 to 0.12, which is why four of the nine
exchange weights sit slightly above one, a value the decomposition cannot
really take. The ordering survives the bias in every configuration tested, so
the weights are read as a ranking rather than as point estimates.

The estimate is also unstable when two venues correct at similar speeds,
scattering between 0.19 and 0.60 around a true 0.5. No exchange-against-pool
pair is near even, the closest being AMZNX at 0.63; the pool-against-pool
readings are, which is why they are reported as a scale and not a ranking.

Two things about the data are worth stating plainly. The 24-hour volumes are a
snapshot taken when the universe was built and the minute bars were pulled
afterwards, so the two are minutes apart rather than simultaneous. And the
committed CSVs carry no capture timestamp of their own, so the date on this
post is the date the files were committed.

The repository holds the code, the tests that hold the estimator to its known
answer, the CSVs behind every figure, and a script that reads each number in
this post back out of those CSVs. The grouping of all twenty-four tokens,
including the nine in the middle, is in `data/token_groups.csv`.
