# Changelog

## [2.7.9] - Development line

### Release overview

Computes a virtual battery view on Venus OS for installations without a physical BMS. The existing README documents configuration and external interfaces for this development line.

### Maintenance

- Publish reviewed release notes from the exact source commit used to build each candidate, preserving build provenance.
- Document contribution checks, confidential security reporting and the project-specific trust boundaries.
- Require complete Bandit scans with no unresolved findings; reject malformed or incomplete scanner output. Document narrowly reviewed tooling and synthetic-fixture exceptions.

### Upgrade

These maintenance changes do not introduce a configuration or data migration. Retain local configuration and credentials when using the documented update procedure. Validate the candidate on an isolated system before production use; automated checks do not establish hardware acceptance.

### Security

Private vulnerability reporting and response policy are documented in SECURITY.md. This maintenance update strengthens release evidence and review instructions; it does not replace deployment authentication, network isolation or independent equipment safeguards. No new project CVE is announced by these changes.

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
