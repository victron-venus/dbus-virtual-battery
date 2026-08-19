# Virtual Battery Simulator

[![CI](https://github.com/victron-venus/virtual-battery/actions/workflows/ci.yml/badge.svg)](https://github.com/victron-venus/virtual-battery/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Venus OS](https://img.shields.io/badge/Venus%20OS-3.x-blue)](https://github.com/victronenergy/venus)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/victron-venus/virtual-battery/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/victron-venus/virtual-battery/pulls)

## Overview

The Virtual Battery Simulator creates a virtual battery by calculating values from a SmartShunt minus other battery chains. This is used for battery chains without a physical BMS (Battery Management System).

## Architecture

```
    SmartShunt (total system) - Chain1 - Chain2 = Virtual Chain3

    [SmartShunt] ----\
    [Chain 1]   ------ [This Script] --> D-Bus --> Victron GX
    [Chain 2]   ------/
```

The virtual battery inherits voltage from chain1/chain2 (parallel connection) and calculates current as:
```
SmartShunt_current - chain1_current - chain2_current
```

When any source is missing, the script shows:
- Which sources are online/offline
- Partial data where available
- Warnings in the GUI

## Usage

```bash
./dbus-virtual-battery.py --smartshunt ttyUSB4 --chains mqtt_chain1 mqtt_chain2
```

## Installation

1. Copy `dbus-virtual-battery.py` to your Victron Venus OS device
2. Ensure Python 3.7+ is available
3. Install required dependencies (if not already present):
   ```bash
   pip install pyyaml
   ```
4. Make the script executable:
   ```bash
   chmod +x dbus-virtual-battery.py
   ```

## Configuration

The script accepts the following command-line arguments:
- `--smartshunt`: Device path for the SmartShunt (e.g., ttyUSB4)
- `--chains`: Space-separated list of chain identifiers to subtract (e.g., mqtt_chain1 mqtt_chain2)
- `--help`: Show help message

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

This tool is part of the Victron Venus OS ecosystem:
- [dbus-mqtt-battery](https://github.com/victron-venus/dbus-mqtt-battery) - MQTT to D-Bus bridge for JBD BMS batteries
- [inverter-control](https://github.com/victron-venus/inverter-control) - Grid-zero feed-in control for Victron inverters
- [venus-os-ci-toolkit](https://github.com/victron-venus/venus-os-ci-toolkit) - Reusable GitHub Actions workflows

## Support

For issues, questions, or contributions, please use the [GitHub Issues](https://github.com/victron-venus/virtual-battery/issues) section of this repository.
