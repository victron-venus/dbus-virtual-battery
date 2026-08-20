# dbus-virtual-battery - Virtual Battery Calculator for Victron Venus OS

[![CI](https://github.com/victron-venus/dbus-virtual-battery/actions/workflows/ci.yml/badge.svg)](https://github.com/victron-venus/dbus-virtual-battery/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/releases)
[![Downloads](https://img.shields.io/github/downloads/victron-venus/dbus-virtual-battery/total)](https://github.com/victron-venus/dbus-virtual-battery/releases)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Venus OS](https://img.shields.io/badge/Venus%20OS-3.x-blue)](https://github.com/victronenergy/venus)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)](https://github.com/victron-venus/dbus-virtual-battery)
[![GitHub stars](https://img.shields.io/github/stars/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/watchers)
[![GitHub contributors](https://img.shields.io/github/contributors/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/graphs/contributors)
[![GitHub issues](https://img.shields.io/github/issues/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/issues)
[![GitHub closed issues](https://img.shields.io/github/issues-closed/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/issues?q=is%3Aissue+is%3Aclosed)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/pulls)
[![GitHub last commit](https://img.shields.io/github/last-commit/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/commits/main)
[![Code size](https://img.shields.io/github/languages/code-size/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery)
[![Repo size](https://img.shields.io/github/repo-size/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/victron-venus/dbus-virtual-battery/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/victron-venus/dbus-virtual-battery/pulls)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Victron Community](https://img.shields.io/badge/Victron-Community-blue)](https://community.victronenergy.com/)

## Overview

The dbus-virtual-battery service creates a virtual battery by calculating values from a SmartShunt minus other battery chains on the D-Bus. This is used for battery chains without a physical BMS (Battery Management System) where you want to estimate their combined state by subtracting measured chains from the total system measurement.

## Auto-Discovery Features

### SmartShunt Auto-Discovery
- Automatically discovers all SmartShunt services on D-Bus matching patterns (`ttyUSB*`, `ttyACM*`, `ve_bus`, `ve.can`, `smartshunt`, `shunt`)
- Uses the first discovered SmartShunt by default (index 0)
- Configure which SmartShunt to use via `setupOptions/smartshuntIndex` (zero-based index)

### Chain Auto-Discovery  
- Automatically discovers ALL battery services on D-Bus
- Excludes:
  - `virtual_chain` (the virtual battery service itself)
  - The selected SmartShunt service
- All remaining battery services are treated as chains to subtract from the SmartShunt

### Manual Override
All auto-discovery can be overridden via configuration:
- `setupOptions/smartshuntIndex`: Select which SmartShunt to use (if multiple found)
- `setupOptions/chains`: Specify exact chain service suffixes to subtract (comma-separated, disables auto-discovery)

## Configuration Options

The service is configured via SetupHelper using files in `/data/setupOptions/dbus-virtual-battery/`:

| Option File | Default | Description |
|-------------|---------|-------------|
| `smartshuntIndex` | `0` | Index of SmartShunt to use when multiple are found (0 = first) |
| `enableVirtual` | `true` | Enable virtual battery (should remain true for this package) |
| `chainCapacity` | `280` | Chain capacity in Ah (used for Ah calculated properties) |
| `instance` | `514` | D-Bus device instance |
| `productName` | `Virtual Battery Chain 3` | Product name displayed in Victron GUI |

## Usage Examples

### Default Configuration (Recommended)
```bash
# Auto-discover first SmartShunt
# Auto-discover all chains (excluding virtual_chain and SmartShunt)
# Uses instance 514, capacity 280Ah, product name "Virtual Battery Chain 3"
```

### Select Specific SmartShunt Index
```bash
echo "1" > /data/setupOptions/dbus-virtual-battery/smartshuntIndex
# Use the second SmartShunt found (index 1)
```

### Manual Chain Specification  
```bash
echo "mqtt_chain1,mqtt_chain2" > /data/setupOptions/dbus-virtual-battery/chains
# Subtract only these specific chains (disables auto-discovery)
```

### Custom Capacity
```bash
echo "400" > /data/setupOptions/dbus-virtual-battery/chainCapacity  
# Use 400Ah capacity instead of default 280Ah
```

## System Architecture

```
[SmartShunt] --> [Total System Measurement]  
[Chain 1] --> [Battery 1 Measurements]  
[Chain 2] --> [Battery 2 Measurements]  
                          ↓
[dbus-virtual-battery] --> SmartShunt - (Chain1 + Chain2 + ...) = Virtual Chain
                          ↓
[Virtual Chain] --> [Virtual Battery Measurements] --> Victron GUI
```

The virtual battery service appears on D-Bus as:
`com.victronenergy.battery.virtual_chain`

## Installation

### Option 1: SetupHelper (Recommended)

1. **Configure (optional, before install)**  
   ```bash
   mkdir -p /data/setupOptions/dbus-virtual-battery
   
   # SmartShunt index (0 = first, 1 = second, etc.)
   echo "0" > /data/setupOptions/dbus-virtual-battery/smartshuntIndex
   
   # Chain capacity in Ah (default: 280 for 4x 70Ah batteries)
   echo "280" > /data/setupOptions/dbus-virtual-battery/chainCapacity
   
   # D-Bus instance (default: 514)
   echo "514" > /data/setupOptions/dbus-virtual-battery/instance
   
   # Product name for GUI (default: "Virtual Battery Chain 3")
   echo "Virtual Battery Chain 3" > /data/setupOptions/dbus-virtual-battery/productName
   ```
   
   > **Note**: Virtual battery is **enabled by default**. The `enableVirtual` option exists but should remain `true`.

2. **Install**  
   - PackageManager → dbus-virtual-battery → Install

### How PackageManager Works

PackageManager discovers packages by scanning `/data/` for directories containing both a `version` file and a `setup` script. The `setup` script (sourced from this repo) is executed with the `INSTALL` action by SetupHelper, which:

- Creates the virtual battery service (`dbus-virtual-chain`) 
- Copies Python scripts to `/data/dbus-virtual-battery/`

## Configuration Notes

- **SmartShunt Selection**: When multiple SmartShunts are present, use `smartshuntIndex` to select which one to use (0-based indexing)
- **Chain Selection**: By default, all discovered battery chains (excluding virtual_chain and SmartShunt) are used. To specify exact chains, use the `chains` option with comma-separated service suffixes (e.g., `mqtt_chain1,mqtt_chain2`)
- **Capacity Setting**: The `chainCapacity` option sets the amp-hour capacity used for calculating Ah-related properties. Set this to match your actual battery bank capacity.
- **Service Management**: After installation, use `svcadm enable/disable/restart dbus-virtual-chain` to manage the service

## Monitoring

Once installed and running, the virtual battery will appear in:
- Victron GUI (VRM Portal, etc.) as a battery device
- D-Bus under `com.victronenergy.battery.virtual_chain`
- Logs accessible via `svlogd /var/log/dbus-virtual-chain`

## Dependencies

- Venus OS 2.8 or later
- Python 3.7+
- velib_python (included with Venus OS)
- dbus-python

## Source Code

This package contains:
- `dbus-virtual-battery.py` - Main virtual battery calculation service
- `dbus_mqtt_battery/` - Shared utility package (D-Bus helpers, configuration)
- `setup` - SetupHelper compatible installation script
- `version` - Package version
- `install.sh` - Venus OS installer (for manual installation)
- `register-package.sh` - Package registration helper
- `release.sh` - Release automation script

## Versioning

Version numbers consist of three fields: Major.Minor.Patch
- Major: Backwards-incompatible changes
- Minor: Backwards-compatible feature additions  
- Patch: Backwards-compatible bug fixes

Version is stored in:
1. `version` file (read by runtime/dashboards)
2. `dbus_mqtt_battery/config.py` (used by setuptools/pip)  
3. Git tag (e.g., `v2.6.0`) that marks the release

When releasing:
1. Update `dbus_mqtt_battery/config.py` version
2. Update the `version` file to the same string
3. Commit both changes
4. Create and push a Git tag with the same version (prefixed with `v`)