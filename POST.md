# Tokenized stocks are priced on the exchange, and for a quarter of them the chain is empty

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
pricing rather than one listing venue. The more useful finding is the one underneath it: for a
quarter of the listed tokens there is no on-chain market to compare against at
all.

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
Gate moves at most 0.08 of the gap per minute, and in four of them it
moves the wrong way by a rounding error, while the pool closes 22 to
74 percent of the gap every minute. The pool is chasing a price set
somewhere else, and the somewhere else is the order book.

AMZNX is the exception and it is the exception in the right direction: it is
the only pair where the exchange itself corrects meaningfully, at 0.35, and it
is also the pair with the lowest exchange weight at 0.63. A venue that adjusts
to the other side is a venue giving up some of the pricing, which is what the
decomposition is supposed to show.

The ranking is not an artefact of the hours covered. Cutting the sample to the
minutes when the US equity market is closed, which is most of the window, leaves
eight pairs measurable and the exchange ahead in all eight, at weights of 0.96
to 1.24. Whatever is setting these prices overnight is doing it on the order
book.

That is not damning by itself. A pool tracking a deeper venue is a pool doing
its job, and Gate's volume in these nine names is buying real price discovery.
The problem is the other fifteen.

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

## The tokens with no chain to check

The busiest tokens gave eight hours of paired minutes. In that window, six
tokens traded on-chain for fewer than ten minutes in total:

| token | minutes the pool traded | Gate 24h volume | on-chain 24h volume |
|-------|------------------------:|----------------:|--------------------:|
| VTIX  | 1  | $29,243  | $4   |
| AZNX  | 3  | $35,041  | $60  |
| UNHX  | 4  | $82,147  | $535 |
| NFLXX | 5  | $116,413 | $33  |
| ACNX  | 7  | $127,448 | $24  |
| MCDX  | 8  | $81,439  | $900 |

ACNX is the sharpest case. Gate reports a hundred and twenty-seven thousand
dollars of turnover in a token whose entire on-chain market is two hundred and
twenty-five dollars of liquidity and twenty-four dollars of daily volume, and
which printed on-chain in seven minutes out of four hundred and eighty.

Nothing here proves those prints are fake. What it does prove is that they
cannot be checked. For CRCLX or NVDAX an outside observer can ask whether the
exchange price is the one the wider market believes, because there is a wider
market. For ACNX there is nothing on the other side of the arbitrage, so the
exchange's tape is the only evidence that the exchange's tape is real. That is
the condition under which fabricated volume is undetectable, and it currently
describes a quarter of the tokenized equities listed on this venue.

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
construction, so it can be checked rather than trusted. Two limits came out of
that calibration and both matter for reading the table above. The fit is biased
upward by roughly 0.02 to 0.12, which is why four of the nine weights sit
slightly above one, a value the decomposition cannot really take; the ordering
survives the bias in every configuration tested, so the weights are read as a
ranking. And the estimate is unstable when two venues correct at similar
speeds, scattering between 0.19 and 0.60 around a true 0.5, so a near-even
reading would have meant shared discovery rather than a measured lead. Only
AMZNX comes close, at 0.63, and every other pair sits far from even.

Data, code and the test suite that holds the estimator to its known answer are
in the accompanying repository; every figure above is reproducible from the
committed CSVs.
