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

The answer for Backed Finance's xStocks, over one 8-hour window on 29 July
2026, is that Gate leads and the Solana pool follows in every pair that can be
ranked. The more useful finding is the one underneath it: for a quarter of the
listed tokens there is no on-chain market to compare against at all.

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

Eight pairs had enough overlapping minutes with both sides moving. Every one of
them is led by the exchange:

| token  | Gate weight | Gate correction speed | pool correction speed |
|--------|------------:|----------------------:|----------------------:|
| GLDX   | 1.21 | +0.05 | 0.28 |
| GOOGLX | 1.16 | +0.07 | 0.48 |
| NVDAX  | 1.04 | +0.01 | 0.22 |
| QQQX   | 1.01 | +0.00 | 0.21 |
| TSLAX  | 0.93 | -0.02 | 0.32 |
| SPYX   | 0.92 | -0.02 | 0.22 |
| MSTRX  | 0.90 | -0.08 | 0.72 |
| CRCLX  | 0.87 | -0.06 | 0.40 |

Read the speed columns rather than the weights. Gate never moves more than
eight hundredths of the gap per minute in any pair, and usually moves against
it by nothing at all. The pool closes between 21 and 72 percent of the gap
every minute. The pool is chasing a price set somewhere else, and the somewhere
else is the order book.

That is not damning by itself. A pool tracking a deeper venue is a pool doing
its job, and Gate's volume in these eight names is buying real price discovery.
The problem is the other sixteen.

## The tokens with no chain to check

The window covers eight hours. In that window, six tokens traded on-chain for
fewer than ten minutes in total:

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

- **A wider window.** This is one eight-hour session. A token quiet on-chain
  today may be active tomorrow, and the eight rankings need to hold across days
  before the leadership claim is more than a snapshot.
- **The level gap.** Gate and the pool quote CRCLX six percent apart. Until
  that is explained, the spread cannot be treated as pure arbitrage error, and
  the market-hours split is the obvious first suspect: the underlying equity
  stops trading while the token does not.
- **Other exchanges.** Gate is one listing venue among several. The same test
  against another book would say whether the leadership is Gate's or simply
  any order book's.

## How the numbers were produced

Both sides are free and keyless: Gate's public candlestick endpoint for the
exchange minutes, GeckoTerminal's pool OHLCV endpoint for the on-chain
minutes, and Dexscreener for pool discovery with the mint prefix check.

The estimator is calibrated against a simulator whose answer is fixed by
construction, so it can be checked rather than trusted. Two limits came out of
that calibration and both matter for reading the table above. The fit is biased
upward by roughly 0.02 to 0.12, which is why four of the eight weights sit
slightly above one, a value the decomposition cannot really take; the ordering
survives the bias in every configuration tested, so the weights are read as a
ranking. And the estimate is unstable when two venues correct at similar
speeds, scattering between 0.19 and 0.60 around a true 0.5, so a near-even
reading would have meant shared discovery rather than a measured lead. None of
the eight pairs is near even.

Data, code and the test suite that holds the estimator to its known answer are
in the accompanying repository; every figure above is reproducible from the
committed CSVs.
