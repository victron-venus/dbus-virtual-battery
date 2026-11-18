# Documentation

A D-Bus service that computes and publishes a virtual battery on Venus OS, with
its hardening, accessibility notes and release records.

## Operate it

- [Runtime hardening](runtime-hardening.md) — how the package runs as Python and shell source on the platform.
- [Accessibility](accessibility.md) — the service, command-line setup and Markdown output the project provides.

## Assurance

- [Security assurance case](security-assurance.md) — what the case covers inside an operator-controlled installation.
- [Quality and build evidence](quality-and-build.md) — the `scripts/ci.sh` path and the isolated environment it creates.
- [Reproducing the maintained-source coverage bound](evidence/coverage-scope-method.md) — inventorying reviewed source without executing it.
- [OpenSSF Best Practices evidence: dbus-virtual-battery](openssf-evidence.md) — the index behind the Passing assessment.

## Releases

- [Release operations](release-packaging.md) — what `release.sh` delegates and which events validate what.
- [Release version inputs](release-versioning.md) — the `versioning` fields that identify a release.
- [Verify a signed release](release-signatures.md) — checking a signed artefact.
- [CI and release operations](release-workflow.md) — `.release-policy.json` and the required status.
- [CI orchestration](CI-ORCHESTRATION.md) — how the quality gate and release pipeline divide the events.
- [Version plans and manifest synchronization](VERSIONING.md) — the versioning opt-in.
- [Release-candidate fuzz testing](fuzzing.md) — the illustrated RC fuzzing process.
- [Fuzzing release candidates](rc-fuzzing.md) — the reusable bounded fuzz workflow.
- [Release read recovery and rerun validation](release-read-safety.md) — the two fixes carried from the shared toolkit.
- [Early final-build runner check](runner-preflight.md) — why the check runs before the final build.
