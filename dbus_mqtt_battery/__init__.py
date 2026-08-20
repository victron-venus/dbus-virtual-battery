"""
dbus_mqtt_battery package for dbus-virtual-battery.
Contains only what's needed for virtual battery functionality.
"""

from .config import (
    PATH_DC_CURRENT,
    PATH_DC_POWER,
    PATH_DC_VOLTAGE,
    POLL_INTERVAL_MS,
    VERSION,
    STALE_TIMEOUT,
    DVCC_CELLS_PER_BMS,
)

from .dbus_utils import (
    get_bus,
    setup_main_loop,
    create_shutdown_handler,
    register_signal_handlers,
    create_poll_function,
    run_main_loop,
    setup_dbus_paths_common,
    setup_dbus_paths_dc,
    setup_dbus_paths_alarms,
)

__all__ = [
    "PATH_DC_CURRENT",
    "PATH_DC_POWER",
    "PATH_DC_VOLTAGE",
    "POLL_INTERVAL_MS",
    "VERSION",
    "STALE_TIMEOUT",
    "DVCC_CELLS_PER_BMS",
    "get_bus",
    "setup_main_loop",
    "create_shutdown_handler",
    "register_signal_handlers",
    "create_poll_function",
    "run_main_loop",
    "setup_dbus_paths_common",
    "setup_dbus_paths_dc",
    "setup_dbus_paths_alarms",
]
