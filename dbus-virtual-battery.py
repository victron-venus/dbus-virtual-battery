#!/usr/bin/python3
"""
dbus-virtual-battery - Virtual Battery Calculator for Chain without BMS
========================================================================

Creates a virtual battery by calculating values from SmartShunt minus other chains.
Used for battery chains without physical BMS.

Architecture:
    SmartShunt (total system) - Chain1 - Chain2 = Virtual Chain3

    [SmartShunt] ----\
    [Chain 1]   ------ [This Script] --> D-Bus --> Victron GX
    [Chain 2]   ------/

The virtual battery inherits voltage from chain1/chain2 (parallel connection)
and calculates current as: SmartShunt_current - chain1_current - chain2_current

When any source is missing, the script shows:
- Which sources are online/offline
- Invalid derived measurements until all required sources recover
- Warnings in the GUI

Usage:
    ./dbus-virtual-battery.py --smartshunt ttyUSB4 --chains mqtt_chain1 mqtt_chain2
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import sys
from time import monotonic, sleep, time

# Add shared package to Python path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "../dbus_shared",
    ),
)

# Add Victron library path
sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    ),
)

import dbus

# Existing Venus installations can provide this API through the MQTT battery
# package. Fall back only when dbus_shared itself is absent, not when one of an
# installed helper's own dependencies is broken.
try:
    from dbus_shared import (
        PATH_DC_CURRENT,
        PATH_DC_POWER,
        PATH_DC_VOLTAGE,
        POLL_INTERVAL_MS,
        create_poll_function,
        get_bus,
        register_signal_handlers,
        run_main_loop,
        setup_dbus_paths_common,
        setup_dbus_paths_dc,
        setup_main_loop,
    )
except ModuleNotFoundError as error:
    if error.name != "dbus_shared":
        raise
    from dbus_mqtt_battery import (
        PATH_DC_CURRENT,
        PATH_DC_POWER,
        PATH_DC_VOLTAGE,
        POLL_INTERVAL_MS,
        create_poll_function,
        get_bus,
        register_signal_handlers,
        run_main_loop,
        setup_dbus_paths_common,
        setup_dbus_paths_dc,
        setup_main_loop,
    )
from vedbus import VeDbusService

# This service reports its own release, independently of shared helper versions.
VERSION = "2.7.9"

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Native sources own their Connected contract. MQTT sources additionally publish
# host-monotonic measurement timestamps: polling D-Bus never renews those samples.
DATA_TIMEOUT = 30.0
DEFAULT_CHAIN_SUFFIXES = ("mqtt_chain1", "mqtt_chain2")
DISCOVERY_INTERVAL = 5.0

# Default battery capacity per chain (Ah) - used for SoC calculation
DEFAULT_CHAIN_CAPACITY = 280.0  # 4x 70Ah batteries in series

# Total cell count: 4 batteries in series × 4 cells per 12V battery
CELLS_PER_CHAIN = 16
TIME_TO_GO_CAP_SECONDS = 7 * 24 * 3600
CHARGE_DISCHARGE_THRESHOLD_A = 0.5


def _chain_totals(chains):
    """Accumulate valid chain measurements in their original iteration order."""
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
        if soc is not None and math.isfinite(soc) and 0 <= soc <= 100:
            chain_soc_values.append(soc)
    return chain_current_total, chain_voltage_sum, chains_with_voltage, chain_soc_values


def _calculate_time_to_go(virtual_current, remaining_capacity, chain_capacity):
    """Apply the existing charge/discharge thresholds and duration cap."""
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
    return time_to_go


def _chains_have_measurements(chains):
    """Require finite voltage and current from every configured chain."""
    return bool(chains) and all(
        chain.get("voltage") is not None
        and math.isfinite(chain["voltage"])
        and chain["voltage"] > 0
        and chain.get("current") is not None
        and math.isfinite(chain["current"])
        for chain in chains
    )


def calculate_virtual_battery(
    smartshunt_voltage: float | None,
    smartshunt_current: float | None,
    chains: list[dict],
    chain_capacity: float,
) -> dict:
    """Pure calculator: derive virtual battery values from sources.

    Each chain dict: {voltage: float|None, current: float|None, soc: float|None}.
    """
    shunt_valid = (
        smartshunt_voltage is not None
        and math.isfinite(smartshunt_voltage)
        and smartshunt_voltage > 0
        and smartshunt_current is not None
        and math.isfinite(smartshunt_current)
    )
    chains_valid = _chains_have_measurements(chains)
    if not shunt_valid or not chains_valid:
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
            "status": "SmartShunt missing" if not shunt_valid else "Chain data missing",
        }

    chain_current_total, chain_voltage_sum, chains_with_voltage, chain_soc_values = (
        _chain_totals(chains)
    )

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
        sum(chain_soc_values) / len(chain_soc_values)
        if chains and len(chain_soc_values) == len(chains)
        else None
    )

    if virtual_soc is not None:
        consumed_ah = chain_capacity * (1.0 - virtual_soc / 100.0)
        remaining_capacity = chain_capacity - consumed_ah
    else:
        consumed_ah = None
        remaining_capacity = None

    time_to_go = _calculate_time_to_go(
        virtual_current, remaining_capacity, chain_capacity
    )

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


PATH_CONNECTED = "/Connected"
PATH_CAPACITY = "/Capacity"
PATH_DATA_COMPLETE = "/Info/DataComplete"
PATH_CONSUMED_AMPHOURS = "/ConsumedAmphours"
PATH_TIME_TO_GO = "/TimeToGo"
PATH_MIN_CELL_VOLTAGE = "/System/MinCellVoltage"
PATH_MAX_CELL_VOLTAGE = "/System/MaxCellVoltage"
PATH_VOLTAGE_SUM = "/Voltages/Sum"
PATH_VOLTAGE_DIFF = "/Voltages/Diff"
PATH_CUSTOM_NAME = "/CustomName"


class SourceStatus:
    """Track status of a data source"""

    def __init__(self, name: str, service: str):
        self.name = name
        self.service = service
        self.online = False
        self.last_read = 0.0
        self.sample_age: float | None = None
        self.voltage: float | None = None
        self.current: float | None = None
        self.soc: float | None = None
        self.power: float | None = None


class DbusReader:
    """Read values from D-Bus services with automatic reconnection"""

    def __init__(self):
        self.bus = None
        self._cache = {}
        self._cache_time = {}
        self._cache_ttl = 1.0  # Cache values for 1 second
        self._last_reconnect_attempt = None
        self._reconnect_interval = 5.0  # Minimum seconds between reconnect attempts
        self._connect()

    def _connect(self):
        """Connect to D-Bus"""
        self._last_reconnect_attempt = monotonic()
        self._cache.clear()
        self._cache_time.clear()
        try:
            self.bus = get_bus()
            logger.debug("D-Bus connection established")
            return True
        except Exception:
            logger.exception("D-Bus connection failed")
            self.bus = None
            return False

    def _ensure_connected(self) -> bool:
        """Ensure D-Bus connection is active, reconnect if needed"""
        if self.bus is not None:
            return True

        now = monotonic()
        if (
            self._last_reconnect_attempt is not None
            and now - self._last_reconnect_attempt < self._reconnect_interval
        ):
            return False

        return self._connect()

    def _handle_read_error(self, service, path, e):
        """Invalidate a lost connection while leaving missing objects nonfatal."""
        error_str = str(e)
        if "UnknownObject" not in error_str and "NameHasNoOwner" not in error_str:
            # Connection might be broken
            conn_lost_markers = (
                "Connection refused",
                "org.freedesktop.DBus.Error.Disconnected",
            )
            if any(m in error_str for m in conn_lost_markers):
                logger.warning("D-Bus connection lost, will reconnect")
                self.bus = None
                self._cache.clear()
                self._cache_time.clear()
            else:
                logger.debug("D-Bus error reading %s%s: %s", service, path, e)

    def get_value(self, service: str, path: str) -> float | None:
        """Get a value from D-Bus service"""
        if not self._ensure_connected():
            return None

        cache_key = f"{service}{path}"
        now = monotonic()

        # Return cached value if fresh
        if (
            cache_key in self._cache
            and 0 <= now - self._cache_time.get(cache_key, 0) < self._cache_ttl
        ):
            return self._cache[cache_key]

        try:
            obj = self.bus.get_object(service, path)
            value = obj.GetValue()

            # Handle dbus types and empty lists
            if value is None or (
                isinstance(value, (list, dbus.Array)) and len(value) == 0
            ):
                return None

            if hasattr(value, "real"):
                value = float(value)
            else:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return None

            if not math.isfinite(value):
                return None
            self._cache[cache_key] = value
            self._cache_time[cache_key] = now
            return value

        except dbus.exceptions.DBusException as e:
            self._handle_read_error(service, path, e)
            return None

    def service_exists(self, service: str) -> bool:
        """Check if a D-Bus service exists"""
        if not self._ensure_connected():
            return False
        try:
            self.bus.get_object(service, "/")
            return True
        except dbus.exceptions.DBusException:
            return False

    def get_snapshot(self, service: str) -> dict[str, float | None] | None:
        """Read one coherent BusItem snapshot, without the individual-path cache."""
        if not self._ensure_connected():
            return None
        try:
            items = self.bus.get_object(service, "/").GetItems()
            if not isinstance(items, dict):
                return None
            values = {}
            for path, item in items.items():
                raw = item.get("Value") if isinstance(item, dict) else None
                try:
                    number = float(raw)
                    values[str(path)] = number if math.isfinite(number) else None
                except (TypeError, ValueError, OverflowError):
                    values[str(path)] = None
            return values
        except dbus.exceptions.DBusException as exc:
            if any(
                marker in str(exc)
                for marker in (
                    "Connection refused",
                    "org.freedesktop.DBus.Error.Disconnected",
                )
            ):
                self.bus = None
                self._cache.clear()
                self._cache_time.clear()
            return None

    def get_product_name(self, suffix: str) -> str | None:
        """Identify hardware by its product, not a changeable USB port name."""
        if not self._ensure_connected():
            return None
        try:
            value = self.bus.get_object(
                f"com.victronenergy.battery.{suffix}", "/ProductName"
            ).GetValue()
            return str(value) if isinstance(value, str) else None
        except dbus.exceptions.DBusException:
            return None

    def invalidate_source(self, service: str) -> None:
        """Do not mix prior poll values with a newly connected source."""
        # Snapshot keys before removing entries from this same dictionary.
        for key in list(self._cache):
            if key.startswith(service + "/"):
                self._cache.pop(key, None)
                self._cache_time.pop(key, None)

    def list_battery_services(
        self, pattern: str = "mqtt_chain", exclude_self: str | None = None
    ) -> list[str]:
        """List all D-Bus battery services matching a pattern.

        Returns suffixes (e.g., ['mqtt_chain1', 'ttyUSB4']) for services
        matching com.victronenergy.battery.{pattern}*
        """
        if not self._ensure_connected():
            return []

        try:
            bus_names = self.bus.list_names()
            suffixes = []
            for name in bus_names:
                if name.startswith("com.victronenergy.battery."):
                    suffix = name[len("com.victronenergy.battery.") :]
                    if pattern and pattern not in suffix:
                        continue
                    if exclude_self and suffix == exclude_self:
                        continue
                    suffixes.append(suffix)
            return sorted(suffixes)
        except dbus.exceptions.DBusException:
            logger.exception("Failed to list D-Bus services")
            return []


class VirtualBatteryService:
    """D-Bus service for virtual battery calculated from SmartShunt minus other chains"""

    def __init__(
        self,
        smartshunt_suffix: str | None = None,
        smartshunt_index: int = 0,
        chain_suffixes: list[str] | None = None,
        device_instance: int = 514,
        product_name: str = "Virtual Battery Chain",
        chain_capacity: float = DEFAULT_CHAIN_CAPACITY,
    ):
        self.dbus_reader = DbusReader()
        self.device_instance = device_instance
        self.product_name = product_name
        self.chain_capacity = chain_capacity
        self._smartshunt_index = smartshunt_index
        self._last_discovery = None

        # Auto-discover SmartShunt if not provided
        if smartshunt_suffix is None:
            smartshunt_suffix = self._discover_smartshunt(smartshunt_index)
            if smartshunt_suffix is None:
                logger.warning("No SmartShunt found on D-Bus - waiting for the source")
            else:
                logger.info("Auto-discovered SmartShunt: %s", smartshunt_suffix)

        # Membership is configuration, not the subset that won the boot race.
        # Never subtract an aggregate BMS service or silently omit a late chain.
        if chain_suffixes is None:
            chain_suffixes = list(DEFAULT_CHAIN_SUFFIXES)
        if not chain_suffixes or len(set(chain_suffixes)) != len(chain_suffixes):
            raise ValueError("Specify a nonempty list of distinct chain suffixes")
        if "virtual_chain" in chain_suffixes or smartshunt_suffix in chain_suffixes:
            raise ValueError("A chain cannot be the SmartShunt or this virtual battery")
        self._chain_suffixes = tuple(chain_suffixes)
        logger.info("Required chain services: %s", chain_suffixes)

        # Track data sources
        self.smartshunt = SourceStatus(
            "SmartShunt",
            f"com.victronenergy.battery.{smartshunt_suffix}"
            if smartshunt_suffix
            else "",
        )
        self.smartshunt_suffix = smartshunt_suffix
        self.chains: list[SourceStatus] = []
        for i, suffix in enumerate(chain_suffixes):
            self.chains.append(
                SourceStatus(f"Chain{i + 1}", f"com.victronenergy.battery.{suffix}")
            )

        # Track consumed Ah for SoC calculation
        self.consumed_ah = 0.0
        self.last_update = time()
        self.initial_soc = None
        self.last_status_log = 0.0

        # Create D-Bus service
        service_name = "com.victronenergy.battery.virtual_chain"
        self._dbusservice = VeDbusService(service_name, get_bus(), register=False)

        self._setup_paths()
        self._dbusservice.register()
        logger.info("D-Bus service registered: %s", service_name)
        logger.info("SmartShunt source: %s", self.smartshunt.service)
        logger.info("Chain sources to subtract: %s", [c.service for c in self.chains])

    def _discover_smartshunt(self, index: int = 0) -> str | None:
        """Select a positively identified shunt; a serial BMS is not a shunt."""
        all_services = self.dbus_reader.list_battery_services(
            pattern="", exclude_self="virtual_chain"
        )

        candidates = [
            s
            for s in all_services
            if "shunt" in (self.dbus_reader.get_product_name(s) or "").lower()
        ]

        candidates = [
            s for s in candidates if s not in getattr(self, "_chain_suffixes", ())
        ]
        if not candidates or index < 0 or index >= len(candidates):
            return None
        return candidates[index]

    def _rediscover_missing_smartshunt(self) -> None:
        """Retry initial discovery; retain a selected identity through outages."""
        if self.smartshunt.service:
            return
        now = monotonic()
        if (
            self._last_discovery is not None
            and now - self._last_discovery < DISCOVERY_INTERVAL
        ):
            return
        self._last_discovery = now
        suffix = self._discover_smartshunt(self._smartshunt_index)
        if suffix is not None:
            self.smartshunt_suffix = suffix
            self.smartshunt.service = f"com.victronenergy.battery.{suffix}"
            logger.info("Discovered delayed SmartShunt: %s", suffix)

    def _setup_paths(self):
        """Setup D-Bus paths for Victron GUI v2 compatibility"""

        # Common paths (management, device identification)
        setup_dbus_paths_common(
            self._dbusservice,
            process_name=__file__,
            version=VERSION,
            connection="Virtual (Calculated)",
            device_instance=self.device_instance,
            product_name=self.product_name,
            hardware_version="Virtual BMS",
            product_id=0xB035,
        )
        # Older installed helpers default this path to 1. Override before the
        # service name becomes visible, not after the first polling interval.
        self._dbusservice[PATH_CONNECTED] = 0

        # DC measurements (without formatting for simplicity)
        setup_dbus_paths_dc(self._dbusservice, include_formats=False)

        # Capacity and state
        self._dbusservice.add_path("/Soc", None)
        self._dbusservice.add_path(PATH_CAPACITY, None)
        self._dbusservice.add_path("/InstalledCapacity", self.chain_capacity)
        self._dbusservice.add_path(PATH_CONSUMED_AMPHOURS, None)
        self._dbusservice.add_path(PATH_TIME_TO_GO, None, writeable=True)

        # System info - shows source availability
        # Battery system configuration for GUI v2
        # This virtual chain represents 4 batteries in series (4S config, 48V nominal)
        self._dbusservice.add_path("/System/NrOfBatteries", 4)  # 4 batteries per chain
        self._dbusservice.add_path(
            "/System/NrOfCellsPerBattery", 4
        )  # 4 cells per 12V battery
        self._dbusservice.add_path("/System/BatteriesParallel", 1)
        self._dbusservice.add_path("/System/BatteriesSeries", 4)

        # Modules status (sources providing data for this virtual battery)
        total_sources = 1 + len(self.chains)  # SmartShunt + other chains
        self._dbusservice.add_path("/System/NrOfModulesOnline", 0)
        self._dbusservice.add_path("/System/NrOfModulesOffline", total_sources)
        self._dbusservice.add_path("/System/NrOfModulesBlockingCharge", 0)
        self._dbusservice.add_path("/System/NrOfModulesBlockingDischarge", 0)

        # Cell voltage (estimated from total voltage / 16 cells)
        # Virtual battery cannot provide per-cell voltages, only estimated average
        self._dbusservice.add_path(PATH_MIN_CELL_VOLTAGE, None)
        self._dbusservice.add_path(PATH_MAX_CELL_VOLTAGE, None)
        self._dbusservice.add_path("/System/MinVoltageCellId", "N/A (Virtual)")
        self._dbusservice.add_path("/System/MaxVoltageCellId", "N/A (Virtual)")

        # Estimated cell voltages (dbus-serialbattery format: /Voltages/Cell1..Cell16)
        for i in range(1, 17):
            self._dbusservice.add_path(f"/Voltages/Cell{i}", None)
        self._dbusservice.add_path(PATH_VOLTAGE_SUM, None)
        self._dbusservice.add_path(PATH_VOLTAGE_DIFF, None)

        # Custom status info - shows which sources are online/offline
        self._dbusservice.add_path("/Info/SourceStatus", "Initializing...")
        self._dbusservice.add_path(PATH_DATA_COMPLETE, 0)
        self._dbusservice.add_path("/Info/MissingSources", "")

        # Charge/discharge status (depends on source availability)
        self._dbusservice.add_path("/Io/AllowToCharge", None)
        self._dbusservice.add_path("/Io/AllowToDischarge", None)

        # Alarms
        self._dbusservice.add_path("/Alarms/LowVoltage", 0)
        self._dbusservice.add_path("/Alarms/HighVoltage", 0)
        self._dbusservice.add_path("/Alarms/LowSoc", 0)
        self._dbusservice.add_path("/Alarms/HighTemperature", 0)
        self._dbusservice.add_path("/Alarms/LowTemperature", 0)
        # Use InternalFailure to indicate missing data sources
        self._dbusservice.add_path("/Alarms/InternalFailure", 0)

    def _source_freshness(self, source, complete, sampled, timeout, mqtt_chain):
        """Keep source sample age separate from the time of this local read."""
        source.sample_age = None
        metadata_present = any(
            value is not None for value in (complete, sampled, timeout)
        )
        fresh = not metadata_present and not mqtt_chain
        if (
            complete == 1
            and sampled is not None
            and timeout is not None
            and timeout > 0
        ):
            source.sample_age = monotonic() - sampled
            fresh = 0 <= source.sample_age < timeout
        return fresh

    def _read_source(self, source: SourceStatus) -> bool:
        """Read data from a source and update its status. Returns True if data is valid."""
        if not source.service:
            return False
        self.dbus_reader.invalidate_source(source.service)
        snapshot = self.dbus_reader.get_snapshot(source.service)
        mqtt_chain = source.service.rsplit(".", 1)[-1].startswith("mqtt_chain")
        if snapshot is not None:
            get_value = snapshot.get
        elif mqtt_chain:
            # Do not assemble an atomic MQTT frame from separate D-Bus replies.
            get_value = {}.get
        else:
            # Native Venus services may expose only individual BusItems.
            def get_value(path):
                return self.dbus_reader.get_value(source.service, path)

        connected = get_value(PATH_CONNECTED)
        voltage = get_value(PATH_DC_VOLTAGE)
        current = get_value(PATH_DC_CURRENT)
        soc = get_value("/Soc")
        power = get_value(PATH_DC_POWER)
        complete = get_value(PATH_DATA_COMPLETE)
        sampled = get_value("/Info/LastMeasurementMonotonic")
        timeout = get_value("/Info/DataTimeout")
        fresh = self._source_freshness(source, complete, sampled, timeout, mqtt_chain)

        # A registered service can retain old values while reporting offline.
        # Missing/invalid data must not remain eligible for subtraction.
        if (
            connected == 1
            and fresh
            and voltage is not None
            and voltage > 0
            and current is not None
            and math.isfinite(voltage)
            and math.isfinite(current)
        ):
            source.voltage = voltage
            source.current = current
            source.soc = (
                soc
                if soc is not None and math.isfinite(soc) and 0 <= soc <= 100
                else None
            )
            source.power = (
                power
                if power is not None and math.isfinite(power)
                else voltage * current
            )
            source.online = True
            # This is the time of a local read, never the physical sample time.
            source.last_read = time()
            return True
        if source.online:
            logger.warning(
                "%s went offline or stopped publishing valid measurements", source.name
            )
        source.online = False
        source.voltage = source.current = source.soc = source.power = None
        return False

    def _get_status_string(self) -> tuple[str, str, bool]:
        """Get status string showing online/offline sources.
        Returns: (status_string, missing_sources, all_online)
        """
        online = []
        offline = []

        if self.smartshunt.online:
            online.append("SS")
        else:
            offline.append("SmartShunt")

        for i, chain in enumerate(self.chains):
            if chain.online:
                online.append(f"C{i + 1}")
            else:
                offline.append(f"Chain{i + 1}")

        all_online = len(offline) == 0

        if all_online:
            status = f"OK: All sources online ({', '.join(online)})"
            missing = ""
        else:
            status = f"PARTIAL: Online={', '.join(online) or 'None'}"
            missing = ", ".join(offline)

        return status, missing, all_online

    def _clear_missing_source_values(self, missing_str):
        """Invalidate derived values when any required current source is unavailable."""
        logger.debug("Source unavailable - cannot calculate virtual battery")
        self._dbusservice[PATH_CONNECTED] = 0
        self._dbusservice["/Io/AllowToCharge"] = None
        self._dbusservice["/Io/AllowToDischarge"] = None
        self._dbusservice[PATH_DC_VOLTAGE] = None
        self._dbusservice[PATH_DC_CURRENT] = None
        self._dbusservice[PATH_DC_POWER] = None
        self._dbusservice["/Soc"] = None
        for path in (
            PATH_CAPACITY,
            PATH_CONSUMED_AMPHOURS,
            PATH_TIME_TO_GO,
            PATH_MIN_CELL_VOLTAGE,
            PATH_MAX_CELL_VOLTAGE,
            PATH_VOLTAGE_SUM,
            PATH_VOLTAGE_DIFF,
        ):
            self._dbusservice[path] = None
        for index in range(1, CELLS_PER_CHAIN + 1):
            self._dbusservice[f"/Voltages/Cell{index}"] = None
        self._dbusservice[PATH_CUSTOM_NAME] = (
            f"{self.product_name} [Missing: {missing_str}]"
        )

    def _publish_calculation(self, calc):
        """Publish the complete derived snapshot before marking its data ready."""
        virtual_voltage = calc["voltage"]
        virtual_current = calc["current"]
        virtual_power = calc["power"]
        virtual_soc = calc["soc"]
        cell_voltage = calc["cell_voltage"]
        self.consumed_ah = calc["consumed_ah"]
        remaining_capacity = calc["remaining_capacity"]
        time_to_go = calc["time_to_go"]
        self.last_update = time()

        # Update D-Bus paths
        self._dbusservice[PATH_DC_VOLTAGE] = (
            round(virtual_voltage, 2) if virtual_voltage is not None else None
        )
        self._dbusservice[PATH_DC_CURRENT] = (
            round(virtual_current, 2) if virtual_current is not None else None
        )
        self._dbusservice[PATH_DC_POWER] = (
            round(virtual_power, 1) if virtual_power is not None else None
        )
        self._dbusservice["/Soc"] = (
            round(virtual_soc, 1) if virtual_soc is not None else None
        )
        self._dbusservice[PATH_CAPACITY] = (
            round(remaining_capacity, 1) if remaining_capacity is not None else None
        )
        self._dbusservice[PATH_CONSUMED_AMPHOURS] = (
            round(self.consumed_ah, 1) if self.consumed_ah is not None else None
        )

        # TimeToGo computed by calculate_virtual_battery()
        self._dbusservice[PATH_TIME_TO_GO] = time_to_go

        if cell_voltage:
            self._dbusservice[PATH_MIN_CELL_VOLTAGE] = round(cell_voltage, 3)
            self._dbusservice[PATH_MAX_CELL_VOLTAGE] = round(cell_voltage, 3)
            self._dbusservice[PATH_VOLTAGE_SUM] = (
                round(virtual_voltage, 2) if virtual_voltage is not None else None
            )
            self._dbusservice[PATH_VOLTAGE_DIFF] = (
                0.0  # Virtual battery has no cell difference
            )
            # Set all 16 cells to estimated average voltage (dbus-serialbattery format)
            for i in range(1, 17):
                self._dbusservice[f"/Voltages/Cell{i}"] = round(cell_voltage, 3)

        # Publish readiness last, after the complete derived snapshot is visible.
        # A subtraction is telemetry, not evidence of physical BMS permission.
        self._dbusservice[PATH_DATA_COMPLETE] = 1
        self._dbusservice[PATH_CONNECTED] = 1
        return virtual_voltage, virtual_current, virtual_soc

    def update(self):
        """Update virtual battery values"""
        now = time()

        # Read all sources
        self._rediscover_missing_smartshunt()
        self._read_source(self.smartshunt)
        for chain in self.chains:
            self._read_source(chain)

        # Get status
        status_str, missing_str, all_online = self._get_status_string()

        # Count online/offline modules
        modules_online = (1 if self.smartshunt.online else 0) + sum(
            1 for c in self.chains if c.online
        )
        modules_offline = (1 if not self.smartshunt.online else 0) + sum(
            1 for c in self.chains if not c.online
        )

        # Update status info
        self._dbusservice["/System/NrOfModulesOnline"] = modules_online
        self._dbusservice["/System/NrOfModulesOffline"] = modules_offline
        self._dbusservice["/Info/SourceStatus"] = status_str
        self._dbusservice["/Info/MissingSources"] = missing_str
        if not all_online:
            self._dbusservice[PATH_DATA_COMPLETE] = 0

        # Don't set InternalFailure alarm for missing chains - just show in status
        # Only set alarm if SmartShunt is missing (critical)
        self._dbusservice["/Alarms/InternalFailure"] = 0

        # Log status periodically (every 60 seconds)
        if now - self.last_status_log > 60.0:
            self.last_status_log = now
            if not all_online:
                logger.warning("Missing sources: %s", missing_str)
            else:
                logger.info("All sources online")

        # Every current source is required: omitting one attributes its current
        # to the virtual chain and produces a false remaining capacity estimate.
        if not all_online:
            self._clear_missing_source_values(missing_str)
            return

        # Build chain inputs from online sources
        chains = [
            {
                "voltage": c.voltage,
                "current": c.current,
                "soc": c.soc,
            }
            for c in self.chains
        ]

        # Pure calculator
        calc = calculate_virtual_battery(
            self.smartshunt.voltage,
            self.smartshunt.current,
            chains,
            self.chain_capacity,
        )
        virtual_voltage, virtual_current, virtual_soc = self._publish_calculation(calc)

        # Update CustomName to show status when sources missing
        if not all_online:
            self._dbusservice[PATH_CUSTOM_NAME] = (
                f"{self.product_name} [Missing: {missing_str}]"
            )
        else:
            self._dbusservice[PATH_CUSTOM_NAME] = self.product_name

        # Log debug info
        v_v_str = f"{virtual_voltage:.2f}" if virtual_voltage is not None else "None"
        v_c_str = f"{virtual_current:.2f}" if virtual_current is not None else "None"
        v_s_str = f"{virtual_soc:.0f}" if virtual_soc is not None else "None"
        logger.debug(
            f"Virtual: {v_v_str}V {v_c_str}A {v_s_str}% (Online: {modules_online}/{modules_online + modules_offline})",
        )


def main():
    """Main entry point for virtual battery D-Bus service."""
    parser = argparse.ArgumentParser(
        description="Virtual Battery Calculator for Victron"
    )
    parser.add_argument(
        "--smartshunt",
        default=None,
        help="SmartShunt D-Bus service suffix (default: auto-discover first)",
    )
    parser.add_argument(
        "--smartshunt-index",
        type=int,
        default=0,
        help="Index of SmartShunt to use if multiple found (default: 0 for first)",
    )
    parser.add_argument(
        "--chains",
        nargs="*",
        default=None,
        help="Required chain suffixes (default: mqtt_chain1 mqtt_chain2; never auto-discovered)",
    )
    parser.add_argument(
        "--instance", type=int, default=514, help="D-Bus device instance (default: 514)"
    )
    parser.add_argument(
        "--product-name", default="Virtual Battery Chain 3", help="Product name in GUI"
    )
    parser.add_argument(
        "--capacity",
        type=float,
        default=DEFAULT_CHAIN_CAPACITY,
        help=f"Chain capacity in Ah (default: {DEFAULT_CHAIN_CAPACITY})",
    )
    args = parser.parse_args()

    logger.info("=== dbus-virtual-battery v%s ===", VERSION)
    if args.smartshunt:
        logger.info(
            "SmartShunt: com.victronenergy.battery.%s (user-specified)", args.smartshunt
        )
    else:
        logger.info("SmartShunt: auto-discover (index %d)", args.smartshunt_index)
    if args.chains:
        logger.info("Chains to subtract (provided): %s", args.chains)
    else:
        logger.info("Required chains: %s", DEFAULT_CHAIN_SUFFIXES)
    logger.info("Chain capacity: %s Ah", args.capacity)

    # Setup D-Bus main loop
    mainloop = setup_main_loop()

    # Register signal handlers
    register_signal_handlers(mainloop)

    # Wait for services to be available
    logger.info("Waiting for D-Bus services...")

    sleep(5)

    # Create virtual battery service
    service = VirtualBatteryService(
        smartshunt_suffix=args.smartshunt,
        smartshunt_index=args.smartshunt_index,
        chain_suffixes=args.chains,
        device_instance=args.instance,
        product_name=args.product_name,
        chain_capacity=args.capacity,
    )

    # Create poll function with GC
    poll_fn = create_poll_function(service)

    # Start polling and run main loop
    run_main_loop(mainloop, POLL_INTERVAL_MS, poll_fn)


if __name__ == "__main__":
    main()
