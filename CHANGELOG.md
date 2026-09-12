# Changelog

## [2.7.6] - 2026-09-12

### Fixed
- Use monotonic intervals for the D-Bus reader cache and reconnect throttle so a wall-clock correction cannot prolong stale measurements or postpone recovery.
- Clear cached readings whenever the reader connects or detects a disconnected transport.

## [2.7.5] - 2026-09-12

### Fixed
- Invalidate virtual battery measurements and connectivity when any required source disappears or returns invalid data.
- Reject non-finite measurements and preserve explicit source failures.
- Restore the persistent virtual battery service before `rc.local` exits and avoid copying an installed version file onto itself.
- Finalize SetupHelper installation so PackageManager records the installed release.
- Accept the existing `dbus_mqtt_battery` helper provider when the standalone `dbus_shared` package is absent.

Either `dbus_shared` or the compatible `dbus_mqtt_battery` helper package must be importable. Start the virtual service only after its intended SmartShunt and battery chains are available for discovery.
