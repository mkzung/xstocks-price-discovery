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


def test_spearman_matches_a_hand_computed_case() -> None:
    # Perfectly reversed orders must give exactly -1, and identical orders +1,
    # so the no-scipy implementation is doing what its name says.
    import pandas as pd

    from analysis.relation import spearman

    a = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert spearman(a, a) == pytest.approx(1.0)
    assert spearman(a, a[::-1].reset_index(drop=True)) == pytest.approx(-1.0)
    assert abs(spearman(a, pd.Series([2.0, 1.0, 4.0, 3.0, 5.0]))) < 1.0


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
