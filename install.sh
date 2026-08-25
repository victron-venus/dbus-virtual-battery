#!/bin/bash
#
# dbus-virtual-battery installer for Venus OS
# Run this script ON Venus OS after copying files
#
# Usage: ./install.sh
#

set -e

INSTALL_DIR="/data/dbus-virtual-battery"
SEPARATOR="=============================================="

echo "$SEPARATOR"
echo "  dbus-virtual-battery Installer for Venus OS"
echo "$SEPARATOR"
echo ""

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy Python scripts (if running from source directory)
if [[ -f "dbus-virtual-battery.py" ]] ; then
    cp dbus-virtual-battery.py "$INSTALL_DIR/"
    echo "Copied dbus-virtual-battery.py"
fi

# Copy dbus_mqtt_battery package (shared utilities)
if [[ -d "dbus_mqtt_battery" ]] ; then
    cp -r dbus_mqtt_battery "$INSTALL_DIR/"
    echo "Copied dbus_mqtt_battery package"
fi

# Copy version file
if [[ -f "version" ]] ; then
    cp version "$INSTALL_DIR/"
    echo "Copied version file"
fi

echo ""
echo "Installation complete. Files copied to: $INSTALL_DIR"
echo ""
echo "To complete installation via SetupHelper:"
echo "  1. Ensure /data/setupOptions/dbus-virtual-battery/ exists with desired options"
echo "  2. Run: /data/SetupHelper/HelperScripts/installer.sh dbus-virtual-battery"
echo ""
echo "Or start manually with:"
echo "  python3 $INSTALL_DIR/dbus-virtual-battery.py [options]"
echo ""
echo "Example options:"
echo "  --smartshunt-index 1    # Use second SmartShunt if multiple found"
echo "  --chains mqtt_chain1 mqtt_chain2  # Use specific chains (overrides auto-discovery)"
echo "  --capacity 400          # Set battery capacity to 400Ah"
echo ""