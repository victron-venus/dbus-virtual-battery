# Security assurance case

## Claim and operating assumptions

Within an operator-controlled Venus OS installation, the service calculates and publishes a virtual battery view without silently treating unavailable required inputs as healthy. The operator controls the D-Bus service/configuration and supplies trustworthy physical measurements. The calculation is **not a battery management system**, cell protection, or evidence that a charger/inverter installation is safe.

Assets are correct and fresh reported measurements, service availability, operator configuration, and authenticated release artifacts. Entry points are D-Bus replies and service discovery, CLI/setup options, local deployment paths and release metadata. A malicious local administrator or compromised upstream measurement source remains outside the trust the calculation can establish.

## Argument and evidence

- Missing, invalid or stale inputs must invalidate dependent output. [Runtime tests](../tests/test_runtime.py) exercise disconnect/recovery and clearing dependent measurements. [Cold-start tests](../tests/test_black_start.py) cover delayed sources, immutable membership, stale timestamps and atomic snapshots. [Timing tests](../tests/test_runtime.py) cover monotonic expiry/reconnect behavior.
- Battery membership must not silently switch during recovery. The configured chain set and SmartShunt selection are checked in the cold-start tests; calculator tests verify arithmetic separately from I/O. A mock boundary does not prove firmware or driver behavior.
- Setup configuration must remain data in the generated shell service. [Installer tests](../tests/test_setup_installation.py) execute the generated script with an inert argument recorder and shell-metacharacter/newline input, and reject malformed numeric/membership options before creation. No real service is started by these tests.
- Host packaging must not overwrite linked operator files or require live installation. [Staging tests](../tests/test_install_staging.py) verify payload/modes, non-root DESTDIR, link rejection, manifest validation and preservation of unrelated files. This assumes the staging directory is controlled by the caller; it is not a defense against a privileged attacker changing paths concurrently.
- Release identity and filesystem boundaries are tested by the release contract suite. The security gate rejects incomplete/erroring Bandit reports and every unresolved finding; [gate tests](../tests/test_security_gate.py) prove those failure cases. A successful scanner does not prove absence of vulnerabilities.

## Crypto and native-code boundary

The application has no password database or custom cryptographic algorithm. Local D-Bus access control is provided by the deployment. Source/download transport and release identity belong to the delivery layer. Use authenticated HTTPS and verify the published signing identity when signatures are available; a bare SHA-256 checksum only detects changes relative to a trusted checksum.

Maintained application and tooling source is Python and shell. No first-party C/C++ source is compiled by this repository. Python, dbus-python, PyGObject/GLib and host libraries contain native code: their memory safety is not established by Python coverage. Keep those dependencies and Venus OS patched, consult their security advisories and use their upstream dynamic-analysis evidence where applicable. Reassess memory-safety tooling before introducing generated or maintained C/C++ code. Do not claim project ASan coverage from a Python test run.

[Runtime hardening](runtime-hardening.md) records a read-only inspection of the
actual Venus OS process: enabled ASLR, non-executable stack and RELRO, together
with the non-PIE launcher, partial RELRO and W+X limitations. Those measured
platform protections are separate from application memory safety and privilege.

## Remaining evidence

The original implementation review did not perform physical-device acceptance.
Subsequent acceptance of the exact v2.7.9 RC2 and its unchanged signed stable
publication is recorded in [PR #91](https://github.com/victron-venus/dbus-virtual-battery/pull/91)
and [the stable release](https://github.com/victron-venus/dbus-virtual-battery/releases/tag/v2.7.9).
See [quality evidence](quality-and-build.md) for measured statement coverage and
limitations. Continuity/recovery remains an explicit [roadmap](../ROADMAP.md)
item. Revisit this argument after changes to input trust, freshness, permissions,
setup or delivery.

## Implemented release signing

The opted-in release workflow delegates signing to pinned Cosign 3.1.3. Its default [ECDSA P-256 generation uses Go crypto/rand](https://github.com/sigstore/cosign/blob/v3.1.3/pkg/cosign/keys.go). The project uses standard SHA-256 digests and does not implement its own cryptography. [Recipient verification](release-signatures.md) binds the signature to the expected repository, workflow, branch and reviewed source commit before inspecting every payload. Ephemeral signing keys are not a claim about forward secrecy of every deployment transport. A real signed publication must still be verified before marking the Silver release-signature requirement complete.
