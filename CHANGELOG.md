# Changelog

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
