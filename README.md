# dbus-virtual-battery - Virtual Battery Calculator for Victron Venus OS

[![CI](https://github.com/victron-venus/dbus-virtual-battery/actions/workflows/ci.yml/badge.svg)](https://github.com/victron-venus/dbus-virtual-battery/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/victron-venus/dbus-virtual-battery)](https://github.com/victron-venus/dbus-virtual-battery/releases)
[![Downloads](https://img.shields.io/github/downloads/victron-venus/dbus-virtual-battery/total)](https://github.com/victron-venus/dbus-virtual-battery/releases)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Venus OS](https://img.shields.io/badge/Venus%20OS-3.x-blue)](https://github.com/victronenergy/venus)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)](https://github.com/victron-venus/dbus-virtual-battery)
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
- `--smartshunt-index 1` selects the second discovered SmartShunt when starting the service directly; SetupHelper passes `smartshuntIndex` through the same option. An explicit `--smartshunt` suffix takes precedence.
- Configure which SmartShunt to use via `setupOptions/smartshuntIndex` (zero-based index)

### Chain Auto-Discovery
- Automatically discovers ALL battery services on D-Bus
- Excludes:
  - `virtual_chain` (the virtual battery service itself)
  - The selected SmartShunt service
- All remaining battery services are treated as chains to subtract from the SmartShunt

### Manual Override
SmartShunt selection is configurable through SetupHelper; explicit source lists are available through the runtime CLI:
- `setupOptions/smartshuntIndex`: Select which SmartShunt to use (if multiple found)
- `--chains mqtt_chain1 mqtt_chain2`: Specify exact chain suffixes in a custom runtime launcher. The bundled SetupHelper script does not read a `setupOptions/chains` file; reinstalling regenerates its default launcher.

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
For a separately maintained runtime launcher, add `--chains mqtt_chain1 mqtt_chain2` to its Python command. The arguments are space-separated service suffixes. Do not start a second process alongside the supervised service. The bundled SetupHelper configuration retains automatic chain discovery.

### Custom Capacity
```bash
echo "400" > /data/setupOptions/dbus-virtual-battery/chainCapacity
# Use 400Ah capacity instead of default 280Ah
```

## System Architecture

```mermaid
graph LR
    A[SmartShunt] --> B[Total System Measurement]
    C[Chain 1] --> D[Battery 1 Measurements]
    E[Chain 2] --> F[Battery 2 Measurements]
    B & D & F --> G[dbus-virtual-battery<br/>SmartShunt - (Chain1 + Chain2 + ...) = Virtual Chain]
    G --> H[Virtual Chain<br/>Virtual Battery Measurements]
    H --> I[Victron GUI]
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
- Uses runtime files already extracted into `/data/dbus-virtual-battery/` and records the installed version

## Configuration Notes

- **SmartShunt Selection**: When multiple SmartShunts are present, use `smartshuntIndex` to select which one to use (0-based indexing)
- **Chain Selection**: By default, all discovered battery chains (excluding virtual_chain and SmartShunt) are used. An explicit list requires the runtime `--chains` arguments in a custom launcher; SetupHelper does not consume `setupOptions/chains`.
- **Capacity Setting**: The `chainCapacity` option sets the amp-hour capacity used for calculating Ah-related properties. Set this to match your actual battery bank capacity.
- **Service Management**: After installation, use Venus OS daemontools: `svc -d /service/dbus-virtual-chain` to stop, `svc -u /service/dbus-virtual-chain` to start, and `svc -t /service/dbus-virtual-chain` to restart the process

## Monitoring

Once installed and running, the virtual battery will appear in:
- Victron GUI (VRM Portal, etc.) as a battery device
- D-Bus under `com.victronenergy.battery.virtual_chain`
- Read logs with `tail -n 50 /var/log/dbus-virtual-chain/current`; the service uses native `multilog` rotation

## Dependencies

- Venus OS 2.8 or later
- Python 3.11+
- velib_python (included with Venus OS)
- dbus-python
- Either the separately installed `dbus_shared` package or the compatible `dbus_mqtt_battery` package already used by existing Venus installations. The helper must be importable; this repository does not bundle it. Errors inside an installed helper remain visible instead of being silently replaced.

## Source Code

This package contains:
- `dbus-virtual-battery.py` - Main virtual battery calculation service
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
2. Git tag (e.g., `v2.6.0`) that marks the release

When releasing:
1. Update the `version` file
2. Commit the change
3. Create and push a Git tag with the same version (prefixed with `v`)

## Release v2.7.4

Disconnected upstream sources no longer contribute cached measurements to the
virtual battery. This patch preserves existing discovery, timeout and recovery
behavior for sources without an explicit connection status.

### Source connection status

An upstream source reporting `/Connected = 0` is immediately treated as offline,
even if it still exposes its last measurements. A disconnected SmartShunt makes
the virtual battery unavailable; a disconnected chain is omitted and reported as
missing. Fresh connected readings restore normal calculations. Sources without
`/Connected` retain the existing measurement-based availability and timeout behavior.

Download the [v2.7.4 runtime archive](https://github.com/victron-venus/dbus-virtual-battery/releases/download/v2.7.4/dbus-virtual-battery-v2.7.4.tar.gz)
and its [SHA256 checksum](https://github.com/victron-venus/dbus-virtual-battery/releases/download/v2.7.4/dbus-virtual-battery-v2.7.4.tar.gz.sha256).
Use the existing SetupHelper installation procedure above. Venus OS libraries and
the separately installed `dbus_shared` package remain required.

## Release v2.7.3

The `--smartshunt-index` option now selects the requested discovered SmartShunt. The service reports its own version instead of the separately installed shared helper package's version.

GitHub stable and nightly downloads contain a `dbus-virtual-battery/` directory with the production entrypoint, executable SetupHelper `setup`, `gitHubInfo`, and `version`. A SHA256 checksum accompanies each archive. A compatible shared helper provider and Venus OS platform libraries remain prerequisites; the archive does not bundle or replace them.

## Venus OS source validity and persistence

The virtual current is a subtraction, so every configured source must publish
`/Connected=1` and finite voltage/current measurements. Cached numeric values
from a disconnected source are discarded. If any required chain or SmartShunt
is unavailable, `/Connected=0` and all derived measurements, capacity, time to
go, and estimated cell voltages become invalid. Source status paths identify
the missing input. This avoids assigning an unavailable chain's current to the
virtual chain. Complete live data restores calculations automatically.

SetupHelper installs `/data/dbus-virtual-battery/boot.sh` before an existing
`exit 0` in `/data/rc.local` to restore `/service/dbus-virtual-chain`. Install the
shared `dbus_shared` or `dbus_mqtt_battery` helper package first. `install.sh` is a
file-copy helper; running it from `/data/dbus-virtual-battery` is supported,
but SetupHelper still performs service registration. Logs use native `multilog`
with four rotated 25 KB files plus the current file.

Version 2.7.5 completes SetupHelper's installed-version bookkeeping. Start it
after the intended SmartShunt and MQTT chains are available: default source
discovery occurs at startup, so installation order must preserve that topology.

Calculator tests load the actual production function; no copied implementation
is used as the test subject. Separate source-loss regressions exercise the
production D-Bus update methods with hardware-free inputs.

The next revision uses monotonic time for the reader's one-second cache and
five-second reconnect interval, and clears cached values when the connection
changes. Wall-clock corrections therefore cannot extend cached source validity
or suppress transport recovery. These reader safeguards do not replace an
upstream service's own freshness reporting: `/Connected=1` with finite retained
values is indistinguishable from a new physical measurement on this interface.
