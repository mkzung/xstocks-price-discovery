---
title: "Tokenized stocks are priced on the exchange, and the quieter the chain the more the exchange prints"
description: "Which venue prices a tokenized equity, measured on 24 xStocks quoted at once on Gate and in Solana pools, daily across three days. The exchange leads in 21 of 23 rankable pair-days, the quieter a pool the more the exchange prints against it, and the exceptions are reported rather than smoothed over."
date: 2026-07-31
entities:
  - Gate
  - Bybit
  - Raydium
  - Orca
  - TSLAX
  - NVDAX
  - CRCLX
  - ACNX
---

## Summary

A tokenized equity is the rare asset where one instrument, on one issuer's
mint, trades at the same moment on a centralised order book and in an on-chain
pool. Arbitrage ties the two quotes together. That allows a market-health
question a single-venue study cannot ask: when the two disagree, which one
moves, and which one follows.

Volume can be manufactured on either side. A permanent price move is harder:
whatever drives it, information, inventory or force, it has to be paid for and
it has to appear somewhere first, and the venue where it keeps appearing first
is the venue doing the pricing. Which shock moved the price is beyond a
two-venue model; who moved first is not.

This wiki has read Gate before. The [2021 Gate.io
article](https://github.com/1712n/dn-institute/tree/main/content/research/market-health/posts/2021-01-19-Gate-io)
tested the digit distribution of the venue's own executed sizes, and the [Bybit
low-cap
tape](https://github.com/1712n/dn-institute/tree/main/content/research/market-health/posts/2026-06-13-bybit)
read one book's cadence and clip sizes. Both check a venue against a
statistical expectation. This one checks it against a second venue quoting the
same mint. That is what makes the leadership question answerable at all.

The answer for Backed Finance's xStocks, collected daily from 29 to 31 July
2026, is that the exchange leads and the Solana pool follows in 21 of the 23
pair-days that can be ranked. It holds when the sample is cut to the hours when
the US equity market is shut and it holds on a second exchange. The two
exceptions get their own paragraphs below, and both sit where the first day
already pointed: TSLAX reads near even on the third day, and AMZNX, the one
pair the first day flagged as the exchange giving up pricing, is a clear pool
lead the one day it can be measured, on the alignment these tables use. The
correction described below is the one thing that takes it away.

The more useful finding sits underneath it. Rank the twenty-four tokens by how
much their pool trades, and by how many exchange dollars are printed per
on-chain dollar, and the two orders come out close to reversed: the quieter the
chain, the more the exchange prints against it. At the bottom of that ordering
sit six tokens whose pools are too close to dead to check the exchange against.

{{< figure src="relation.png" alt="Scatter of minutes the pool traded against exchange dollars per on-chain dollar, on log axes, sloping down across four and a half orders of magnitude" caption="Each point is one token quoted on both venues. Rank correlation -0.93 across all twenty-four." >}}

## The universe

Every Gate USDT pair whose ticker ends in X and printed at least twenty
thousand dollars of 24-hour volume was matched to a Solana pool. Ticker
matching alone is not safe here: a re-screen after the third collection day,
run by `analysis/collisions.py` and committed as `data/collisions.csv`, found
13 Solana pools answering to 10 of these tickers on mints that are not the
issuer's. Their claimed liquidity was negligible that day, and the population
is not stable: impostor pools appear and vanish between screens. Each pool was
therefore checked against the vanity prefix Backed uses for its issued mints,
and only exact-symbol pools on such mints were kept. A prefix is a screen, not
authentication, so every kept mint is checked against the issuer's own
published list at `api.xstocks.fi`, which gives each asset's deployment address
per network. All 24 match the Solana address Backed publishes for that symbol,
and the same 24 also appear in Jupiter's independently curated verified list.
`data/registry_check.csv` records both, `data/universe.csv` carries the full
addresses, and `analysis/registry.py` rebuilds the check.

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
`data/token_groups.csv`, which `analysis/relation.py` builds along with the
rank correlation and its permutation test. Four and a half orders of magnitude,
inside one asset class, one issuer, and one pair of venues. The median is 6.8.

## Which venue moves first

Two venues quoting one mint should share one efficient price, so the difference
between their log quotes is the error each is pulled back toward, and each
venue's speed of closing it says who is anchoring whom. The Gonzalo-Granger
common-factor weights fall out of those speeds: the venue that corrects less
carries more of the permanent price move. Whether the two series really are
cointegrated is a testable claim, not a definition, and it is tested below
instead of assumed.

Nine pairs cleared the session panel's gate of eighty paired minutes with
twenty moves on each side, and in that pass the exchange leads every one. Two
sit under the stricter 120-minute floor the series passes use, GOOGLX at 119
and AMZNX at 82, and the text below leans on them accordingly:

{{< figure src="weights.png" alt="Left panel, exchange weight in the common factor for nine tokens, the lowest at 0.63. Right panel, the share of the gap each side closes per observation, with the pool bars far longer than the exchange bars" caption="The exchange weight, and underneath it the reason: the pool closes the gap, the book does not." loading="lazy" >}}

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
moves at most 0.08 of the gap per observation, while the pool closes 22 to 74
percent of it. The pool is chasing a price set somewhere else, and the
somewhere else is the order book.

An observation is a minute both venues traded in, and the untraded minutes are
dropped rather than filled, so consecutive rows are not always a minute apart.
The median gap between them is one minute for four of the seven ranked pairs on
the first series pass, two or three for the rest, and the mean runs from 2.0 to
8.1 minutes because a handful of long silences pull it. So these coefficients
are per observation and not per minute, and the two readings are the same only
where a pool traded in nearly every minute. That does not touch which venue
leads, since both sides of a pair are read off the same rows, and it does mean
a speed here is not a rate per clock minute. The grid sweep below shows the
same thing from the other end: refitting TSLAX on five-minute bars takes the
pool's coefficient from 0.34 to 0.67, because a coarser bar is a longer step.

Four of the exchange coefficients come out positive. That is the wrong sign,
the book drifting away from the pool rather than toward it. All four are small,
from 0.002 to 0.08, and where the series pass can put a bootstrap band around
one, the band includes zero, so none of them can be told from noise. The two
largest, GLDX at 0.04 and GOOGLX at 0.08, are the pairs whose weights print
above one, and a weight above one is the decomposition saying the pool
contributed negatively, which it cannot really do. Those readings are worth no
more than a rank.

AMZNX is the exception and it points the right way: the only pair where the
exchange itself corrects meaningfully, at 0.35, and also the pair with the
lowest exchange weight at 0.63. A venue that adjusts to the other side is a
venue giving up some of the pricing, and showing that is what the decomposition
is for. It is also the thinnest sample in the table, 82 paired minutes against
480 for TSLAX. Two days later, with enough minutes to rank properly, this stops
being a caveat: AMZNX turns out to be the study's one clear pool lead, in the
daily section below. On the corrected alignment it is 0.33 rather than -0.24,
which is no longer a clear lead for either side; the correction reported below
moves 21 of 23 weights the same way, so the exception is the reading it costs.

Is the ranking an artefact of the hours covered? The panel's own answer is no,
at weights of 0.96 to 1.24 across the eight pairs measurable when the US equity
market is shut, which is 86 percent of the window. That panel kept no minutes,
though, so nobody can refit it from anything committed here, and a saved
aggregate is a record of a result rather than a way to check it. The claim
therefore rests on the three series passes, where the same cut does refit. 19
pair-days carry at least 120 shut-hours minutes, and the exchange leads 17 of
them on the shut hours against 17 on the whole window. That equality is two
offsetting flips rather than nothing moving: METAX falls from 0.57 to 0.41 and
TSLAX rises from 0.47 to 0.51, each crossing an even split, and the strict rule
declines to call either of them in either regime. AMZNX stays a pool lead in
both. So the ranking does not depend on the market being open, which is the
question asked; it says nothing to firm up a pair that was already near even.
`data/sessions_from_series.csv` holds it and `analysis/sessions.py` rebuilds
it.

{{< figure src="sessions.png" alt="Exchange weights for eight tokens measured on the whole window and on the closed-market hours, both sets sitting near or above one" caption="The session panel's reading of the overnight hours. It is the saved aggregate, not a refittable one; the series passes below carry the weight of the claim." loading="lazy" >}}

A pool tracking a deeper venue is a pool doing its job, and the exchange volume
in these nine names is buying real price discovery. The question is what the
other fifteen are buying.

## Is it Gate, or is it the order book

One exchange against one pool cannot separate the two explanations. Gate could
lead because it is Gate, or because a book with a resting maker queue prices
faster than a constant-product pool whoever runs it.

Bybit lists TSLAX, so the same test runs against a different book on the same
pool. Bybit leads too, at a weight of 0.75 over 498 paired minutes: it corrects
at 0.09 of the gap per observation while the pool closes 0.28.

The mirror control is two pools on the same mint, where the pattern disappears.
Both pools correct hard against each other, the deeper one by 0.58 to 0.88 of
the gap per observation, against at most 0.08 for a listing exchange in eight
of the nine pairs above. Two of the three weights, 0.41 and 0.43, sit in the
range the calibration calls shared discovery rather than a lead; the third,
NVDAX at 0.06, points the other way and is also the pair where the deeper pool
corrects hardest.

{{< figure src="controls.png" alt="Bar chart of first-venue weights: the Bybit against pool bar sits at 0.75, the three pool against pool bars scatter around and below the even line" caption="A second exchange leads. Two pools on one mint do not behave that way at all." loading="lazy" >}}

Pools on one chain arbitrage against each other inside a block, so a minute
grid cannot resolve which moved first, and these three readings are a scale
rather than a ranking. What they establish is the size of the effect: pool
against pool, correction runs both ways and runs fast, and the
exchange-against-pool pairs look nothing like that.

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
at 0.92, so the plain reading is that thin pools trade rarely. That is the same
statement, not a competing one. The ratio's denominator shares data with the
activity measure, so the correlation could be suspected of being mechanical;
the numerator alone says otherwise. Exchange dollars in absolute terms rank
positively with pool activity, at 0.64, meaning busy pools sit on busy
listings. The finding is that the exchange's volume against the quiet pools is
large relative to anything the chain can absorb, not that it is large outright.

The six at the bottom of the ordering are the ones whose pools, a few prints
and a few hundred dollars deep, cannot meaningfully check the exchange tape:

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
twenty-five dollars of liquidity, and whose pool overlapped the exchange tape
for seven minutes in the pass above.

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

## What would have to be true for this to be wrong

Everything above rests on one estimator, one specification and one stretch of
minutes. Six things could have gone wrong underneath it. The first is a mistake
in how the two tapes were read, and it opens this section because it comes
before the rest; it is answered across all three series passes. The other five
are ways the result could have appeared with no venue leading anything, and
each is answered against the first day's pass, whose minute series are
committed under `raw/` so the check can be re-run instead of taken on trust.
Whether any of it survives being measured again has its own section after them.

### Whether the two series describe the same instant

Before any of the rest, the two prices have to be the same moment. They were
not.

Gate's candlestick endpoint, which supplies the exchange minutes, returns a bar
as `[timestamp, quote volume, close, high, low, open, base volume, closed]`,
and the collector read field five, the open, which is the price at the stamp.
GeckoTerminal's pool OHLCV endpoint, which supplies the on-chain minutes,
returns `[timestamp, open, high, low, close, volume]`, and the collector read
field four, the close, sixty seconds later. So at every timestamp the pool
price was a minute newer than the exchange price beside it.

Both tapes say which field is which, because on each the open of a bar equals
the close of the one before. The study's own minutes say what it cost:
correlate one-minute returns at lags of minus three to plus three, and the
strongest correlation sits at plus one rather than zero on **14 of 23** ranked
pairs.

A pool holding newer information than the venue it is measured against has been
given a head start. The error pushes towards calling the pool the leader, the
opposite of what is reported here.

Correcting it needs no new collection. Gate's close for a minute is Gate's open
for the next one, the following row of the same committed file, so the exchange
series moves onto the same instant at the cost of the rows whose next minute
was never collected. Refitted that way, the exchange leads **22 of 23** rather
than 21 and the median weight rises from 0.90 to **1.17**. The exchange's own
correction speed collapses towards zero, far enough that most weights leave the
range the decomposition can express, and that is the reason this post reads the
speeds and not the weights.

The relation itself is not an artefact of the misalignment. The spread is the
same size either way, a median standard deviation of 20.9 basis points as
collected against 20.7 realigned, and it stays stationary in 21 of 23 pairs
after the correction against 23 of 23 before it. The difference is a sample cut
roughly in half, not a weaker relation.

One reading does not survive the correction, and it is the one that runs
against the headline. AMZNX is the study's single clear pool lead at -0.24;
realigned it is 0.33, inside the band the strict rule declines to call. A
correction that moves 21 of 23 weights towards the exchange has to do that. The
other two move the other way by 0.01 and less, and no pair loses a lead it had,
so the correction takes the one pool reading and hands back none. It is why
"conservative" cannot be said of the whole and left to stand for each part: the
as-collected fit is the harder test of the headline and the easier one for its
exception. The exception is named where it appears, with the corrected reading
beside it.

The tables in this post are the as-collected fit, and the reason is not that it
reads better. Every other check here was run on those series: the bootstrap,
the Hasbrouck bounds, the stationarity tests, the session split, the daily
comparison and the sensitivity sweeps. Refitting all of it on a sample cut in
half would be a second study rather than a correction, and it would be a second
study whose answer is already known to be the same one, more strongly. What is
reported is therefore the conservative side of the error, said plainly here
rather than left for a reader to find.

One thing this does not touch. Bybit and MEXC return their closes at field four
and the collector read field four, so the second exchange and the
pool-against-pool controls were on the same instant throughout. The misreading
was Gate's alone.

`analysis/alignment.py` rebuilds the comparison into `data/alignment.csv` and
`analysis/collect.py` now reads Gate's close. A test pins the field layout of
all four venue readers against payloads shaped like the real ones, since
nothing had held any of them to a known answer.

### Cointegration, tested rather than assumed

The error-correction framework assumes the two log prices are cointegrated, and
the earlier draft called that true by construction. It is not. It is true if
arbitrage binds, and arbitrage cannot bind on a pool holding two hundred
dollars of liquidity. Tested rather than assumed, with an augmented
Dickey-Fuller regression on each pair's spread, it holds: the spread is
stationary in **7 of 7** rankable pairs, and it reverts fast: half-lives of 0.6
to 3.9 observations. Those are steps and not clock minutes, for the reason the
correction speeds are: the regression runs on the rows it is given. Multiplying
each pair by its own mean spacing puts the reversion between 2.4 and 25.0
minutes, and the slow end is the pairs whose pools trade least, which is the
same ordering everything else in this post keeps finding.

### The error term, fitted instead of imposed

Stationarity is tested on the spread of log prices, which imposes a
cointegrating vector of one to minus one instead of fitting it. Two venues
quoting one mint should move one for one, and imposing that buys precision, but
it is an assumption and it can fail: a pool at a proportional discount that
widens with the price would need a coefficient away from one, and the spread
built the wrong way would not be the error the model thinks it is.

Fitted instead of imposed, the coefficient comes out between 0.85 and 1.00,
below one in every pair. That is what noise in a regressor does, not evidence
of scaling: a pool quote carries error, and error in a regressor drags its
slope toward zero. The test that survives that is whether one sits inside the
bracket the two one-sided regressions define, and it does in **7 of 7** pairs.
Refitting the whole model on the fitted coefficient instead of the imposed one
names the same leader in **7 of 7**, moving the largest weight by 0.20. That
one case is GOOGLX, whose imposed weight of 1.20 is above one and so
impossible; fitting the coefficient brings it to 1.00, a more plausible reading
of the same data.

### Hasbrouck against Gonzalo-Granger

Gonzalo-Granger reads leadership off the correction speeds and ignores how
correlated the two venues' innovations are ([Gonzalo and Granger
1995](https://doi.org/10.1080/07350015.1995.10524576)). Hasbrouck splits the
variance of the efficient price innovation instead ([Hasbrouck
1995](https://doi.org/10.1111/j.1540-6261.1995.tb04054.x)), and the two are
different quantities, not two names for one: with uncorrelated innovations and
equal variances the second reduces to the square of the first over the sum of
squares, so a weight of 0.80 corresponds to a share near 0.94. Only the
direction can be compared, and it agrees in **7 of 7** pairs. Hasbrouck's
bounds are informative here because the innovation correlation is a median 0.39
rather than the near-collinear case that makes them useless, and every interval
sits entirely above an even split.

| token | paired minutes | pool fill | GG weight | Hasbrouck bounds | bootstrap lead | half-life, obs |
|-------|---------------:|----------:|----------:|:----------------:|---------------:|---------------:|
| TSLAX | 503 | 50% | 0.89 | 0.74 to 0.96 | 100% | 1.6 |
| NVDAX | 493 | 49% | 0.96 | 0.80 to 1.00 | 100% | 2.8 |
| QQQX | 457 | 46% | 1.06 | 0.98 to 1.00 | 100% | 3.9 |
| CRCLX | 378 | 38% | 0.90 | 0.60 to 0.98 | 99% | 1.2 |
| MSTRX | 244 | 25% | 0.90 | 0.56 to 0.99 | 100% | 0.6 |
| GOOGLX | 134 | 13% | 1.20 | 0.88 to 0.94 | 100% | 1.7 |
| SPYX | 124 | 12% | 1.03 | 0.94 to 0.99 | 100% | 3.1 |

The bootstrap column is each token's own data speaking rather than the method:
resampling blocks of the fitted regression rows, the exchange still leads in 99
to 100 percent of resamples. The weight's own interval is deliberately not
shown, because it is useless. The weight is a ratio whose denominator is the
difference between two similar speeds, so a resample that nudges them together
sends it to infinity and the interval stays wide however long the sample.

The claim is never a single weight. In this pass seven of seven point the same
way, which carries p = 0.0156 under a coin-flip null; the session panel's nine
of nine and the daily repeats are tallied in their own sections, and across all
three days the count is 21 of 23.

That null treats the seven pairs as seven separate draws, and these are all US
equities, so the obvious objection is that one market moved and the seven
agreed for one reason. The objection is right about the prices and misses what
the model is fitted to. It is not fitted to a price but to the gap between two
venues quoting one mint, and a market-wide move enters both sides of that gap
at once. Measured on the ten token pairs of this pass with enough jointly
observed minutes: the exchange legs move together at a median 0.51, the pool
legs at 0.14, and the spread the model actually uses at **0.08**. What is
shared is the price, not the arbitrage relation. Some sharing survives.
Discounting the sample by the mean spread correlation of 0.12 leaves seven
pairs worth about four, and four of four one way is 0.125 under the same
coin-flip null. That is arithmetic, not a second test. The discount is borrowed
from the correlated-mean case and applied to binary outcomes, so read it as the
order of magnitude the sharing costs. It is harsh, since a correlation only
costs a draw if it pushes a weight across an even split, and it is rough, since
nothing here shows this is the right discount to take. What it settles is that
a single pass of seven is suggestive on its own, and that the case rests on the
repeats and the controls. `analysis/dependence.py` rebuilds it into
`data/dependence.csv`, overlap counts included, since eleven of the twenty-one
pairings do not clear the floor and are left out.

### Could sparse trading have invented all of it

This is the objection that would sink the study. A pool does not print every
minute. Its last price stands still while the exchange keeps moving, so when it
finally prints it jumps most of the way to the current level, which through an
error-correction model is indistinguishable from the pool chasing the exchange.

The simulator gives the objection a number, because there the answer is known.
Build a world where the **pool** is the true leader, sample the pool sparsely,
and see what the estimator says. Carrying the last price forward destroys it.
At complete fill the estimator is right, and it fails the moment a minute goes
missing: at every partial fill rate tested it calls the exchange the leader in
**95 to 100 percent** of runs, and at the fill rates the real pools actually
show it is 100 percent every time. Dropping the untraded minutes instead, as
this pipeline does, holds the error to **2 to 19 percent** on a long base
series. The simulation drops minutes independently at random, while a real
pool's silences follow price, liquidity and fees, and the fit treats surviving
rows as consecutive whatever gap they span, so this bounds the artefact under a
stated model rather than settling it. Sample length matters too, and
`data/staleness_matched.csv` prices it: shortening the base series to the
sixteen-hour windows the real pairs occupy lifts the error to about 12 percent
at half fill and 42 percent at an eighth. The deep pairs carry low risk; the
thin ranked pairs carry real risk on any single day, which is what the daily
repetition and the strict tally below are for. The artefact also runs one way,
fabricating exchange leads, so AMZNX's pool lead stands against it, not because
of it. The bar misalignment runs the same way, and on the corrected series that
reading is 0.33 rather than -0.24, so this particular exception survives only
the sampling objection and not the alignment one.

{{< figure src="staleness.png" alt="Two curves against pool fill rate. The forward-filling curve sits flat at one hundred percent. The drop curve falls from thirty-eight percent at the sparsest fills to two percent at half, with the seven ranked tokens marked along it" caption="The sampling choice is doing load-bearing work. The ranked pairs sit on the lower curve, between 2 and 19 percent." loading="lazy" >}}

So the finding is not an artefact, but the residual risk is not zero and it is
not uniform. TSLAX at half its minutes filled sits at 2 percent; SPYX at an
eighth sits at 19 percent. The thin tokens further down the universe, at one to
nine percent fill, sit where the test errs up to 38 percent of the time, which
is why none of them is ranked here and why the volume finding below rests on
their trading frequency rather than on any leadership claim about them.

That is a simulation answering for the data. The data can answer for itself,
and it had not been asked: if sparse trading were driving the reading, the
sparser pairs would read differently from the dense ones. Across the 23
pair-days the rank correlation between the exchange weight and the mean minutes
between rows is -0.01, against the count of paired minutes +0.02, and against
the fill rate +0.01, none of them distinguishable from nothing on a permutation
test. Split the pair-days at the median spacing and the tally is 11 of 12 on
the tighter-spaced side against 10 of 11 on the wider. A sample this size
resolves a rank correlation of about 0.42, so this rules out a strong relation
and not a weak one, and it is the empirical half of an objection the simulation
answers from the other end. `analysis/spacing.py` rebuilds it into
`data/spacing.csv`.

A prediction went in here and did not come out, which belongs in the record.
Reversion over a gap is concave in the length of the gap, so a long enough gap
saturates both venues' correction and pulls the ratio between them toward an
even split. That would have shown up as the wider-spaced pairs sitting nearer
an even split than the tighter-spaced ones. They sit further from it: the rank
correlation between spacing and distance from an even split is +0.13, the
opposite sign to the prediction and small enough to mean nothing either way at
23 pair-days. So the saturation is not reached at these gaps, against a spread
that reverts in single-digit steps, and the argument is unavailable. What
stands is the measurement.

### Lags, grids and the other free choices

Five lags and one-minute bars were choices. Refitting every pair at one, three,
five and ten lags changes the leader in **0 of 7** pairs. Coarsening the grid
to five minutes handicaps the test on purpose, since pools arbitrage inside a
block, and it leaves the same leader in **7 of 7**.

The 120-minute floor is the third such choice, and a cut is only innocent if it
does not select on the outcome, so the estimator was run below it as well. The
16 pairs it can fit there lean the same way, 12 of them to the exchange at a
median 0.93, against 21 of 23 at 0.90 above it. Those readings are not evidence
and are not counted anywhere: at 43 to 111 paired minutes the estimator
scatters, and 6 of the 16 print outside the range a weight can take, which is
what the floor is for. What they establish is weaker than it first looks. A
further 26 pairs the estimator refuses outright, on too few rows to fit at all.
Those are not missing at random. A pair is refused because its pool barely
traded, and how much a pool trades is the thing this post shows tracks the
exchange's dominance. The 16 that can be fitted are therefore a selected sample
too, and agreement inside them cannot rule out that the excluded 26 would have
pointed the other way. It is a sensitivity check on the floor, not a
demonstration that the floor is neutral. `analysis/threshold.py` rebuilds this
into `data/threshold.csv`.

## Measured again, and then daily

A result that exists in one stretch of minutes is a result about that stretch.
The leadership was therefore refitted on a second pass over the same day, and
the whole collection then became a daily routine, each day on its own volume
snapshot so that nothing at all is carried over.

Against the session panel first: the 7 tokens rankable in both the panel and
the series pass lead in both every time, with weights moving by at most 0.11.
The correction speeds, which are what the ordering actually rests on, come back
closer still.

{{< figure src="replication.png" alt="Left, exchange weights for seven tokens measured in the session panel and in the series pass, all well above the even line in both. Right, pool correction speed in one pass against the other, with the points sitting on the diagonal" caption="Same day, two passes, seven tokens, one answer." loading="lazy" >}}

The next days are the harder test. The headline number replicates without
wobble. The correlation between how much a pool trades and how many exchange
dollars are printed against it prints -0.93 on 25 tokens on the second day and
**-0.93** on 24 on the third, each with a permutation p below 0.0001, and each
surviving its own tail check: dropping the six most extreme ratios leaves the
third day at -0.92 on 18 tokens. Pool liquidity ranks with pool activity at
0.90. Whatever else moves between days, the quieter the chain, the more the
exchange prints, every day, by the same amount.

The leadership is where three days say more than two. Every token measurable
across days:

| token | 29 July | 30 July | 31 July | span |
|-------|--------:|--------:|--------:|-----:|
| SPYX | 1.03 | 1.05 | - | 0.01 |
| GLDX | - | 0.64 | 0.67 | 0.03 |
| QQQX | 1.06 | 1.01 | 0.92 | 0.15 |
| MSTRX | 0.90 | 0.91 | 0.72 | 0.18 |
| NVDAX | 0.96 | 0.77 | 0.76 | 0.20 |
| GOOGLX | 1.20 | 0.94 | - | 0.26 |
| CRCLX | 0.90 | 0.72 | 0.61 | 0.29 |
| TSLAX | 0.89 | 0.92 | 0.47 | 0.44 |

Seven of the eight tokens rankable in more than one window lead in every window
they appear in. The second day alone ranks nine and the exchange leads all
nine, at a sign-test p of 0.0039. The third day is softer: five of seven, and
the two that break ranks are the honest content of the table.

TSLAX prints 0.47 on the third day after 0.89 and 0.92, with the exchange for
once correcting meaningfully, at 0.21 of the gap per observation. A move of
that size sits at the edge of the scatter the calibration declares for one
weight from one sample, so the reading is shared discovery on that day rather
than a measured handover, and the two clear days still carry the token's
ranking.

AMZNX is not noise. The first day's panel already flagged it as the only pair
where the exchange corrects meaningfully and the weight sits lowest; the third
day, the first with enough paired minutes to rank it in a series pass, prints a
weight of -0.24 with the pool ahead in 98 percent of bootstrap resamples and
both estimators agreeing. That is a pool lead, stated plainly, on the alignment
these tables use. It is also the reading the bar correction costs: realigned,
AMZNX is 0.33, which the strict rule declines to call for either side. Both are
true and the second is the less comfortable, which is why it is here and not
only in the robustness section. One pair out of twenty-three pair-days prices
on the chain as measured, and it is the pair the very first measurement pointed
at. A method that can only find exchange leads would be describing itself; this
one found the exception.

The 21-of-23 tally uses one mechanical rule, a weight above an even split,
because a tally needs a rule that cannot be argued with after the fact. The
calibration says weights near even are weak readings, so here is the same count
under a stricter predeclared rule that only classifies weights outside 0.3 to
0.7: **17 pair-days are clear exchange leads, 1 is a clear pool lead, and 5 are
unclassified**. The direction is the same and the resolution is not: 21 of 23
under the loose rule becomes 17 classified one way, 1 the other, and 5 that the
strict rule declines to call. GLDX shows what the difference costs. Its 0.64
and 0.67 count as exchange leads under the loose rule and fall into the
unclassified band under the strict one, which is the honest reading of a weight
that close to even. METAX printed 0.57 on the second day, the one pair where
the estimators disagreed, and on the third day its pool went completely silent:
not a single print in the sixteen hours the exchange window reaches, after 142
paired minutes the day before. A pool that is a venue one day and absent the
next is the volatility of the thin end of this market, measured.

Three collection notes, none of them footnotes. The second and third days both
lost their network mid-run and were topped up within hours, so each holds two
collection sessions; per-token timestamps are in each run's `coverage.csv`, and
each day's ratios use that day's own morning snapshot. Tokens whose pools could
not be paired at all, because their last prints sit further back than the
exchange window reaches, numbered two on the second day and three on the third,
METAX among them. And ABTX and PMX, paired for the first time on the third day,
managed one overlapping minute each. The tokens too dead to measure are the
strongest form of the pattern the measurement shows.

## How this was measured

Both sides are free and need no key: Gate's public candlestick endpoint and
Bybit's spot kline endpoint for the exchange minutes, GeckoTerminal's pool
OHLCV endpoint for the on-chain minutes, and Dexscreener for pool discovery
with the mint prefix check. The exchange endpoints serve the last thousand
one-minute bars, which is the sixteen-hour window every pass works inside.

### Which collection each number comes from

Five passes over the same venues sit behind this post, and they do not agree to
the minute because they were taken at different times. TSLAX shows 477, 480,
503, 530 and 433 paired minutes across them. That is the window moving, not a
disagreement, but a figure only means something once you know which pass it
came from.

| pass | when | tokens | what it produces |
|------|------|-------:|------------------|
| universe | 29 July | 24 | the volume snapshot, the grouping, the rank correlation |
| session panel | 29 July, later | 13 | the leadership table and the open-against-shut split |
| series | 29 July, later still | 16 | the minute series in `raw/`, and every robustness check |
| next day | 30 July, two sessions | 25 | the repeat, on its own volume snapshot |
| third day | 31 July, two sessions | 24 | the repeat of the repeat, likewise |

The last three keep their underlying minute series. The robustness checks below
run on the first of those, the daily comparison reads all three, and the tables
above come from passes whose minutes were never kept. Where a sentence quotes a
sample size it quotes the pass that produced the table it sits under, and the
pass is named wherever two of them could be confused.

### Mapping to the DN market-health metrics

The [market-health metric
family](https://dn.institute/market-health/docs/market-health-metrics/) covers
this study as follows.

- `vwap` is the average price of an asset weighted by its trading volume over
  a period. This post uses the one-minute close from each venue instead,
  because the estimator needs both series on one clock and the close is the
  value both public endpoints expose. This is a real substitution and the
  committed data cannot bound it: the bars carry no intra-minute detail, so how
  far a close sits from that minute's VWAP is unmeasured here. The gaps the estimator works on are small, a median of 0.10 percent and at most 0.14 percent across the nine ranked pairs, so a large enough intra-minute divergence would matter. A close-versus-VWAP error common to both venues cancels in the spread; an error on one side alone does not, and thin minutes make one-sided errors likelier. That is a real, unmeasured term in every minute-bar study of this kind.
- `tradecount` is the total number of trades in a timeframe. It appears here
  in a coarser form, the number of minutes in which a venue printed at all,
  because the public minute endpoints expose bars, not a trade feed.
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
construction, so it can be checked instead of trusted. The calibration is
`analysis/calibrate.py`, ninety-six runs over eight speed pairs, and it is
committed as `data/calibration.csv`. It says the fit is worse than a single
weight makes it look.

The bias is small and consistent: the fit lands 0.03 above the truth on
average, in every speed pair tested. That is why four of the nine exchange
weights sit slightly above one, a value the decomposition cannot really take.

The scatter is not small. A single run lands anywhere from 0.33 below the truth
to 0.28 above it, and that holds across the whole grid, not only where the two
venues correct at similar speeds. One token's weight is therefore a weak
reading on its own, and no weight in this post should be read as a point
estimate.

What survives that scatter is the ordering. Across the 60 runs where the true
weight is plainly one-sided the estimator picks the right leader 98 percent of
the time. Nearer an even split the grid holds a single point, and there it is
right in 11 of 12 runs, which is a direction rather than a rate. The runs where
the truth is an even split are excluded from both, because neither venue leads
in them and there is nothing for the estimator to recover. So the post never
rests on one weight. It rests on 21 of 23 pair-days pointing the same way
across three days, and underneath the weights, on the correction speeds: in the
first day's panel the pool closes 22 to 74 percent of the gap per observation
while the exchange closes at most 8. Those speeds are read straight off the fit
rather than through the ratio that forms the weight, and they are what the
ordering is built on. Pool-against-pool weights land near even, where the
estimator is weakest, so they are reported as a scale and not a ranking.

### Provenance

Within a pass the 24-hour volumes are a snapshot taken when the universe was
built and the minute bars were pulled afterwards, so the two are minutes apart
rather than simultaneous. Each daily pass carries its own snapshot in
`raw/<day>/universe.csv` and borrows nothing from the days before it.

The bar CSVs carry epoch timestamps per row, so the series passes date
themselves, and those timestamps say something the pass labels do not. Each
pass is the last thousand minutes before it ran, so its window reaches back
into the previous calendar day: the three run from 28 July 23:35 to 29 July
16:20, from 29 July 15:39 to 30 July 10:02, and from 30 July 18:02 to 31 July
10:48, all UTC. A pass named for 31 July is therefore mostly the evening of the
30th, which is the same fact the open-against-shut split turns on. The two
earlier panels carry no timestamps at all, and their date is the date they were
committed.

The registry check is a live read of the issuer's list and of the
second-opinion registry, and `data/registry_check.csv` is the answer those
endpoints gave when it was committed. A list can be edited after the fact, so
the committed file is a record of what was published then rather than a
standing guarantee; rerunning `analysis/registry.py` says what is published
now.

### Reproducing

All of it lives in one repository,
[mkzung/xstocks-price-discovery](https://github.com/mkzung/xstocks-price-discovery):
the code, the tests that hold each estimator to an answer it was not told, and
`analysis/verify.py`, which reads every number in this post back out of the
CSVs and exits non-zero if one has drifted. Every path below that starts
`analysis/`, `tests/` or `raw/` is relative to it. The `data/` files named
through the post are mirrored beside it as well, so those resolve wherever it
is published.

Reproducibility splits by pass. Everything drawn from the three series passes
re-fits from the committed minute series in `raw/`: every robustness check, the
daily comparison, the vector and session splits. The two earliest passes, the
universe snapshot and the session panel, kept only their outputs, so their
tables are reported rather than re-fittable, and the series passes carry the
same claims where it matters. The modules behind them, `analysis/panel.py` for
the session split and `analysis/venues.py` for the second exchange and the
pool-against-pool controls, will run, but they collect afresh from the live
endpoints rather than replaying those windows, which no longer exist.

```bash
pip install -r requirements.txt
python -m pytest tests -q                          # known-answer tests
python analysis/verify.py                          # every number, against data/
python analysis/calibrate.py                       # what the fit does to a known answer
python analysis/staleness.py                       # can sparse trading fake this
python analysis/robustness.py 2026-07-29b          # the series pass
python analysis/vector.py 2026-07-29b              # imposed vector against fitted
python analysis/sensitivity.py 2026-07-29b         # lags, grid, artefact risk
python analysis/robustness.py 2026-07-30           # the second day
python analysis/vector.py 2026-07-30               # its cointegrating vector
python analysis/robustness.py 2026-07-31           # the third day
python analysis/vector.py 2026-07-31               # its cointegrating vector
python analysis/windows.py 2026-07-29b 2026-07-30 2026-07-31  # across the calendar
python analysis/registry.py                        # mints against the issuer's own list
python analysis/sessions.py                        # open-against-shut, from the series
python analysis/dependence.py                      # are the pairs separate draws
python analysis/threshold.py                       # what the pairs below the floor say
python analysis/alignment.py                       # do both tapes mean the same instant
python analysis/spacing.py                         # does row spacing predict the reading
python analysis/build_analysis.py                  # redraw every figure
python analysis/format_post.py --check             # wrapping is settled
python analysis/check_post.py                      # formatting, spelling, links
```

A fresh window is a new directory, never an overwrite:

```bash
python analysis/collect_raw.py 2026-08-05 --refresh-universe
```

## Scope

One issuer's tokenized equities, one listing exchange plus one control
exchange, Solana pools only, minute bars, and three consecutive days at the end
of July 2026. Nothing here is a claim about other issuers, other chains,
coarser horizons, or other months.

The underlying equities trade on NYSE and NASDAQ, and during US hours both
venues in every pair are importing a price from there, not discovering it. The
open-against-shut split separates the two regimes and the answer holds in both,
but no third leg reads the primary listing, so this measures which of the two
crypto venues moves first, not where the price is born.

The daily series passes rank only pairs with at least 120 paired minutes, a
floor the sensitivity check above probes rather than clears; the first day's
session panel used a looser gate of eighty minutes and twenty moves per side,
and its two thinnest rows are named where they appear. Near-even weights are
read as shared discovery, never as a lead. The volume finding makes no claim
that any print is fake, only that for a quarter of these listings nothing
outside the exchange could tell you either way.
