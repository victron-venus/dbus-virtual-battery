"""Monotonic cache and reconnect regressions without a system D-Bus connection."""

from unittest.mock import Mock

from tests.fake_dbus import DBusException


def test_clock_rollback_cannot_keep_disconnected_chain_online(runtime, monkeypatch):
    clock = {"wall": 1000.0, "elapsed": 100.0}
    monkeypatch.setattr(runtime, "time", lambda: clock["wall"])
    monkeypatch.setattr(runtime, "monotonic", lambda: clock["elapsed"], raising=False)
    values = {
        "com.victronenergy.battery.ss": {
            "/Connected": 1,
            "/Dc/0/Voltage": 52,
            "/Dc/0/Current": 12,
            "/Soc": 80,
        },
        "com.victronenergy.battery.chain": {
            "/Connected": 1,
            "/Dc/0/Voltage": 52,
            "/Dc/0/Current": 3,
            "/Soc": 70,
        },
    }
    bus = runtime.get_bus.return_value
    bus.get_object.side_effect = lambda name, path: Mock(
        GetValue=lambda: values[name].get(path)
    )
    service = runtime.VirtualBatteryService(
        smartshunt_suffix="ss", chain_suffixes=["chain"]
    )
    service.update()
    assert service._dbusservice["/Dc/0/Current"] == 9
    clock.update(wall=500.0, elapsed=102.0)
    values["com.victronenergy.battery.chain"]["/Connected"] = 0
    service.update()
    assert service._dbusservice["/Connected"] == 0
    assert service._dbusservice["/Dc/0/Current"] is None
    clock["elapsed"] += 2
    values["com.victronenergy.battery.chain"]["/Connected"] = 1
    service.update()
    assert service._dbusservice["/Connected"] == 1
    assert service._dbusservice["/Dc/0/Current"] == 9


def test_clock_rollback_does_not_delay_reconnect(runtime, monkeypatch):
    clock = {"wall": 1000.0, "elapsed": 100.0}
    monkeypatch.setattr(runtime, "time", lambda: clock["wall"])
    monkeypatch.setattr(runtime, "monotonic", lambda: clock["elapsed"], raising=False)
    runtime.get_bus.side_effect = DBusException("offline")
    reader = runtime.DbusReader()
    assert reader.get_value("battery", "/Soc") is None
    bus = Mock()
    bus.get_object.return_value.GetValue.return_value = 75
    runtime.get_bus.side_effect = None
    runtime.get_bus.return_value = bus
    clock.update(wall=500.0, elapsed=106.0)
    assert reader.get_value("battery", "/Soc") == 75


def test_replaced_connection_cannot_reuse_cached_values(runtime, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(runtime, "time", lambda: clock[0])
    monkeypatch.setattr(runtime, "monotonic", lambda: clock[0], raising=False)
    old = runtime.get_bus.return_value
    old.get_object.return_value.GetValue.return_value = 1
    reader = runtime.DbusReader()
    assert reader.get_value("battery", "/Connected") == 1
    clock[0] += 0.2
    new = Mock()
    new.get_object.return_value.GetValue.return_value = 0
    runtime.get_bus.return_value = new
    assert reader._connect()
    assert reader.get_value("battery", "/Connected") == 0
