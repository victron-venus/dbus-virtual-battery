"""Exercise production D-Bus reader and service logic without devices."""

# These tests exercise service internals and inspect registered D-Bus values.
# pylint: disable=protected-access

from unittest.mock import Mock

import pytest

from tests.fake_dbus import DBusException


def test_reader_connect_failure_and_reconnect_throttle(runtime, monkeypatch):
    """A failed connection retries only after the configured interval."""
    clock = [1.0]
    monkeypatch.setattr(runtime, "time", lambda: clock[0])
    bus = Mock()
    runtime.get_bus.side_effect = [DBusException("unavailable"), bus]
    reader = runtime.DbusReader()
    assert reader.bus is None
    assert reader.get_value("battery", "/Soc") is None
    assert not reader.service_exists("battery")
    assert reader.list_battery_services() == []
    assert runtime.get_bus.call_count == 1
    clock[0] = 6.0
    bus.get_object.return_value.GetValue.return_value = 80
    assert reader.get_value("battery", "/Soc") == 80.0
    assert runtime.get_bus.call_count == 2


@pytest.mark.parametrize(
    "value, expected",
    [(None, None), ([], None), ("bad", None), ("51.2", 51.2), (12, 12.0)],
)
def test_reader_values(runtime, value, expected):
    """D-Bus values normalize to floats while missing or invalid values stay unknown."""
    bus = runtime.get_bus.return_value
    bus.get_object.return_value.GetValue.return_value = value
    assert runtime.DbusReader().get_value("battery", "/value") == expected


def test_reader_cache_expires(runtime, monkeypatch):
    """Fresh cached values avoid transport calls and expired values are refreshed."""
    clock = [100.0]
    monkeypatch.setattr(runtime, "time", lambda: clock[0])
    bus = runtime.get_bus.return_value
    bus.get_object.return_value.GetValue.side_effect = [50, 51]
    reader = runtime.DbusReader()
    assert reader.get_value("battery", "/voltage") == 50
    clock[0] += 0.5
    assert reader.get_value("battery", "/voltage") == 50
    assert bus.get_object.call_count == 1
    clock[0] += 1.0
    assert reader.get_value("battery", "/voltage") == 51
    assert bus.get_object.call_count == 2


@pytest.mark.parametrize(
    "message, disconnected",
    [
        ("UnknownObject", False),
        ("NameHasNoOwner", False),
        ("other error", False),
        ("Connection refused", True),
        ("org.freedesktop.DBus.Error.Disconnected", True),
    ],
)
def test_reader_handles_transport_errors(runtime, message, disconnected):
    """Only disconnect errors invalidate the transport connection."""
    bus = runtime.get_bus.return_value
    bus.get_object.side_effect = DBusException(message)
    reader = runtime.DbusReader()
    assert reader.get_value("battery", "/value") is None
    assert (reader.bus is None) is disconnected


def test_reader_discovers_only_matching_external_batteries(runtime):
    """Discovery filters non-battery services and excludes the virtual service."""
    bus = runtime.get_bus.return_value
    bus.list_names.return_value = [
        "com.other.service",
        "com.victronenergy.battery.mqtt_chain2",
        "com.victronenergy.battery.mqtt_chain1",
        "com.victronenergy.battery.virtual_chain",
        "com.victronenergy.battery.ttyUSB0",
    ]
    reader = runtime.DbusReader()
    assert reader.service_exists("battery")
    assert reader.list_battery_services() == ["mqtt_chain1", "mqtt_chain2"]
    assert reader.list_battery_services("", "virtual_chain") == [
        "mqtt_chain1",
        "mqtt_chain2",
        "ttyUSB0",
    ]
    bus.list_names.side_effect = DBusException("unavailable")
    bus.get_object.side_effect = DBusException("unavailable")
    assert reader.list_battery_services() == []
    assert not reader.service_exists("battery")


def make_service(runtime, monkeypatch, discovered=None, **options):
    """Replace the transport reader, retaining the actual service implementation."""
    reader = Mock()
    reader.list_battery_services.return_value = discovered or []
    reader.get_value.return_value = None
    reader.service_exists.return_value = False
    monkeypatch.setattr(runtime, "DbusReader", Mock(return_value=reader))
    return runtime.VirtualBatteryService(**options), reader


def test_service_registration_and_explicit_sources(runtime, monkeypatch):
    """Service setup registers expected measurement paths and explicit source names."""
    service, _ = make_service(
        runtime, monkeypatch, smartshunt_suffix="ttyUSB0", chain_suffixes=["a", "b"]
    )
    paths = service._dbusservice
    assert paths.registered
    assert paths["/InstalledCapacity"] == 280
    assert paths["/System/NrOfModulesOffline"] == 3
    assert paths["/Voltages/Cell16"] is None
    assert paths["/Info/DataComplete"] == 0
    assert [chain.service for chain in service.chains] == [
        "com.victronenergy.battery.a",
        "com.victronenergy.battery.b",
    ]


@pytest.mark.parametrize(
    "discovered, index, expected",
    [
        (["mqtt_chain1", "ttyUSB0", "ttyUSB1"], 1, "ttyUSB1"),
        (["mqtt_chain1", "ttyUSB0"], 9, "ttyUSB0"),
        (["custom_battery"], 0, "custom_battery"),
        ([], 0, None),
    ],
)
def test_service_auto_discovery(runtime, monkeypatch, discovered, index, expected):
    """Discovery honors the selected index and safely handles unavailable candidates."""
    service, _ = make_service(
        runtime, monkeypatch, discovered=discovered, smartshunt_index=index
    )
    assert service.smartshunt_suffix == expected
    assert [chain.service for chain in service.chains] == [
        f"com.victronenergy.battery.{name}" for name in discovered if name != expected
    ]


