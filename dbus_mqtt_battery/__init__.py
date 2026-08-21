"""
dbus_mqtt_battery package for dbus-virtual-battery.
Contains only what's needed for virtual battery functionality.
"""

from .config import (
    DVCC_CELLS_PER_BMS,
    PATH_DC_CURRENT,
    PATH_DC_POWER,
    PATH_DC_VOLTAGE,
    POLL_INTERVAL_MS,
    STALE_TIMEOUT,
    VERSION,
)
from .dbus_utils import (
    create_poll_function,
    create_shutdown_handler,
    get_bus,
    register_signal_handlers,
    run_main_loop,
    setup_dbus_paths_alarms,
    setup_dbus_paths_common,
    setup_dbus_paths_dc,
    setup_main_loop,
)

__all__ = [
    "DVCC_CELLS_PER_BMS",
    "PATH_DC_CURRENT",
    "PATH_DC_POWER",
    "PATH_DC_VOLTAGE",
    "POLL_INTERVAL_MS",
    "STALE_TIMEOUT",
    "VERSION",
    "create_poll_function",
    "create_shutdown_handler",
    "get_bus",
    "register_signal_handlers",
    "run_main_loop",
    "setup_dbus_paths_alarms",
    "setup_dbus_paths_common",
    "setup_dbus_paths_dc",
    "setup_main_loop",
]
