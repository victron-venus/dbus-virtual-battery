#!/bin/bash
#
# Deploy dbus-virtual-battery to Venus OS
#
# Usage: ./deploy.sh [SSH_HOST]
#
# Downloads latest version from GitHub (victron-venus/dbus-virtual-battery)
# into /data/dbus-virtual-battery and runs setup install.
#
# Package name matches the GitHub repo name, so PackageManager can also
# manage updates after this initial deploy.

set -e

SSH_HOST="${1:-${SSH_HOST:-Cerbo}}"
REPO="victron-venus/dbus-virtual-battery"
APP_DIR="/data/dbus-virtual-battery"
SERVICE="dbus-virtual-chain"
SEPARATOR="=============================================="

echo "$SEPARATOR"
echo "  Deploying dbus-virtual-battery to Venus OS"
echo "$SEPARATOR"
echo "SSH Host: $SSH_HOST"
echo ""

# Stop service+log pair before replacing files: replacing a supervised tree
# live leaves orphan supervises watching deleted directories
echo ">>> Stopping service..."
ssh "$SSH_HOST" "svc -dx /service/$SERVICE 2>/dev/null || true; svc -dx /service/$SERVICE/log 2>/dev/null || true"

# Download and install
echo ">>> Downloading latest version..."
ssh "$SSH_HOST" "rm -rf $APP_DIR && \
mkdir -p /data && cd /data && \
wget -qO - https://github.com/$REPO/archive/main.tar.gz | tar -xzf - && \
mv dbus-virtual-battery-main dbus-virtual-battery && \
chmod +x $APP_DIR/setup"

echo ">>> Running setup install..."
ssh "$SSH_HOST" "$APP_DIR/setup install"

# Restart service
echo ">>> Starting service..."
ssh "$SSH_HOST" "svc -u /service/$SERVICE/log 2>/dev/null || true; svc -u /service/$SERVICE 2>/dev/null || true"

# Wait for service to start
echo ""
echo ">>> Waiting for service to start..."
sleep 8

echo ""
echo "$SEPARATOR"
echo "  Service Status"
echo "$SEPARATOR"
ssh "$SSH_HOST" "svstat /service/$SERVICE 2>/dev/null || echo 'Service not found'"

echo ""
echo "$SEPARATOR"
echo "  D-Bus Values"
echo "$SEPARATOR"
ssh "$SSH_HOST" 'svc=com.victronenergy.battery.virtual_chain
# NOTE: no "timeout" on Venus OS busybox - call dbus-send directly
str() { dbus-send --system --print-reply --dest=$svc $1 com.victronenergy.BusItem.GetValue 2>/dev/null | grep variant | sed "s/.*string //; s/\"//g"; }
num() { dbus-send --system --print-reply --dest=$svc $1 com.victronenergy.BusItem.GetValue 2>/dev/null | grep variant | awk "{print \$NF}"; }
name=$(str /ProductName)
soc=$(num /Soc)
voltage=$(num /Dc/0/Voltage)
current=$(num /Dc/0/Current)
if [[ -n "$name" ]]; then
  printf "%-25s SoC: %5s%%  Voltage: %6sV  Current: %6sA\n" "$name" "$soc" "$voltage" "$current"
else
  echo "Virtual battery D-Bus service not responding yet"
fi'

echo ""
echo "$SEPARATOR"
echo "  Deployment Complete!"
echo "$SEPARATOR"
echo ""
echo "Configuration: /data/setupOptions/dbus-virtual-battery/"
echo "  smartshuntIndex - SmartShunt index if multiple found (default: 0)"
echo "  enableVirtual   - Enable virtual battery (default: true)"
echo "  chainCapacity   - Chain capacity in Ah (default: 280)"
echo "  instance        - D-Bus device instance (default: 514)"
echo "  productName     - Product name in GUI (default: Virtual Battery Chain 3)"
echo ""
echo "Commands:"
echo "  Update:    ./deploy.sh"
echo "  Uninstall: ssh $SSH_HOST '$APP_DIR/setup uninstall'"
echo "  Logs:      ssh $SSH_HOST 'tail -f /var/log/$SERVICE/current'"
