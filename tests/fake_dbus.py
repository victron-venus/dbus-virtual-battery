"""Minimal fake dbus/vedbus module shims for testing without Venus OS.

Why: the runtime entrypoint imports `dbus`, `vedbus`, and `dbus_shared` — all
Venus OS-only. The pure calculator in tests/calculator.py does NOT need any
of them, so it tests cleanly. This file documents the small set of symbols
that the runtime expects, so a future PR extending coverage to the
DbusReader/VirtualBatteryService classes has a starting point. It is NOT
imported by anything yet.

ponytail: a stub here is enough; if real DBusReader tests land, build out
the fake (Service registry, ObjectProxy with GetValue, GetObject) or pull
in dbus-python's test harness.
"""