def test_source_timeout_and_power_fallback(runtime, monkeypatch):
    """A source becomes stale after timeout and derives missing power from voltage/current."""
    clock = [100.0]
    monkeypatch.setattr(runtime, "time", lambda: clock[0])
    service, reader = make_service(
        runtime, monkeypatch, smartshunt_suffix="ss", chain_suffixes=["chain"]
    )
    source = service.smartshunt
    reader.get_value.side_effect = [50, -2, 80, None]
    assert service._read_source(source)
    assert source.power == -100
    assert source.online
    reader.get_value.side_effect = None
    reader.get_value.return_value = None
    reader.service_exists.return_value = True
    clock[0] += 10
    assert not service._read_source(source)
    assert source.online
    clock[0] += runtime.DATA_TIMEOUT
    assert not service._read_source(source)
    assert not source.online


def test_update_publishes_calculator_values_and_marks_missing_sources(
    runtime, monkeypatch
):
    """Measured source changes update real service output and missing-source status."""
    monkeypatch.setattr(runtime, "time", lambda: 1000.0)
    service, reader = make_service(
        runtime, monkeypatch, smartshunt_suffix="ss", chain_suffixes=["a", "b"]
    )
    values = {
        "ss": {"/Dc/0/Voltage": 51.2, "/Dc/0/Current": 30.0, "/Soc": 80},
        "a": {"/Dc/0/Voltage": 51.2, "/Dc/0/Current": 10.0, "/Soc": 70},
        "b": {"/Dc/0/Voltage": 51.2, "/Dc/0/Current": 5.0, "/Soc": 90},
    }
    reader.get_value.side_effect = lambda name, path: values.get(
        name.rsplit(".", 1)[-1], {}
    ).get(path)
    service.update()
    paths = service._dbusservice
    assert paths["/Connected"] == 1
    assert paths["/Dc/0/Current"] == 15
    assert paths["/Dc/0/Voltage"] == 51.2
    assert paths["/Dc/0/Power"] == 768
    assert paths["/Soc"] == 80
    assert paths["/Capacity"] == 224
    assert paths["/ConsumedAmphours"] == 56
    assert paths["/TimeToGo"] == 13440
    assert paths["/Voltages/Cell1"] == paths["/Voltages/Cell16"] == 3.2
    assert paths["/Info/DataComplete"] == 1
    assert paths["/CustomName"] == service.product_name
    values.pop("b")
    monkeypatch.setattr(runtime, "time", lambda: 1100.0)
    service.update()
    assert paths["/System/NrOfModulesOnline"] == 2
    assert paths["/System/NrOfModulesOffline"] == 1
    assert paths["/Info/MissingSources"] == "Chain2"
    assert paths["/Dc/0/Current"] == 20
    assert "Missing: Chain2" in paths["/CustomName"]
    values.pop("ss")
    monkeypatch.setattr(runtime, "time", lambda: 1200.0)
    service.update()
    assert paths["/Connected"] == 0
    assert paths["/Dc/0/Voltage"] is None
    assert paths["/Dc/0/Current"] is None
    assert paths["/Soc"] is None


def test_update_without_chains_has_partial_status(runtime, monkeypatch):
    """A missing chain leaves unavailable derived measurements unknown."""
    monkeypatch.setattr(runtime, "time", lambda: 1000.0)
    service, reader = make_service(
        runtime, monkeypatch, smartshunt_suffix="ss", chain_suffixes=["missing"]
    )
    reader.get_value.side_effect = lambda name, path: (
        {"/Dc/0/Voltage": 50, "/Dc/0/Current": 4}.get(path)
        if name.endswith(".ss")
        else None
    )
    service.update()
    assert service._dbusservice["/Dc/0/Current"] == 4
    assert service._dbusservice["/Dc/0/Voltage"] is None
    assert service._dbusservice["/Capacity"] is None
    assert service._dbusservice["/TimeToGo"] is None


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        [
            "--smartshunt",
            "ttyUSB9",
            "--chains",
            "a",
            "b",
            "--smartshunt-index",
            "2",
            "--capacity",
            "400",
        ],
    ],
)
def test_main_wires_options_and_polling(runtime, monkeypatch, arguments):
    """The CLI forwards selection/capacity and wires the service into the main loop."""
    monkeypatch.setattr(runtime.sys, "argv", ["dbus-virtual-battery.py", *arguments])
    monkeypatch.setattr(runtime, "sleep", Mock())
    factory = Mock()
    monkeypatch.setattr(runtime, "VirtualBatteryService", factory)
    runtime.main()
    options = factory.call_args.kwargs
    assert options["smartshunt_index"] == (2 if arguments else 0)
    assert options["chain_capacity"] == (400 if arguments else 280)
    assert options["smartshunt_suffix"] == ("ttyUSB9" if arguments else None)
    assert options["chain_suffixes"] == (["a", "b"] if arguments else None)
    runtime.register_signal_handlers.assert_called_once_with(
        runtime.setup_main_loop.return_value
    )
    runtime.create_poll_function.assert_called_once_with(factory.return_value)
    runtime.run_main_loop.assert_called_once_with(
        runtime.setup_main_loop.return_value,
        runtime.POLL_INTERVAL_MS,
        runtime.create_poll_function.return_value,
    )
