# Runtime hardening

The package runs as Python and shell source on the supported Venus OS platform.
It does not compile or ship its own Python interpreter, native extension,
web application or HTTP server. Runtime hardening therefore depends on the
interpreter, native libraries and kernel supplied by the installed firmware.
Keep that firmware and the separate shared-helper package maintained; a
Python-only implementation does not establish their memory safety.

## Measured deployment

A read-only inspection on 2026-10-12 of the running v2.7.9 service, source
`af08bdb5d6a9c25b34913fe2149916df48a870bb`, used a Cerbo GX with Venus OS v3.75,
ARMv7 and Python 3.12.13. No service, configuration, kernel setting or device
state was changed. The [ELF and process record](evidence/runtime-hardening-2026-10-12.json)
contains hashes and properties for the interpreter and all 43 loaded native
objects inspected at that point.

- The kernel's `randomize_va_space` was 2 and the service's `ADDR_NO_RANDOMIZE`
  personality flag was clear. Address randomization was enabled; this does not
  make a fixed-address executable position independent.
- All 44 inspected ELF files declared a non-executable `GNU_STACK` and a
  `GNU_RELRO` segment. The actual process stack mapping was non-executable.
- Five objects also requested immediate binding (`BIND_NOW` or an equivalent
  dynamic flag), giving full RELRO. The other 39, including Python, had partial
  RELRO. `readelf -h -l -d` independently confirmed Python's recorded properties.

These are actual exploit-mitigation mechanisms used by the deployment, rather
than a claim based on least privilege or the absence of first-party C code.

## Limits

The Python launcher was `ET_EXEC`, not PIE. One writable-and-executable mapping
was present, so this process does **not** establish comprehensive W^X protection.
The Python build flags and inspected symbols do not establish comprehensive
stack-canary or fortified-function coverage. A missing canary symbol is not a
function-by-function proof that no compiler protection exists, and a present
symbol does not establish coverage of every vulnerable operation.

This snapshot is specific to the recorded firmware and file hashes; it is not
evidence for all Venus OS versions, every process state, exploit resistance,
sanitizer coverage or the firmware's overall security. Reassess it after changing
firmware or native dependencies. Do not replace the device's interpreter or
change global kernel settings merely to improve an assessment score. Platform
mitigation gaps require an upstream firmware change and compatibility testing.

## Repeating the inspection

An authorized operator can read the running service's `/proc/<pid>/exe`,
`/proc/<pid>/maps` and `/proc/<pid>/personality`, and
`/proc/sys/kernel/randomize_va_space`. Inspect the executable and each unique
file-backed native object in its mappings with `readelf -h -l -d`, then record
SHA-256 hashes. Check `GNU_STACK` execute permission, `GNU_RELRO`, dynamic
`BIND_NOW`/`FLAGS`/`FLAGS_1`, ELF type and actual stack/W+X mappings separately.
Record only aggregate mapping properties, never raw addresses, arguments,
credentials or environment contents in public evidence.
