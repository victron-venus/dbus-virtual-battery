"""
Configuration module for dbus-virtual-battery.
Contains only the constants needed by the virtual battery implementation.
"""

# D-Bus measurement paths (from dbus_utils.py in original)
# These are duplicated here to avoid circular imports, but in practice
# they should be imported from dbus_utils. Keeping them here for simplicity.
PATH_DC_VOLTAGE = "/Dc/0/Voltage"
PATH_DC_CURRENT = "/Dc/0/Current"
PATH_DC_POWER = "/Dc/0/Power"

# Polling interval in milliseconds
POLL_INTERVAL_MS = 2000

# Version of the package
VERSION = "2.7.2"

# Other constants that might be needed (keeping for compatibility)
STALE_TIMEOUT = 10000  # 10 seconds
DVCC_CELLS_PER_BMS = 4