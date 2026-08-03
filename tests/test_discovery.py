"""The estimator has to recover a leader it was never told about."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.discovery import information_share, simulate_leader_follower  # noqa: E402


def test_pure_leader_is_recovered() -> None:
    # A never corrects, B closes the gap: A must take essentially all weight.
    a, b = simulate_leader_follower(adjust_a=0.0, adjust_b=0.4, seed=0)
    r = information_share(a, b)
    assert r.weight_a > 0.9
    assert r.weight_a + r.weight_b == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("adjust_a, adjust_b", [(0.0, 0.4), (0.1, 0.4),
                                                (0.2, 0.2), (0.4, 0.1)])
def test_known_weight_is_recovered_on_average_across_seeds(
    adjust_a: float, adjust_b: float
) -> None:
    # The construction fixes the answer at adjust_b / (adjust_a + adjust_b).
    #
    # An earlier version of this test ran one seed and asserted the error was
    # within 0.12 and never negative. Both hold on seed 0 and neither holds in
    # general: over the calibration grid 21 of 72 runs come out below the truth
    # and 16 miss by more than 0.12. The test was green because of the seed.
    #
    # What is true across seeds is that the mean sits just above the truth.
    truth = adjust_b / (adjust_a + adjust_b)
    fits = [information_share(*simulate_leader_follower(
        adjust_a=adjust_a, adjust_b=adjust_b, seed=s)).weight_a
        for s in range(12)]
    mean = sum(fits) / len(fits)
    assert mean == pytest.approx(truth, abs=0.06)
    assert mean >= truth  # the bias is upward in the mean, not run by run


@pytest.mark.parametrize("adjust_a, adjust_b", [(0.0, 0.4), (0.1, 0.4),
                                                (0.4, 0.1)])
def test_single_runs_scatter_by_up_to_a_third(
    adjust_a: float, adjust_b: float
) -> None:
    # The scatter the post has to declare. If this bound ever tightens, the
    # post's stated limit is too pessimistic and should be retightened with it.
    truth = adjust_b / (adjust_a + adjust_b)
    errors = [information_share(*simulate_leader_follower(
        adjust_a=adjust_a, adjust_b=adjust_b, seed=s)).weight_a - truth
        for s in range(12)]
    assert max(abs(e) for e in errors) <= 0.35


def test_the_leader_is_picked_far_more_often_than_chance() -> None:
    # The claim the post actually rests on. Individual weights are noisy; what
    # has to hold is that the venue correcting less comes out ahead.
    right = total = 0
    for adjust_a, adjust_b in [(0.0, 0.4), (0.05, 0.4), (0.1, 0.4),
                               (0.2, 0.4), (0.4, 0.1), (0.4, 0.05)]:
        truth = adjust_b / (adjust_a + adjust_b)
        for seed in range(12):
            fit = information_share(*simulate_leader_follower(
                adjust_a=adjust_a, adjust_b=adjust_b, seed=seed))
            right += (fit.weight_a > 0.5) == (truth > 0.5)
            total += 1
    assert right / total >= 0.9


def test_hasbrouck_bounds_collapse_on_their_own_analytic_value() -> None:
    # A Hasbrouck information share is not a Gonzalo-Granger weight and there
    # is no reason for them to agree in magnitude. Hasbrouck splits the
    # variance of the efficient price innovation, so with uncorrelated
    # innovations and equal venue variances the share reduces to
    #
    #     IS_a = w_a^2 / (w_a^2 + w_b^2)
    #
    # For a Gonzalo-Granger weight of 0.8 that is 0.64/0.68, about 0.94, not
    # 0.8. Asserting the two should match was the mistake this test was written
    # with; the analytic value is what the bounds must close on.
    from analysis.discovery import hasbrouck_share

    # The expected value is built from the weight the fit produced, not from
    # the weight the simulation was built with. That isolates the Hasbrouck
    # transformation, which is what this test is for, from the separate upward
    # bias in the weight itself, which its own tests already cover.
    for adjust_a, adjust_b in [(0.1, 0.4), (0.4, 0.1), (0.2, 0.4), (0.4, 0.2)]:
        prices = simulate_leader_follower(
            adjust_a=adjust_a, adjust_b=adjust_b, venue_shock=0.02, seed=0)
        gg = information_share(*prices)
        expected = gg.weight_a ** 2 / (gg.weight_a ** 2 + gg.weight_b ** 2)
        h = hasbrouck_share(*prices)
        assert abs(h.correlation) < 0.1
        assert h.upper - h.lower < 0.05
        assert h.midpoint == pytest.approx(expected, abs=0.02)


def test_hasbrouck_and_gonzalo_granger_agree_on_who_leads() -> None:
    # The two decompositions differ in magnitude and must not differ in
    # direction. Where they do, the data cannot settle the question and the
    # post has to say so rather than pick the friendlier number.
    from analysis.discovery import hasbrouck_share

    for adjust_a, adjust_b in [(0.0, 0.4), (0.1, 0.4), (0.2, 0.4),
                               (0.4, 0.2), (0.4, 0.1), (0.4, 0.0)]:
        prices = simulate_leader_follower(
            adjust_a=adjust_a, adjust_b=adjust_b, venue_shock=0.02, seed=0)
        gg = information_share(*prices).weight_a
        hb = hasbrouck_share(*prices)
        assert (gg > 0.5) == (hb.midpoint > 0.5)


def test_hasbrouck_bounds_are_wide_when_the_venues_move_together() -> None:
    # The other half of the same property, and the reason the post has to
    # report a range rather than a number: with a small venue-specific shock
    # the innovations are nearly collinear and the split is not identified.
    from analysis.discovery import hasbrouck_share

    h = hasbrouck_share(*simulate_leader_follower(
        adjust_a=0.0, adjust_b=0.4, venue_shock=0.0005, seed=0))
    assert h.correlation > 0.9
    assert h.upper - h.lower > 0.5


def test_hasbrouck_share_stays_within_zero_and_one() -> None:
    # A variance share that leaves the unit interval means the decomposition
    # has been mis-assembled, which no amount of eyeballing would catch.
    from analysis.discovery import hasbrouck_share

    for seed in range(6):
        h = hasbrouck_share(*simulate_leader_follower(
            adjust_a=0.15, adjust_b=0.35, seed=seed))
        assert 0.0 <= h.lower <= h.upper <= 1.0


def test_ranking_is_recovered_in_every_configuration() -> None:
    # Weaker claim than the magnitude and the one the post relies on: whoever
    # corrects less must come out ahead, in every pairing tested.
    for adjust_a, adjust_b in [(0.0, 0.4), (0.1, 0.4), (0.4, 0.1), (0.4, 0.05)]:
        a, b = simulate_leader_follower(adjust_a=adjust_a, adjust_b=adjust_b, seed=1)
        r = information_share(a, b)
        assert (r.weight_a > r.weight_b) == (adjust_a < adjust_b)


def test_roles_swap_when_the_leader_swaps() -> None:
    # Same simulation read the other way round: the weights must swap too, so
    # the estimator is reading the data and not the argument order.
    a, b = simulate_leader_follower(adjust_a=0.0, adjust_b=0.4, seed=1)
    forward = information_share(a, b)
    reverse = information_share(b, a)
    assert forward.weight_a == pytest.approx(reverse.weight_b, abs=1e-6)


def test_shared_discovery_averages_to_even() -> None:
    # Both venues correct equally, so the truth is 0.5. Single runs scatter
    # widely because the denominator is the difference of two similar speeds,
    # so the property that holds is the average over seeds, and the module
    # says as much about reading near-even numbers.
    weights = [information_share(*simulate_leader_follower(
        adjust_a=0.25, adjust_b=0.25, seed=s)).weight_a for s in range(12)]
    assert sum(weights) / len(weights) == pytest.approx(0.5, abs=0.15)


def test_follower_speed_has_the_correcting_sign() -> None:
    # The follower is the venue that closes the gap, so its speed pulls it back
    # toward the leader while the leader barely reacts.
    a, b = simulate_leader_follower(adjust_a=0.0, adjust_b=0.5, seed=3)
    r = information_share(a, b)
    assert r.speed_b > abs(r.speed_a)


def test_bootstrap_recovers_the_leader_it_was_not_told_about() -> None:
    # The bootstrap has to separate a known leader from a known follower on a
    # long sample. An earlier version resampled blocks of the price levels,
    # which splices two cointegrated series and puts a jump in the spread at
    # every seam; it reported 65 percent for a true leader and 45 percent for a
    # true follower, which is no signal. Resampling the fitted regression rows
    # fixed it, and this test is what would have caught the original.
    from analysis.bootstrap import block_bootstrap

    leader = block_bootstrap(*simulate_leader_follower(
        n=4000, adjust_a=0.0, adjust_b=0.4, seed=0), draws=200)
    follower = block_bootstrap(*simulate_leader_follower(
        n=4000, adjust_a=0.4, adjust_b=0.0, seed=0), draws=200)
    assert leader.lead_share > 0.9
    assert follower.lead_share < 0.1
    assert leader.speeds_are_separated()


def test_bootstrap_is_uninformative_on_a_short_sample() -> None:
    # The property that makes the interval worth reporting: a token with a few
    # hundred paired minutes cannot establish its own leader, so the post must
    # not lean on one.
    from analysis.bootstrap import block_bootstrap

    short = block_bootstrap(*simulate_leader_follower(
        n=300, adjust_a=0.0, adjust_b=0.4, seed=0), draws=200)
    assert 0.2 < short.lead_share < 0.8


def test_sign_test_matches_the_binomial() -> None:
    from math import comb

    from analysis.bootstrap import sign_test

    for led, total in [(9, 9), (8, 9), (5, 9), (7, 7), (0, 6)]:
        extreme = max(led, total - led)
        expected = min(1.0, 2 * sum(comb(total, k)
                                    for k in range(extreme, total + 1)) / 2 ** total)
        assert sign_test(led, total) == pytest.approx(expected)



def test_sign_test_refuses_an_empty_sample() -> None:
    # The guard on an empty tally was uncovered: relaxing it from `total <= 0`
    # to `total < 0` left every test green, so nothing said what the function
    # does when there is nothing to test. Zero pairs is not evidence of
    # anything and must not come back as a p-value of 1.
    import math

    from analysis.bootstrap import sign_test

    assert math.isnan(sign_test(0, 0))
    assert math.isnan(sign_test(3, -1))

def test_sparse_sampling_does_not_manufacture_a_leader() -> None:
    # The objection that would sink the study. A pool that trades in a fraction
    # of minutes could look like a follower purely through sampling. Dropping
    # untraded minutes, which is what the pipeline does, must not flip a known
    # pool leader into an apparent exchange leader.
    from analysis.staleness import drop_sample, stale_sample

    flips_drop = flips_hold = 0
    for seed in range(12):
        pool, cex = simulate_leader_follower(adjust_a=0.0, adjust_b=0.4, seed=seed)
        for sampler, counter in ((drop_sample, "drop"), (stale_sample, "hold")):
            sparse = sampler(pool, 0.3, seed=seed + 99)
            paired = pd.concat([cex.rename("c"), sparse.rename("p")],
                               axis=1).dropna()
            weight = information_share(paired["c"], paired["p"]).weight_a
            if weight > 0.5:
                if counter == "drop":
                    flips_drop += 1
                else:
                    flips_hold += 1
    # Holding a stale price forward does manufacture the result, which is why
    # the pipeline must not do it. Dropping untraded minutes does not.
    assert flips_hold >= 10
    assert flips_drop <= 4


def test_short_samples_are_refused() -> None:
    a, b = simulate_leader_follower(n=30, seed=4)
    with pytest.raises(ValueError, match="paired observations"):
        information_share(a, b)


def test_session_mask_matches_the_us_regular_session() -> None:
    # 13:30 to 20:00 UTC on weekdays, which is the regular session on US
    # summer time; the boundary minutes and the weekend have to be right.
    import pandas as pd

    from analysis.panel import session_mask

    idx = pd.to_datetime([
        "2026-07-29 13:29", "2026-07-29 13:30", "2026-07-29 19:59",
        "2026-07-29 20:00", "2026-08-01 15:00", "2026-08-02 15:00",
    ], utc=True)
    got = session_mask(pd.DatetimeIndex(idx)).tolist()
    assert got == [False, True, True, False, False, False]


def test_adf_separates_a_random_walk_from_a_reverting_series() -> None:
    # The assumption the error-correction model rests on. If this test cannot
    # tell a wandering spread from a reverting one, the per-pair cointegration
    # results in the post mean nothing.
    import numpy as np
    import pandas as pd

    from analysis.cointegration import adf

    rng = np.random.default_rng(0)
    walk = pd.Series(np.cumsum(rng.normal(0, 0.001, 600)))
    assert not adf(walk).rejects_unit_root()

    reverting = np.zeros(600)
    for t in range(1, 600):
        reverting[t] = 0.8 * reverting[t - 1] + rng.normal(0, 0.001)
    result = adf(pd.Series(reverting))
    assert result.rejects_unit_root()
    # phi of 0.8 implies a half-life of ln(0.5)/ln(0.8), about 3.1 minutes.
    assert 2.0 < result.half_life_min < 4.5


def test_adf_rejects_at_about_its_nominal_rate() -> None:
    # A test that never rejects would pass the check above by being broken in
    # the safe direction. Size it: on true random walks it should reject near
    # five percent of the time, not zero and not thirty.
    import numpy as np
    import pandas as pd

    from analysis.cointegration import adf

    rng = np.random.default_rng(7)
    rejects = sum(
        adf(pd.Series(np.cumsum(rng.normal(0, 0.001, 400)))).rejects_unit_root()
        for _ in range(200)
    )
    assert 0.01 <= rejects / 200 <= 0.12


def test_fitted_vector_recovers_a_scaling_that_is_really_there() -> None:
    # The model imposes a cointegrating vector of (1, -1). If the estimator
    # cannot see a scaling when one exists, the check that the imposition is
    # harmless proves nothing.
    import numpy as np

    from analysis.vector import estimate_vector

    a, b = simulate_leader_follower(n=4000, adjust_a=0.0, adjust_b=0.4, seed=0)
    beta, se, _ = estimate_vector(a, b)
    assert beta == pytest.approx(1.0, abs=0.05)

    # Same series with venue A's log price stretched by 1.3.
    stretched = pd.Series(np.exp(1.3 * np.log(a)), index=a.index)
    beta_stretched, _, _ = estimate_vector(stretched, b)
    assert beta_stretched == pytest.approx(1.3, abs=0.05)
    assert beta_stretched - beta > 0.2


def test_attenuation_bracket_contains_one_when_the_truth_is_one() -> None:
    # Noise in a regressor drags its slope toward zero, so a fitted slope below
    # one is not evidence against a one-for-one relation. The bracket between
    # the two one-sided regressions is what has to contain one.
    from analysis.vector import attenuation_bounds

    for noise in (0.0, 0.001, 0.004):
        a, b = simulate_leader_follower(n=4000, adjust_a=0.1, adjust_b=0.4,
                                        noise=noise, seed=0)
        low, high = attenuation_bounds(a, b)
        assert low <= 1.0 <= high
    # And the bracket has to widen as the noise grows, or it is not measuring
    # attenuation at all.
    quiet = attenuation_bounds(*simulate_leader_follower(
        n=4000, adjust_a=0.1, adjust_b=0.4, noise=0.0, seed=0))
    noisy = attenuation_bounds(*simulate_leader_follower(
        n=4000, adjust_a=0.1, adjust_b=0.4, noise=0.004, seed=0))
    assert (noisy[1] - noisy[0]) > (quiet[1] - quiet[0])


def test_imposing_the_vector_matches_fitting_it_when_it_holds() -> None:
    from analysis.vector import fit_with_vector

    a, b = simulate_leader_follower(n=4000, adjust_a=0.0, adjust_b=0.4, seed=0)
    imposed = fit_with_vector(a, b, beta=1.0)
    reference = information_share(a, b)
    assert imposed.weight_a == pytest.approx(reference.weight_a, abs=1e-9)
    assert imposed.speed_a == pytest.approx(reference.speed_a, abs=1e-9)


def test_spearman_matches_a_hand_computed_case() -> None:
    # Perfectly reversed orders must give exactly -1, and identical orders +1,
    # so the no-scipy implementation is doing what its name says.
    import numpy as np
    import pandas as pd

    from analysis.relation import spearman

    a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert spearman(a, a) == pytest.approx(1.0)
    assert spearman(a, a[::-1].reset_index(drop=True)) == pytest.approx(-1.0)
    assert abs(spearman(a, pd.Series([2.0, 1.0, 4.0, 3.0, 5.0]))) < 1.0

    # The three assertions above pass just as happily on a Pearson
    # correlation, because the ranks of 1..5 are 1..5 and the two coincide on
    # data like that. Dropping the .rank() calls from the implementation left
    # the whole suite green, which is a test agreeing with itself rather than
    # checking anything. This case separates them: the relation is perfectly
    # monotone, so a rank correlation is exactly 1, while Pearson sees the
    # curvature and lands near 0.66. It is the property the study leans on,
    # since the volume ratios it correlates span four and a half orders of
    # magnitude.
    steps = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    powers = pd.Series([1.0, 1e1, 1e2, 1e3, 1e4, 1e6])
    assert spearman(steps, powers) == pytest.approx(1.0)
    assert np.corrcoef(steps, powers)[0, 1] < 0.7


def test_permutation_test_calls_noise_noise() -> None:
    # Unrelated series must not come out significant; a real relation must.
    import numpy as np
    import pandas as pd

    from analysis.relation import test_relation

    rng = np.random.default_rng(0)
    noise_x = pd.Series(rng.normal(size=40))
    noise_y = pd.Series(rng.normal(size=40))
    assert test_relation(noise_x, noise_y, draws=2000).p_value > 0.05

    monotone = pd.Series(range(40))
    assert test_relation(monotone, monotone, draws=2000).p_value < 0.01


def test_a_change_across_a_gap_is_not_a_one_minute_change() -> None:
    # The first version of the dependence module differenced a sparse series
    # directly, which turns a jump across a seven-minute hole into a "one
    # minute change" and inflates every correlation built on it. Only steps
    # where the previous bar is exactly sixty seconds earlier may survive.
    import pandas as pd

    from analysis.dependence import minute_changes

    stamps = pd.to_datetime([0, 60, 120, 600, 660], unit="s", utc=True)
    series = pd.Series([1.0, 2.0, 3.0, 99.0, 100.0], index=stamps)

    changes = minute_changes(series)
    assert list(changes) == [1.0, 1.0, 1.0]
    assert 96.0 not in list(changes)
    assert len(series.diff().dropna()) == 4


def test_effective_pairs_discounts_only_what_is_shared() -> None:
    # Independent pairs must be worth their count, perfectly shared ones must
    # collapse to a single observation, and a negative correlation must not be
    # allowed to manufacture extra evidence.
    from analysis.dependence import effective_pairs

    assert effective_pairs(7, 0.0) == pytest.approx(7.0)
    assert effective_pairs(7, 1.0) == pytest.approx(1.0)
    assert effective_pairs(7, -0.5) == pytest.approx(7.0)
    assert effective_pairs(7, 0.12) < 7.0
    assert effective_pairs(7, 0.12) > effective_pairs(7, 0.30)


def test_the_floor_is_applied_to_the_sample_not_the_answer() -> None:
    # The threshold table exists to show the 120-minute floor does not select
    # on the outcome, which it can only do if membership is decided by sample
    # size alone. A row above the floor marked as dropped, or one below it
    # marked as kept, would mean the cut is reading something else.
    import pandas as pd

    from analysis.robustness import MIN_PAIRED

    table = pd.read_csv("data/threshold.csv")
    assert (table[table.kept].minutes >= MIN_PAIRED).all()
    assert (table[~table.kept].minutes < MIN_PAIRED).all()


def test_every_bar_reader_takes_the_close() -> None:
    # Each venue's array orders its fields differently and nothing pinned which
    # index meant what. Gate's reader took field five, the open, while the pool
    # reader took the close, so the two series described instants a minute
    # apart at every stamp. These payloads are shaped like the real ones, with
    # a distinct value in every slot, so an index swapped in any reader shows
    # up as the wrong number rather than as a subtle lead.
    import analysis.collect as collect
    import analysis.venues as venues

    gate = [["1700000000", "9999", "222", "333", "111", "555", "88", "true"]]
    gecko = {"data": {"attributes": {"ohlcv_list":
             [[1700000000, 111.0, 333.0, 44.0, 222.0, 88.0]]}}}
    bybit = {"result": {"list":
             [["1700000000000", "111", "333", "44", "222", "88", "9999"]]}}
    mexc = [[1700000000000, "111", "333", "44", "222", "88", 1700000059999, "9"]]

    collect._get = lambda url: gecko if "geckoterminal" in url else gate
    venues._get = lambda url: bybit if "bybit" in url else mexc

    # 222 is the close in every one of the four layouts above.
    assert collect.cex_bars("X_USDT").iloc[0] == pytest.approx(222.0)
    assert collect.dex_bars("pool").iloc[0] == pytest.approx(222.0)
    assert venues.bybit_bars("XUSDT").iloc[0] == pytest.approx(222.0)
    assert venues.mexc_bars("XUSDT").iloc[0] == pytest.approx(222.0)

    # And every reader stamps the bar with the second it opens, not milliseconds.
    assert collect.cex_bars("X_USDT").index[0] == 1700000000
    assert venues.bybit_bars("XUSDT").index[0] == 1700000000


def test_realigning_puts_both_venues_on_one_instant() -> None:
    # Built so the answer is known. One price path, quoted by both venues with
    # no lead either way: the exchange column holds each minute's open, which
    # is the path at that minute, and the pool column holds each minute's
    # close, which is the path a minute later. As collected the two columns
    # differ by one step even though nothing led anything. Realigned they must
    # agree to the last digit, because they are then the same instant.
    import pandas as pd

    from analysis.alignment import realign

    path = [100.0, 101.0, 103.0, 106.0, 110.0, 115.0]
    stamps = [0, 60, 120, 180, 240, 300]
    paired = pd.DataFrame({"cex": path, "dex": path[1:] + [121.0]}, index=stamps)

    assert not (paired.cex == paired.dex).any()
    fixed = realign(paired)
    assert list(fixed.cex) == list(fixed.dex)
    assert len(fixed) == len(paired) - 1


def test_realigning_refuses_to_step_across_a_gap() -> None:
    # The next row is only the next minute if it is sixty seconds later. Where
    # collection dropped a minute, taking the following row would hand the
    # exchange a price from further in the future than the pool's, which is the
    # error this function exists to remove, in the other direction.
    import pandas as pd

    from analysis.alignment import realign

    stamps = [0, 60, 300, 360]
    paired = pd.DataFrame({"cex": [1.0, 2.0, 3.0, 4.0],
                           "dex": [9.0, 9.0, 9.0, 9.0]}, index=stamps)

    fixed = realign(paired)
    assert list(fixed.index) == [0, 300]
    assert list(fixed.cex) == [2.0, 4.0]


def test_the_lag_profile_finds_a_planted_one_minute_offset() -> None:
    # A pool series that is the exchange series one minute ahead must peak at
    # plus one and nowhere else. This is the measurement that caught the real
    # misalignment, so it is held to a case where the offset was put there on
    # purpose.
    import numpy as np
    import pandas as pd

    from analysis.alignment import lag_profile

    rng = np.random.default_rng(0)
    path = 100 * np.exp(np.cumsum(rng.normal(scale=1e-4, size=400)))
    stamps = [60 * i for i in range(len(path) - 1)]
    paired = pd.DataFrame({"cex": path[:-1], "dex": path[1:]}, index=stamps)

    profile = lag_profile(paired)
    assert max(profile, key=lambda k: profile[k]) == 1
    assert profile[1] == pytest.approx(1.0, abs=1e-9)
    assert abs(profile[0]) < 0.2


def test_the_floor_table_splits_on_sample_size_alone() -> None:
    # threshold.below_the_floor exists to show the paired-minute floor does not
    # select on the outcome, so its own split has to be decided by nothing but
    # the row count, and a pair too short for the estimator has to come back
    # with no weight rather than a fabricated one.
    import pandas as pd

    from analysis.robustness import MIN_PAIRED
    from analysis.threshold import below_the_floor

    table = below_the_floor("2026-07-29b")
    assert (table[table.kept].minutes >= MIN_PAIRED).all()
    assert (table[~table.kept].minutes < MIN_PAIRED).all()
    assert table[table.w_cex.isna()].minutes.max() < MIN_PAIRED
    assert pd.notna(table[table.kept].w_cex).all()


def test_each_coverage_row_describes_its_own_series() -> None:
    # coverage.csv is where the post's fill rates and gap structure come from,
    # and nothing recomputed it from the minutes it summarises. Every field is
    # derivable, so every field is derived here: a stale summary beside a
    # re-collected series would otherwise put wrong fill rates into the
    # write-up with every other check still green.
    import numpy as np
    import pandas as pd

    for label in ("2026-07-29b", "2026-07-30", "2026-07-31"):
        folder = Path("raw") / label
        coverage = pd.read_csv(folder / "coverage.csv").set_index("symbol")
        for symbol, row in coverage.iterrows():
            series = pd.read_csv(folder / f"{symbol}.csv", index_col="ts")
            stamps = np.sort(series.index.to_numpy())
            gaps = np.diff(stamps) // 60

            assert int(row.paired_minutes) == len(stamps), symbol
            assert row.fill_rate == pytest.approx(
                round(len(stamps) / int(row.window_minutes), 4)), symbol
            assert int(row.first_ts) == int(stamps.min()), symbol
            assert int(row.last_ts) == int(stamps.max()), symbol
            if len(stamps) > 1:
                assert int(row.median_gap_min) == int(np.median(gaps)), symbol
                assert int(row.max_gap_min) == int(gaps.max()), symbol
                assert row.consecutive_share == pytest.approx(
                    round(float((gaps == 1).mean()), 4)), symbol


def test_no_series_file_is_missing_from_its_coverage() -> None:
    # And the other direction: a token collected but left out of the summary
    # would be invisible to every count the post makes.
    import pandas as pd

    for label in ("2026-07-29b", "2026-07-30", "2026-07-31"):
        folder = Path("raw") / label
        listed = set(pd.read_csv(folder / "coverage.csv").symbol)
        on_disk = {p.stem for p in folder.glob("*.csv")} - {"coverage", "universe"}
        assert on_disk == listed, f"{label}: {on_disk ^ listed}"


def test_every_written_table_has_a_total_order() -> None:
    # pandas' default sort is not stable, so a table sorted on a key that ties
    # comes out in a different row order on a different machine. That is how
    # the workflow's artefact diff failed on CI while passing here: nothing but
    # row order moved. Each writer now sorts on a key that cannot tie, and this
    # asserts the key really is unique and the file really is in that order.
    import pandas as pd

    ordered = {
        "robustness_2026-07-29b.csv": (["paired_minutes", "symbol"], [False, True]),
        "robustness_2026-07-30.csv": (["paired_minutes", "symbol"], [False, True]),
        "robustness_2026-07-31.csv": (["paired_minutes", "symbol"], [False, True]),
        "threshold.csv": (["window", "minutes", "symbol"], [True, False, True]),
        "alignment.csv": (["window", "symbol"], [True, True]),
        "dependence.csv": (["window", "leg"], [True, True]),
        "sensitivity_staleness_2026-07-29b.csv": (["fill_rate", "symbol"], [False, True]),
        "collisions.csv": (["claimed_liquidity_usd", "symbol", "impostor_mint"],
                           [False, True, True]),
        "token_groups.csv": (["paired_min", "symbol"], [False, True]),
    }
    for name, (keys, ascending) in ordered.items():
        frame = pd.read_csv(Path("data") / name)
        assert not frame.duplicated(subset=keys).any(), f"{name}: key ties"
        expected = frame.sort_values(keys, ascending=ascending).reset_index(drop=True)
        assert frame.reset_index(drop=True).equals(expected), f"{name}: not in key order"

