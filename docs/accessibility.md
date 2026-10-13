# Accessibility

The project provides a background service, command-line setup and Markdown
documentation. It does not supply its own graphical interface. Measurements are
published through named D-Bus paths; the Victron interface presents those values.

## Using the text interfaces

- Follow the README's numbered setup instructions and command examples with a
  keyboard. Logs are ordinary text and can be redirected or read with the
  operator's preferred tools.
- The architecture diagram has an adjacent prose description of its data flow.
- Documentation uses headings, descriptive links and text labels for badges.
  Follow a badge's link to read the underlying status rather than relying on its
  colour. GitHub provides the repository's rendered documentation and issue UI.
- Configuration identifiers and D-Bus paths are written as text so they can be
  copied without interpreting an image.

## Review boundary

This review checked the repository's Markdown, diagram description and text
interfaces. It did not test a screen reader with the installed Venus OS GUI or
every GitHub page. Those interfaces have their own accessibility behaviour; the
project does not claim WCAG conformance for them. The OpenSSF assessment records
the remaining review requirement.

Report a barrier through [GitHub Issues](https://github.com/victron-venus/dbus-virtual-battery/issues).
Describe the affected page or command, expected behaviour, platform and assistive
technology when relevant. Do not include private configuration or credentials.
