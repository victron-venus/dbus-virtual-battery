"""Pure calculator for virtual battery values.

No D-Bus, no I/O — given SmartShunt measurements and online chain
readings, returns derived virtual battery state. Imports cleanly under
plain Python so the unit test suite does not need Venus OS.
"""

from __future__ import annotations

DATA_TIMEOUT = 30.0
DEFAULT_CHAIN_CAPACITY = 280.0
CELLS_PER_CHAIN = 16
TIME_TO_GO_CAP_SECONDS = 7 * 24 * 3600
CHARGE_DISCHARGE_THRESHOLD_A = 0.5


def calculate_virtual_battery(
    smartshunt_voltage: float | None,
    smartshunt_current: float | None,
    chains: list[dict],
    chain_capacity: float,
) -> dict:
    """Pure calculator: derive virtual battery values from sources.

    Each chain dict: {voltage: float|None, current: float|None, soc: float|None}.
    Returns dict with keys: voltage, current, power, soc, soc_valid, cell_voltage,
    consumed_ah, remaining_capacity, time_to_go, status (str).
    """
    if smartshunt_voltage is None or smartshunt_current is None:
        return {
            "voltage": None,
            "current": None,
            "power": None,
            "soc": None,
            "soc_valid": False,
            "cell_voltage": None,
            "consumed_ah": None,
            "remaining_capacity": None,
            "time_to_go": None,
            "status": "SmartShunt missing",
        }

    chain_current_total = 0.0
    chain_voltage_sum = 0.0
    chains_with_voltage = 0
    chain_soc_values: list[float] = []

    for chain in chains:
        current = chain.get("current")
        voltage = chain.get("voltage")
        soc = chain.get("soc")
        if current is not None:
            chain_current_total += current
        if voltage is not None and voltage > 0:
            chain_voltage_sum += voltage
            chains_with_voltage += 1
        if soc is not None and soc >= 0:
            chain_soc_values.append(soc)

    virtual_current = smartshunt_current - chain_current_total
    virtual_voltage = (
        chain_voltage_sum / chains_with_voltage if chains_with_voltage > 0 else None
    )
    virtual_power = (
        virtual_voltage * virtual_current
        if virtual_voltage is not None and virtual_current is not None
        else None
    )
    cell_voltage = (
        virtual_voltage / CELLS_PER_CHAIN
        if virtual_voltage is not None and virtual_voltage > 0
        else None
    )
    virtual_soc = (
        sum(chain_soc_values) / len(chain_soc_values) if chain_soc_values else None
    )

    if virtual_soc is not None:
        consumed_ah = chain_capacity * (1.0 - virtual_soc / 100.0)
        remaining_capacity = chain_capacity - consumed_ah
    else:
        consumed_ah = None
        remaining_capacity = None

    time_to_go: int | None
    if (
        virtual_current is not None
        and remaining_capacity is not None
        and virtual_current < -CHARGE_DISCHARGE_THRESHOLD_A
        and remaining_capacity > 0
    ):
        hours = remaining_capacity / abs(virtual_current)
        time_to_go = min(int(hours * 3600), TIME_TO_GO_CAP_SECONDS)
    elif (
        virtual_current is not None
        and remaining_capacity is not None
        and virtual_current > CHARGE_DISCHARGE_THRESHOLD_A
        and chain_capacity > remaining_capacity
    ):
        hours = (chain_capacity - remaining_capacity) / virtual_current
        time_to_go = min(int(hours * 3600), TIME_TO_GO_CAP_SECONDS)
    else:
        time_to_go = None

    return {
        "voltage": virtual_voltage,
        "current": virtual_current,
        "power": virtual_power,
        "soc": virtual_soc,
        "soc_valid": virtual_soc is not None,
        "cell_voltage": cell_voltage,
        "consumed_ah": consumed_ah,
        "remaining_capacity": remaining_capacity,
        "time_to_go": time_to_go,
        "status": "ok",
    }
