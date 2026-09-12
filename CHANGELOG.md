# Changelog

## [2.7.5] - 2026-09-12

### Fixed
- Invalidate virtual battery measurements and connectivity when any required source disappears or returns invalid data.
- Use a monotonic clock for source freshness, reject non-finite measurements, and preserve explicit source failures.
- Log source availability transitions instead of repeating the same healthy state every minute.
- Restore the persistent virtual battery service before `rc.local` exits and avoid copying an installed version file onto itself.
- Finalize SetupHelper installation so PackageManager records the installed release.
- Accept the existing `dbus_mqtt_battery` helper provider when the standalone `dbus_shared` package is absent.

Either `dbus_shared` or the compatible `dbus_mqtt_battery` helper package must be importable. Start the virtual service only after its intended SmartShunt and battery chains are available for discovery.
