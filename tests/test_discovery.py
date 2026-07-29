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
def test_known_weight_is_recovered_within_the_calibrated_bias(
    adjust_a: float, adjust_b: float
) -> None:
    # The construction fixes the answer at adjust_b / (adjust_a + adjust_b);
    # the fit is biased upward by up to 0.12, as recorded in the module.
    truth = adjust_b / (adjust_a + adjust_b)
    a, b = simulate_leader_follower(adjust_a=adjust_a, adjust_b=adjust_b, seed=0)
    r = information_share(a, b)
    assert r.weight_a == pytest.approx(truth, abs=0.12)
    assert r.weight_a >= truth - 1e-9  # the bias is upward, never downward


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
