"""Synthetic arithmetic boundaries must not become live battery measurements."""

import math

import pytest

from tests.runtime_loader import runtime


@pytest.mark.parametrize("capacity", [float("inf"), float("nan"), -1.0, 0.0])
def test_invalid_capacity_has_no_derived_measurements(capacity):
    result = runtime.calculate_virtual_battery(
        52.0, 10.0, [{"voltage": 52.0, "current": 4.0, "soc": 50.0}], capacity
    )
    assert result["status"] == "Invalid chain capacity"
    assert result["power"] is None
    assert result["remaining_capacity"] is None


def test_finite_inputs_that_overflow_do_not_publish_infinity():
    result = runtime.calculate_virtual_battery(
        52.0, 1e308, [{"voltage": 52.0, "current": -1e308, "soc": 50.0}], 280.0
    )
    assert result["status"] == "Calculation overflow"
    assert result["current"] is None
    assert result["power"] is None


def test_duration_is_capped_before_integer_conversion():
    result = runtime.calculate_virtual_battery(
        52.0, 10.0, [{"voltage": 52.0, "current": 9.0, "soc": 50.0}], 1e308
    )
    assert result["time_to_go"] == runtime.TIME_TO_GO_CAP_SECONDS
    assert math.isfinite(result["remaining_capacity"])
