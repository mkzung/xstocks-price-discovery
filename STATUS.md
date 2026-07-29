# xStocks price discovery: CEX against on-chain

The DN case that needs both venues. A tokenized equity trades on a centralised
exchange and on Solana at the same time, and arbitrage ties the two quotes to
one price. Volume can be manufactured on either side; the permanent price move
cannot. So the question a single-venue study cannot ask is: which venue is
actually discovering the price, and does its share of the discovery match its
share of the volume.

Method is Gonzalo-Granger common-factor weights off a two-venue error-correction
model, which is citable rather than home-made. A venue that only follows carries
a weight near zero however much volume it prints.

## Built (local, held)

- `analysis/discovery.py` - the estimator plus a simulator whose answer is known
  by construction (the weight is `adjust_b / (adjust_a + adjust_b)`).
- `tests/test_discovery.py` - 10 tests, all passing: exact recovery for a pure
  leader, recovery within the calibrated bias across four configurations, the
  ordering in every configuration, the swap test (reading the pair backwards
  swaps the weights), and the refusal on short samples.
- Data path proven end to end and free: Gate 1m candles plus GeckoTerminal 1m
  pool bars, no keys.

## Calibrated honestly, both limits written into the module

- The single-equation fit is biased upward by 0.02 to 0.12 on synthetic data,
  because a venue's transitory shock sits in the residual and in the lagged
  spread at once. The error shrinks as the spread is better identified.
- Near-even configurations are unstable: with both venues correcting equally,
  the weight scatters between 0.19 and 0.60 across seeds around a truth of 0.5.
  A near-even reading means shared discovery, not a measured lead.
- Both limits mean the weights are read as a ranking with a stated tolerance,
  and the finding a post can carry is a venue far from even that stays there.

## First real reading

CRCLX, 359 paired minutes: Gate 0.88, Raydium 0.12. Gate barely corrects
(-0.055) while the pool closes 0.40 of the gap each minute, so on this window
the centralised book leads and the pool follows. Two caveats before this means
anything: one window is not a result, and the 6 percent level gap seen between
the two quotes needs explaining before the spread can be called a pure
arbitrage error.

## Next

Widen to every xStock listed on both venues, run several days, and keep the
pairs where the ranking is stable. The post writes itself only if the volume
share and the discovery share disagree somewhere.
