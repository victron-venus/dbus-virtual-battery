# Accessibility

The project provides a background service, command-line setup and Markdown
documentation. It does not supply its own graphical interface. Measurements are
published through named D-Bus paths; the Victron interface presents those values.

## Using the text interfaces

- Follow the README's numbered setup instructions and command examples with a
  keyboard. Its terminal installation alternative does not require navigating
  the PackageManager GUI. Logs are ordinary text and can be redirected or read
  with the operator's preferred tools.
- Inspect runtime options without starting a second service with
  `python3 -B /data/dbus-virtual-battery/dbus-virtual-battery.py --help`.
  The option names, defaults and descriptions are text; no colour or pointer
  action is needed. Use a terminal's wrapping, zoom or screen-reader features
  as appropriate. The `-B` option avoids writing import caches for this check.
- The architecture diagram has an adjacent prose description of its data flow.
- Documentation uses headings, descriptive links and text labels for badges.
  Follow a badge's link to read the underlying status rather than relying on its
  colour. GitHub provides the repository's rendered documentation and issue UI.
- Configuration identifiers and D-Bus paths are written as text so they can be
  copied without interpreting an image.

## Review and maintenance

The 2026-10-12 review of source `af08bdb5d6a9c25b34913fe2149916df48a870bb`
checked the README, contributor instructions, documentation and runtime help.
In GitHub's rendered README, the browser exposed 29 semantic headings, labels
for all 20 badge images, and header cells for the configuration table. Activating
the README's accessibility link with Enter opened this document. The architecture
paragraph supplies the diagram's data flow in reading order. The installed
Python 3.12.13 command above exited successfully and produced plain text with all
seven runtime options, including help, and no terminal escape sequences.
See the [review record](evidence/accessibility-2026-10-12.json).

This is an assessment of the project's text interfaces and authored content,
not a screen-reader test or a WCAG conformance certification. GitHub's application
and the Venus OS/VRM graphical interfaces are maintained by other projects; this
review does not establish their accessibility. There is no project-owned web,
GUI or full-screen terminal application. A browser accessibility tree alone
does not prove that every assistive technology works well.

When changing documentation or output, preserve descriptive link and image
labels, semantic heading order, text explanations for diagrams, plain-text
diagnostics and keyboard operation. Never make colour the only way to identify
a status. Recheck the affected interaction and record any remaining barrier.

Report a barrier through [GitHub Issues](https://github.com/victron-venus/dbus-virtual-battery/issues).
Describe the affected page or command, expected behaviour, platform and assistive
technology when relevant. Do not include private configuration or credentials.
