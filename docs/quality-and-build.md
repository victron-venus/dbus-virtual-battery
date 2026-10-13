# Quality and build evidence

## Test boundary

Run `bash scripts/ci.sh --install` with uv 0.12.18, then `bash scripts/ci.sh`. This creates an isolated `.venv-ci`, installs the checked-in lock and the separate hash-pinned scanner, and runs the checked-in lint and combined test policy. `CI_PYTHON` may point at an already prepared interpreter when running checks; installation uses `.venv-ci`.

The combined pytest invocation includes `tests/`, `.github/workflow-tests/` and `.github/release-tests/`. Coverage uses the repository root with namespace-package discovery so unimported maintained Python scripts remain visible at zero coverage. It excludes test code, virtual environments. Shell and workflow configuration are exercised by contract/installation tests but are not part of the Python-statement denominator. Third-party installed libraries are outside that denominator. The enforced threshold remains 80%; there is no branch-coverage claim.

[Machine-readable measurement](evidence/coverage-2026-10-12.json) records the measured source hashes, executable/covered statements, test result and environment. Those hashes bind the result to the tested source, without a circular commit hash in the evidence file. A local run is not hosted CI: inspect the pull request's actual required checks before merging or submitting a badge assessment. The [regression ledger](evidence/regressions-2026-10-12.json) records recent fix/test links and gaps; a test count is not a bugfix ratio.

## Repeating the build

No native compiler is required to package this Python service. From a reviewed checkout with Python 3.12.13:

```bash
.venv-ci/bin/python scripts/build_release.py "$(cat version)"
```

The archive declares all runtime and staging-installer inputs in `.release-package.json`; timestamps and owner fields are normalized and executable modes preserved. `tests/test_release_package.py` builds the actual payload twice, compares the bytes, checks extracted runtime imports with explicit driver substitutes, and stages the extracted package without starting a service. `tests/test_candidate_package.py` also checks malformed identity, missing inputs, symlinks and stale output. Host/compiler-independent runtime behavior is a separate question from repeatable archive bytes.

For a packaging host, use an empty directory you control:

```bash
DESTDIR="$PWD/stage-root" bash setup install
DESTDIR="$PWD/stage-root" bash setup uninstall
```

The payload is placed under `stage-root/data/dbus-virtual-battery`. This mode does not source SetupHelper, contact D-Bus, modify boot state or start a service. Uninstall uses a validated manifest and preserves unrelated operator files. Empty/root DESTDIR and linked destination paths are rejected. Conventional Venus OS installation without DESTDIR continues through SetupHelper; review its documented configuration before live use.

## Review policy and limits

Contributions must resolve new warnings, preserve enforced checks, test important success and failure paths, and explain untested behavior. Keep bug-regression evidence current for the preceding six months. No local result here is a physical-device acceptance test or a security certification. See [CONTRIBUTING.md](../CONTRIBUTING.md) for review requirements and [the assurance case](security-assurance.md) for security-specific evidence.

## Warning policy

Python warnings are errors during the entire pytest suite (`filterwarnings = ["error"]`), including release and workflow contracts. Ruff lint and formatting checks fail CI. Do not add a blanket warning ignore: fix a warning, or document a narrowly matched upstream exception with its rationale. This chooses the useful warning mechanisms for Python rather than enabling mutually conflicting style rules.
