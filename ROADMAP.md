# Maintenance roadmap

This roadmap covers October 2026 through October 2027. Priorities are reviewed in public issues and pull requests. These are work items, not delivery-date promises or claims that a badge has been awarded.

1. Establish and verify the real emergency-access/continuity arrangement described in [GOVERNANCE.md](GOVERNANCE.md). This is an open mandatory Silver requirement.
2. Continue publishing cryptographically signed evidence for reviewed source and every distributed artifact, documenting identity-bound verification and testing rejection of altered artifacts. Repeat the [verified stable release process](docs/openssf-evidence.md) for each release; checksums alone are not signatures.
3. Keep the combined application, packaging and release-tooling test run above 80% of executable Python statements. Increase coverage of currently unexecuted release helpers and security-relevant error paths; do not remove them from the denominator to pass the gate.
4. Maintain the six-month bugfix/regression ledger. Resolve entries without linked regression evidence and refresh the reviewed time window before submitting a badge assessment.
5. Keep dependency/security analyses current and investigate findings; periodically re-evaluate the assumptions in [the security assurance case](docs/security-assurance.md), including native dependencies and deployment boundaries.
6. Maintain the [awarded Passing assessment](https://www.bestpractices.dev/en/projects/15435) and recheck each Silver criterion against the merged revision and public CI/release results. Human knowledge and response-history answers must come from the responsible maintainer, not repository prose.

## Scope and non-goals

Maintain reliable virtual battery telemetry, cold-start recovery and safe Venus OS installation. The project does not intend to replace physical BMS charge protection, operate hardware control loops, or embed a web service during this roadmap period.
