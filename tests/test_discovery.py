"""The estimator has to recover a leader it was never told about."""

from __future__ import annotations

import sys
from pathlib import Path

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
