# Changelog

## [2.7.15] - Unreleased

### Changed

- Raise the dbus-python minimum in the requirements installation path from 1.5.0 to 1.5.1.
- Update the development linter to Ruff 0.17.2 and its lock, retaining the original dependency update.
- Refresh grouped CI pins and harden release publication against draft lookup and metadata propagation failures.

### Upgrade

Use the existing installation procedure and preserve configuration. The requirements installation path now requires dbus-python 1.5.1 or later. Battery aggregation logic is unchanged; verify D-Bus integration on the target Venus OS before accepting the update. Preserve an accepted package for rollback.

### Security

No new runtime vulnerability fix is claimed for the dbus-python minimum change. Keep local D-Bus access restricted. Required checks and source-bound release validation remain enabled.

## [2.7.14] - Unreleased

### Changed

- Update Ruff to 0.17.1 with a matching dependency lock.
- Use native uv dependency updates so manifest and lock changes stay together.
- Document bounded lock updates and refresh pinned shared CI workflows.

### Upgrade

Use the existing upgrade procedure and preserve configuration and data. This
maintenance release does not change battery calculations or require a migration.

### Security

Retain the existing access restrictions on the Venus OS host and its D-Bus
services. The development-tool updates do not add authentication to telemetry
sources or change their trust boundaries. Dependency and secret scans remain
required before publication.

## [2.7.13] - 2026-10-18

### Changed

- Route Dependabot metadata approval through the trusted default branch while preserving the existing author and review policy.
- Refresh pinned shared CI workflows and their source-bound release validation.

### Upgrade

Use the documented upgrade procedure and preserve local configuration and data. No configuration migration is required. Keep the previous immutable release available for rollback.

### Security

This maintenance release preserves the existing security and release-validation requirements. Publication does not deploy the service or establish physical-device acceptance.

## [2.7.12] - 2026-10-17

### Changed

- Keep the local package version in `uv.lock` synchronized through the release policy; dependency versions and hashes remain unchanged.

- Document the virtual battery data flow and link maintained source-bound RC fuzzing evidence.

### Upgrade

Use the existing update procedure and preserve local settings. Runtime behavior and configuration are unchanged.

### Security

This documentation maintenance release introduces no new vulnerability fix. Existing validation and device acceptance remain required.

## [2.7.11] - 2026-10-14

### Changed

- Require positive fuzz engine execution counts, instrumented production code and validated seed corpora before accepting RC evidence.
- Add regression tests for malformed reports, unsafe corpora and incomplete seed replay; retain the existing coverage requirements.
- Keep mutation campaigns restricted to public RCs and use deterministic seed checks in ordinary CI.

### Upgrade

Use the documented update procedure and preserve local configuration. No application configuration or data migration is introduced. Keep the previous accepted package available for rollback; the exact candidate still requires applicable device and integration acceptance.

### Security

RC publication rejects absent or invalid source-bound fuzz reports. The fuzz runner bounds corpus paths, file types and size. No application vulnerability or new target-device acceptance is claimed by these tooling changes.

## [2.7.10] - Development line

### Maintenance

- Require bounded fuzzing on public release candidates, with source-bound reports and retained diagnostics; beta and ordinary CI do not run mutation campaigns.
- Reject invalid capacity and non-finite calculations; cap duration before conversion to seconds.

### Upgrade

Use the documented update procedure and retain local configuration. Automated tests do not establish target-device acceptance.

### Security

Release qualification now requires isolated fuzzing against the candidate source. Report findings through SECURITY.md.

## [2.7.9] - Development line

### Release overview

Computes a virtual battery view on Venus OS for installations without a physical BMS. The existing README documents configuration and external interfaces for this development line.

### Maintenance

- Add non-activating DESTDIR installation/uninstallation with a validated payload manifest and link checks; retain operator-owned files.
- Quote product names as literal arguments in generated services and reject invalid numeric/membership setup inputs. Shell metacharacters in a configured name must never execute.
- Package the staging helper in both supported archive builders and check actual extracted installation/repeatable archive bytes.
- Measure application, packaging and release-tooling Python coverage together with the unchanged 80% gate.
- Document governance, remaining continuity requirements, security assurance, build/test boundaries and dated regression evidence.


- Include Ruff and the already required PyYAML test dependency in `uv.lock` for reproducible Python checks, preserving the existing locked runtime versions.
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
