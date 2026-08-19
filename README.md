# Virtual Battery Simulator

[![CI](https://github.com/victron-venus/virtual-battery/actions/workflows/ci.yml/badge.svg)](https://github.com/victron-venus/virtual-battery/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Venus OS](https://img.shields.io/badge/Venus%20OS-3.x-blue)](https://github.com/victronenergy/venus)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/victron-venus/virtual-battery/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/victron-venus/virtual-battery/pulls)

## Overview

The Virtual Battery Simulator creates a virtual battery by calculating values from a SmartShunt minus other battery chains. This is used for battery chains without a physical BMS (Battery Management System).

## Use Case Example

Imagine you have an energy storage system with:
- Five excellent Pylontech batteries with built-in BMS (Battery Management System) providing accurate telemetry
- Several older "dummy" batteries without BMS that are still in good condition but you don't want to discard
- A main SmartShunt measuring the total system current/power going to/from all batteries combined

The challenge is monitoring those old batteries - you need to know if their charging current becomes unreasonably low or if their power output has degraded significantly, so you can see this on your monitoring graphs (like Grafana) and take appropriate action.

This is exactly what the Virtual Battery Simulator solves:
1. The SmartShunt gives you the total system current (let's call it I_total)
2. Each of your five Pylontech batteries reports its individual current via MQTT/D-Bus (I_pylon1, I_pylon2, etc.)
3. By subtracting all the known battery currents from the total: I_virtual = I_total - ΣI_known_batteries
4. The result is the combined current of all your "dummy" batteries without BMS
5. This virtual battery's current/power appears in your monitoring system just like any other battery
6. You can now set up alerts when the virtual battery's current drops below a threshold, indicating degradation in your old batteries
7. You can visualize the virtual battery's performance over time alongside your other batteries

The virtual battery inherits voltage from the reference batteries (assuming parallel connection) and calculates its current as the remainder after subtracting all measured battery currents from the total system measurement.

## Architecture

```
    SmartShunt (total system) - Chain1 - Chain2 - ... - ChainN = Virtual Chain

    [SmartShunt] ----\
    [Chain 1]   ------ [This Script] --> D-Bus --> Victron GX
    [Chain 2]   ------/
    ...
    [Chain N]   ------/
```

The virtual battery inherits voltage from chain1/chainN (parallel connection) and calculates current as:
```
I_virtual = I_smartshunt - ΣI_chain1_to_N
V_virtual ≈ V_chain1 (assuming parallel connection)
```

When any source is missing, the script shows:
- Which sources are online/offline
- Partial data where available
- Warnings in the GUI

## Usage

```bash
./dbus-virtual-battery.py --smartshunt ttyUSB4 --chains mqtt_chain1 mqtt_chain2 mqtt_chain3 mqtt_chain4 mqtt_chain5
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
- `--chains`: Space-separated list of chain identifiers to subtract (e.g., mqtt_chain1 mqtt_chain2 ...)
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
