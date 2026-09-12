"""Small hardware-free driver doubles; all calculator/service logic is production code."""

from types import ModuleType, SimpleNamespace
from unittest.mock import Mock


class DBusException(Exception):
    """Fake transport exception with the same catch boundary as dbus-python."""


class FakeService(dict):
    """Record registered paths and reject writes to unregistered paths."""

    def __init__(self, name, bus, register=False):
        super().__init__()
        self.name = name
        self.bus = bus
        self.registered = register

    def add_path(self, path, value, **_options):
        """Declare a writable service path as vedbus does."""
        dict.__setitem__(self, path, value)

    def __setitem__(self, path, value):
        if path not in self:
            raise KeyError(f"Unregistered D-Bus path: {path}")
        super().__setitem__(path, value)

    def register(self):
        """Mark the service ready after its paths have been declared."""
        self.registered = True


def driver_modules():
    """Provide only imported driver symbols, without opening any real bus."""
    dbus = ModuleType("dbus")
    dbus.Array = list
    dbus.exceptions = SimpleNamespace(DBusException=DBusException)
    vedbus = ModuleType("vedbus")
    vedbus.VeDbusService = FakeService
    shared = ModuleType("dbus_shared")
    shared.PATH_DC_VOLTAGE = "/Dc/0/Voltage"
    shared.PATH_DC_CURRENT = "/Dc/0/Current"
    shared.PATH_DC_POWER = "/Dc/0/Power"
    shared.VERSION = "test"
    shared.POLL_INTERVAL_MS = 1000
    shared.get_bus = Mock()
    shared.setup_main_loop = Mock()
    shared.register_signal_handlers = Mock()
    shared.create_poll_function = Mock()
    shared.run_main_loop = Mock()

    def common_paths(service, **options):
        service.add_path("/Connected", 0)
        service.add_path("/CustomName", options["product_name"])

    def dc_paths(service, **_options):
        for path in ("/Dc/0/Voltage", "/Dc/0/Current", "/Dc/0/Power"):
            service.add_path(path, None)

    shared.setup_dbus_paths_common = common_paths
    shared.setup_dbus_paths_dc = dc_paths
    return {"dbus": dbus, "vedbus": vedbus, "dbus_shared": shared}
