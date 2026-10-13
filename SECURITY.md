# Security policy

## Reporting a vulnerability

Send vulnerability details privately using [GitHub's Report a vulnerability form](https://github.com/victron-venus/dbus-virtual-battery/security/advisories/new). Include the affected commit or release, reproduction steps, impact and a suggested mitigation if known. Remove live secrets and personal information. Do not open a public issue with exploit details. If private reporting is temporarily unavailable, open a public issue requesting a confidential contact without disclosing the vulnerability.

Maintainers aim to acknowledge reports within 14 days, investigate promptly and coordinate disclosure with the reporter. Critical confirmed vulnerabilities receive priority. Confirmed exploitable medium-or-higher issues should be corrected within 60 days of confirmation. Coordinate normal public disclosure with a fix or effective mitigation. If active exploitation or another urgent risk requires earlier warning, promptly publish the affected scope and available protective steps while remediation continues. Release notes should identify any assigned CVE or equivalent advisory identifier for fixes. These are maintenance policies, not claims about historical response times.

## Supported code

Security fixes are developed on the current default branch and released through the repository's normal delivery process. Older releases are not guaranteed backports; reproduce against the current code where practical and include the original affected version in the report. A prerelease or development build is not a promise of production or hardware acceptance.

## Trust boundaries

Calculated battery values depend on configured inputs and do not provide physical cell protection. Restrict access to the local D-Bus and configuration. Validate behavior on an isolated system and retain independent battery, charger and inverter safety limits.

## Secure development and delivery

Validate external values at trust boundaries, reject unsupported or malformed commands, avoid shell interpolation, preserve certificate verification, and use maintained cryptographic libraries rather than custom cryptography. Apply least privilege to service accounts, repository tokens and filesystem permissions. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for validation and review.

Obtain source and published artifacts through the repository's HTTPS URLs. Verify published checksums or provenance when provided, over an authenticated channel. Keep local configuration, credentials and private keys out of source control and logs. Report suspected exposure through the private channel so credentials can be revoked and replaced; deleting a file alone does not revoke it.

[OpenSSF evidence and remaining verification](docs/openssf-evidence.md) is maintained separately from this policy.

## Recognition, credentials and assurance review

With the reporter's consent, acknowledge vulnerability reporters in the advisory or release notes. Offer anonymity, and do not make credit depend on public disclosure before remediation. This is the policy for future reports; it does not assert a history of reports or awards.

If a repository token, service credential or signing identity is compromised, revoke or disable it at its provider, replace it through the normal secret store, inspect access/publication logs and invalidate affected artifacts where necessary. A source-code deletion does not revoke a credential. Prefer scoped, short-lived credentials; never publish private recovery material.

[The project security assurance case](docs/security-assurance.md) records claims, test evidence and limitations. Revisit it when interfaces, privilege, transport, storage or release mechanisms change. The public issue/PR history records design decisions; confidential details stay in the private reporting channel until coordinated disclosure.

## Separate credential files

The battery runtime consumes local D-Bus measurements and needs no network
password or private key. Release maintenance delegates GitHub access to `gh`;
it does not embed tokens in project configuration. Authenticate using `gh auth
login --with-token < /private/path/token` when an operator supplies a dedicated
token file, or use the system credential store. Follow the
[GitHub CLI authentication documentation](https://cli.github.com/manual/gh_auth_login)
and keep token files outside the repository with owner-only permissions. The
file is read by `gh` during login; revocation or rotation requires replacing the
token at its provider and authenticating again, not just deleting the local file.

Git over SSH uses OpenSSH's `IdentityFile` (for example,
`~/.ssh/id_ed25519`) or an SSH agent; project configuration contains no private
key. [OpenSSH documents the key-file setting](https://man.openbsd.org/ssh_config#IdentityFile).
Scope this setting to the intended Git host and protect key-file permissions.
CI release signatures use a short-lived OIDC identity and ephemeral signing key;
there is no persistent signing private key to put in this repository.
