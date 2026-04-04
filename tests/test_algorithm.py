"""Unit tests for the pure algorithm functions in app.py."""

import math

import pytest

from src.app import compute_distance, compute_mouse_distance, mean_and_std


class TestMeanAndStd:
    def test_single_sample_returns_default_std(self):
        means, stds = mean_and_std([[100.0, 200.0, 150.0]])
        assert means == [100.0, 200.0, 150.0]
        assert stds == [30.0, 30.0, 30.0]

    def test_two_samples_mean(self):
        means, _ = mean_and_std([[100.0, 200.0], [200.0, 100.0]])
        assert means == [150.0, 150.0]

    def test_two_samples_std(self):
        _, stds = mean_and_std([[100.0], [200.0]])
        expected = math.sqrt(((100 - 150) ** 2 + (200 - 150) ** 2) / 1)
        assert stds[0] == pytest.approx(expected, rel=1e-6)

    def test_identical_samples_produce_zero_std(self):
        _, stds = mean_and_std([[80.0, 120.0]] * 4)
        assert stds == [0.0, 0.0]

    def test_five_samples_mean_accuracy(self):
        values = [[float(i * 10)] for i in range(1, 6)]  # 10, 20, 30, 40, 50
        means, _ = mean_and_std(values)
        assert means[0] == pytest.approx(30.0)

    def test_length_preserved(self):
        samples = [[1.0, 2.0, 3.0, 4.0, 5.0]] * 3
        means, stds = mean_and_std(samples)
        assert len(means) == 5
        assert len(stds) == 5


class TestComputeDistance:
    @staticmethod
    def _profile(
        dwell_mean: float = 100.0,
        dwell_std: float = 10.0,
        flight_mean: float = 50.0,
        flight_std: float = 5.0,
    ) -> dict:
        return {
            "mean_dwell": [dwell_mean],
            "std_dwell": [dwell_std],
            "mean_flight": [flight_mean],
            "std_flight": [flight_std],
        }

    def test_identical_timing_is_zero(self):
        profile = self._profile()
        timing = {"dwell": [100.0], "flight": [50.0]}
        assert compute_distance(timing, profile) == pytest.approx(0.0)

    def test_distance_positive_for_different_timing(self):
        profile = self._profile()
        timing = {"dwell": [150.0], "flight": [80.0]}
        assert compute_distance(timing, profile) > 0.0

    def test_high_std_reduces_distance(self):
        tight = self._profile(dwell_std=5.0, flight_std=5.0)
        loose = self._profile(dwell_std=100.0, flight_std=100.0)
        timing = {"dwell": [110.0], "flight": [60.0]}
        assert compute_distance(timing, tight) > compute_distance(timing, loose)

    def test_dwell_floor_applied(self):
        # std=1 should clamp to floor=15; deviation of 15ms → normalised dist of 1.0
        profile = self._profile(dwell_std=1.0, flight_std=1.0)
        timing = {"dwell": [115.0], "flight": [75.0]}
        # dwell: |115-100|/15 = 1.0,  flight: |75-50|/25 = 1.0 → avg = 1.0
        assert compute_distance(timing, profile) == pytest.approx(1.0, rel=0.01)

    def test_empty_arrays_return_infinity(self):
        profile = {
            "mean_dwell": [],
            "std_dwell": [],
            "mean_flight": [],
            "std_flight": [],
        }
        timing = {"dwell": [], "flight": []}
        assert compute_distance(timing, profile) == float("inf")

    def test_symmetric_deviation_is_consistent(self):
        profile = self._profile(dwell_mean=100.0, dwell_std=10.0)
        above = compute_distance({"dwell": [110.0], "flight": [50.0]}, profile)
        below = compute_distance({"dwell": [90.0], "flight": [50.0]}, profile)
        assert above == pytest.approx(below, rel=1e-6)


class TestComputeMouseDistance:
    """Tests for compute_mouse_distance — normalised Manhattan distance for mouse dynamics."""

    N_SEG = 7   # movement_times and curvatures length
    N_TGT = 8   # click_dwells length

    @staticmethod
    def _profile(
        mt_mean: float = 300.0,
        mt_std: float = 30.0,
        cd_mean: float = 80.0,
        cd_std: float = 10.0,
        cv_mean: float = 0.1,
        cv_std: float = 0.02,
    ) -> dict:
        n_seg, n_tgt = TestComputeMouseDistance.N_SEG, TestComputeMouseDistance.N_TGT
        return {
            "mean_movement_times": [mt_mean] * n_seg,
            "std_movement_times": [mt_std] * n_seg,
            "mean_click_dwells": [cd_mean] * n_tgt,
            "std_click_dwells": [cd_std] * n_tgt,
            "mean_curvatures": [cv_mean] * n_seg,
            "std_curvatures": [cv_std] * n_seg,
        }

    @staticmethod
    def _sample(
        mt: float = 300.0,
        cd: float = 80.0,
        cv: float = 0.1,
    ) -> dict:
        n_seg, n_tgt = TestComputeMouseDistance.N_SEG, TestComputeMouseDistance.N_TGT
        return {
            "movement_times": [mt] * n_seg,
            "click_dwells": [cd] * n_tgt,
            "curvatures": [cv] * n_seg,
        }

    def test_identical_sample_is_zero(self):
        profile = self._profile()
        sample = self._sample()
        assert compute_mouse_distance(sample, profile) == pytest.approx(0.0)

    def test_distance_positive_for_different_sample(self):
        profile = self._profile()
        sample = self._sample(mt=400.0, cd=120.0, cv=0.2)
        assert compute_mouse_distance(sample, profile) > 0.0

    def test_high_std_reduces_distance(self):
        tight = self._profile(mt_std=10.0, cd_std=5.0, cv_std=0.01)
        loose = self._profile(mt_std=500.0, cd_std=300.0, cv_std=1.0)
        sample = self._sample(mt=350.0, cd=100.0, cv=0.15)
        assert compute_mouse_distance(sample, tight) > compute_mouse_distance(sample, loose)

    def test_floor_applied_to_movement_time(self):
        # std=1 should clamp to floor=30; deviation of 30ms → contribution 1.0
        profile = self._profile(mt_mean=300.0, mt_std=1.0, cd_std=1.0, cv_std=1.0)
        sample = self._sample(mt=330.0, cd=80.0, cv=0.1)
        dist = compute_mouse_distance(sample, profile)
        assert dist > 0.0

    def test_empty_arrays_return_infinity(self):
        profile = {
            "mean_movement_times": [],
            "std_movement_times": [],
            "mean_click_dwells": [],
            "std_click_dwells": [],
            "mean_curvatures": [],
            "std_curvatures": [],
        }
        sample = {"movement_times": [], "click_dwells": [], "curvatures": []}
        assert compute_mouse_distance(sample, profile) == float("inf")

    def test_symmetric_deviation_is_consistent(self):
        profile = self._profile(mt_mean=300.0, mt_std=30.0)
        above = compute_mouse_distance(self._sample(mt=330.0), profile)
        below = compute_mouse_distance(self._sample(mt=270.0), profile)
        assert above == pytest.approx(below, rel=1e-6)
