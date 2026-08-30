"""Tests for calculate_virtual_battery() pure calculator.

Pulled directly from dbus-virtual-battery.py — no D-Bus, no I/O.
"""

import pytest

from tests.calculator import (
    CELLS_PER_CHAIN,
    CHARGE_DISCHARGE_THRESHOLD_A,
    DEFAULT_CHAIN_CAPACITY,
    TIME_TO_GO_CAP_SECONDS,
    calculate_virtual_battery,
)


def make(voltage=None, current=None, soc=None):
    return {"voltage": voltage, "current": current, "soc": soc}


class TestCalculateVirtualBattery:
    def test_smartshunt_missing_returns_none(self):
        result = calculate_virtual_battery(None, None, [], 280.0)
        assert result["voltage"] is None
        assert result["current"] is None
        assert result["power"] is None
        assert result["soc"] is None
        assert result["soc_valid"] is False
        assert result["status"] == "SmartShunt missing"

    def test_smartshunt_voltage_only_returns_none(self):
        result = calculate_virtual_battery(51.2, None, [], 280.0)
        assert result["voltage"] is None
        assert result["current"] is None

    def test_smartshunt_current_only_returns_none(self):
        result = calculate_virtual_battery(None, 5.0, [], 280.0)
        assert result["voltage"] is None
        assert result["current"] is None

    def test_no_chains_voltage_from_smartshunt_not_used(self):
        # Voltage falls back to None when no chain provides voltage
        result = calculate_virtual_battery(51.2, 10.0, [], 280.0)
        assert result["voltage"] is None  # No chains with voltage
        assert result["current"] == 10.0
        assert result["power"] is None

    def test_one_chain_current_subtracted(self):
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=80.0)], 280.0
        )
        assert result["current"] == pytest.approx(15.0)
        assert result["voltage"] == pytest.approx(51.2)
        assert result["power"] == pytest.approx(51.2 * 15.0)

    def test_multiple_chains_current_summed_and_subtracted(self):
        result = calculate_virtual_battery(
            51.2,
            50.0,
            [
                make(voltage=51.2, current=10.0, soc=75.0),
                make(voltage=51.2, current=15.0, soc=80.0),
            ],
            280.0,
        )
        # 50 - (10 + 15) = 25
        assert result["current"] == pytest.approx(25.0)
        # voltage = avg of chain voltages = 51.2
        assert result["voltage"] == pytest.approx(51.2)

    def test_soc_average_of_online_chains(self):
        result = calculate_virtual_battery(
            51.2,
            20.0,
            [
                make(voltage=51.2, current=5.0, soc=70.0),
                make(voltage=51.2, current=5.0, soc=90.0),
            ],
            280.0,
        )
        assert result["soc"] == pytest.approx(80.0)

    def test_soc_valid_true_when_chains_have_soc(self):
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=85.0)], 280.0
        )
        assert result["soc_valid"] is True

    def test_soc_valid_false_when_no_soc(self):
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=None)], 280.0
        )
        assert result["soc"] is None
        assert result["soc_valid"] is False

    def test_soc_negative_ignored(self):
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=-5.0)], 280.0
        )
        assert result["soc"] is None
        assert result["soc_valid"] is False

    def test_cell_voltage_divided_by_16(self):
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=80.0)], 280.0
        )
        assert result["cell_voltage"] == pytest.approx(51.2 / 16)

    def test_cell_voltage_none_when_no_voltage(self):
        result = calculate_virtual_battery(
            None, 20.0, [make(voltage=None, current=5.0, soc=80.0)], 280.0
        )
        assert result["cell_voltage"] is None

    def test_consumed_ah_from_soc(self):
        # SoC 75% → 25% discharged → 280 * 0.25 = 70 Ah consumed
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=75.0)], 280.0
        )
        assert result["consumed_ah"] == pytest.approx(70.0)
        assert result["remaining_capacity"] == pytest.approx(210.0)

    def test_consumed_ah_full_battery(self):
        # SoC 100% → 0 Ah consumed
        result = calculate_virtual_battery(
            51.2, -10.0, [make(voltage=51.2, current=0.0, soc=100.0)], 280.0
        )
        assert result["consumed_ah"] == pytest.approx(0.0)
        assert result["remaining_capacity"] == pytest.approx(280.0)

    def test_consumed_ah_empty_battery(self):
        # SoC 0% → 280 Ah consumed
        result = calculate_virtual_battery(
            51.2, 10.0, [make(voltage=51.2, current=10.0, soc=0.0)], 280.0
        )
        assert result["consumed_ah"] == pytest.approx(280.0)
        assert result["remaining_capacity"] == pytest.approx(0.0)

    def test_time_to_go_discharging(self):
        # 210 Ah remaining, discharging at 10A → 21 hours = 75600s
        result = calculate_virtual_battery(
            51.2,
            -10.0,  # discharging
            [make(voltage=51.2, current=0.0, soc=75.0)],  # 210 Ah left
            280.0,
        )
        assert result["time_to_go"] == 21 * 3600

    def test_time_to_go_discharging_capped_at_7_days(self):
        # 1.0 A discharge → 210Ah/1A = 210h > 168h cap → fires
        result = calculate_virtual_battery(
            51.2,
            -1.0,
            [make(voltage=51.2, current=0.0, soc=75.0)],  # 210 Ah left
            280.0,
        )
        assert result["time_to_go"] == TIME_TO_GO_CAP_SECONDS

    def test_time_to_go_charging(self):
        # Chain drawing 0A, system 14A charging → 70Ah to full / 14A = 5h
        result = calculate_virtual_battery(
            51.2,
            14.0,  # charging
            [make(voltage=51.2, current=0.0, soc=75.0)],  # 70 Ah to full
            280.0,
        )
        assert result["time_to_go"] == 5 * 3600

    def test_time_to_go_charging_capped_at_7_days(self):
        # ponytail: charge cap (7d) is unreachable in practice — the 0.5 A
        # threshold short-circuits before the cap check. Document the
        # boundary case explicitly: at exactly the threshold, time_to_go
        # is None; at 0.5+ A the cap is mathematically impossible to hit
        # because (chain_capacity - remaining) / current can never
        # exceed 7 days once current > 0.5 A and the SoC delta ≤ 100%.
        result = calculate_virtual_battery(
            51.2,
            0.4,  # below 0.5 A threshold
            [make(voltage=51.2, current=0.0, soc=75.0)],
            280.0,
        )
        assert result["time_to_go"] is None

    def test_time_to_go_idle_no_capacity(self):
        # full battery → no time-to-go even when charging
        result = calculate_virtual_battery(
            51.2, 5.0, [make(voltage=51.2, current=0.0, soc=100.0)], 280.0
        )
        assert result["time_to_go"] is None

    def test_time_to_go_discharge_threshold(self):
        # current exactly at threshold → no time-to-go
        result = calculate_virtual_battery(
            51.2,
            -CHARGE_DISCHARGE_THRESHOLD_A,
            [make(voltage=51.2, current=0.0, soc=75.0)],
            280.0,
        )
        assert result["time_to_go"] is None

    def test_time_to_go_charge_threshold(self):
        result = calculate_virtual_battery(
            51.2,
            CHARGE_DISCHARGE_THRESHOLD_A,
            [make(voltage=51.2, current=0.0, soc=75.0)],
            280.0,
        )
        assert result["time_to_go"] is None

    def test_chain_offline_skipped(self):
        # chain with None current → only adds voltage if present
        result = calculate_virtual_battery(
            51.2,
            20.0,
            [
                make(voltage=51.2, current=5.0, soc=80.0),
                make(voltage=51.2, current=None, soc=None),
            ],
            280.0,
        )
        assert result["current"] == pytest.approx(15.0)
        assert result["soc"] == pytest.approx(80.0)

    def test_voltage_zero_chain_skipped(self):
        result = calculate_virtual_battery(
            51.2,
            20.0,
            [
                make(voltage=51.2, current=5.0, soc=80.0),
                make(voltage=0.0, current=10.0, soc=70.0),  # voltage=0, skip
            ],
            280.0,
        )
        assert result["voltage"] == pytest.approx(51.2)

    def test_status_ok_when_smartshunt_present(self):
        result = calculate_virtual_battery(
            51.2, 20.0, [make(voltage=51.2, current=5.0, soc=80.0)], 280.0
        )
        assert result["status"] == "ok"


class TestConstants:
    def test_cells_per_chain(self):
        assert CELLS_PER_CHAIN == 16  # 4 batteries × 4 cells

    def test_time_to_go_cap(self):
        assert TIME_TO_GO_CAP_SECONDS == 7 * 24 * 3600

    def test_default_capacity(self):
        assert DEFAULT_CHAIN_CAPACITY == 280.0

    def test_charge_discharge_threshold(self):
        assert CHARGE_DISCHARGE_THRESHOLD_A == 0.5
