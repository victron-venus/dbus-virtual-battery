"""Cold-start membership and measurement freshness without live D-Bus."""

import pytest

from tests.test_runtime import make_service


def reading(current=0, **extra):
    return {
        "/Connected": 1,
        "/Dc/0/Voltage": 52,
        "/Dc/0/Current": current,
        "/Soc": 70,
        **extra,
    }


def attach(reader, values):
    reader.get_value.side_effect = lambda name, path: values.get(
        name.rsplit(".", 1)[-1], {}
    ).get(path)
    reader.get_snapshot.side_effect = lambda name: values.get(name.rsplit(".", 1)[-1])


def mqtt_reading(current=0, sampled=100.0):
    return reading(
        current,
        **{
            "/Info/DataComplete": 1,
            "/Info/LastMeasurementMonotonic": sampled,
            "/Info/DataTimeout": 60,
        },
    )


def test_legacy_helper_cannot_register_connected_without_samples(runtime, monkeypatch):
    helper = runtime.setup_dbus_paths_common

    def legacy(service, **kwargs):
        helper(service, **kwargs)
        service["/Connected"] = 1

    monkeypatch.setattr(runtime, "setup_dbus_paths_common", legacy)
    service, _ = make_service(runtime, monkeypatch)
    assert service._dbusservice["/Connected"] == 0
    assert service._dbusservice["/Capacity"] is None
    assert service._dbusservice["/Io/AllowToDischarge"] is None


def test_delayed_sources_recover_without_partial_subtraction_or_wrong_shunt(
    runtime, monkeypatch
):
    clock = [100.0]
    monkeypatch.setattr(runtime, "monotonic", lambda: clock[0])
    service, reader = make_service(
        runtime, monkeypatch, discovered=["mqtt_chain1", "parallel_bms"]
    )
    values = {"mqtt_chain1": mqtt_reading(5), "parallel_bms": reading(100)}
    attach(reader, values)
    service.update()
    assert service.smartshunt.service == ""
    assert service._dbusservice["/Connected"] == 0
    assert len(service.chains) == 2
    values["ttyUSB0"] = reading(20)
    reader.list_battery_services.return_value = list(values)
    clock[0] += 5
    service.update()
    assert service.smartshunt.service.endswith(".ttyUSB0")
    assert service._dbusservice["/Connected"] == 0
    assert service._dbusservice["/Dc/0/Current"] is None
    values["mqtt_chain2"] = mqtt_reading(3)
    service.update()
    assert service._dbusservice["/Connected"] == 1
    assert service._dbusservice["/Dc/0/Current"] == 12
    values.pop("mqtt_chain1")
    reader.list_battery_services.return_value = list(values)
    clock[0] += 100
    service.update()
    assert len(service.chains) == 2
    assert service._dbusservice["/Connected"] == 0
    values["mqtt_chain1"] = mqtt_reading(5, sampled=clock[0])
    values["mqtt_chain2"] = mqtt_reading(3, sampled=clock[0])
    service.update()
    assert service._dbusservice["/Dc/0/Current"] == 12


def test_selected_shunt_does_not_switch_to_another_when_disconnected(
    runtime, monkeypatch
):
    service, reader = make_service(
        runtime, monkeypatch, discovered=["ttyUSB0", "ttyUSB1"]
    )
    values = {
        "ttyUSB1": reading(99),
        "mqtt_chain1": reading(5),
        "mqtt_chain2": reading(3),
    }
    attach(reader, values)
    reader.list_battery_services.return_value = list(values)
    service.update()
    assert service.smartshunt.service.endswith(".ttyUSB0")
    assert service._dbusservice["/Connected"] == 0


@pytest.mark.parametrize(
    "age,complete,expected",
    [
        (0, 1, True),
        (59, 1, True),
        (60, 1, False),
        (61, 1, False),
        (-1, 1, False),
        (0, 0, False),
    ],
)
def test_frozen_upstream_timestamp_expires_even_when_dbus_responds(
    runtime, monkeypatch, age, complete, expected
):
    monkeypatch.setattr(runtime, "monotonic", lambda: 100.0 + age)
    service, reader = make_service(
        runtime, monkeypatch, smartshunt_suffix="ss", chain_suffixes=["chain"]
    )
    values = {
        "ss": reading(10),
        "chain": reading(
            3,
            **{
                "/Info/DataComplete": complete,
                "/Info/LastMeasurementMonotonic": 100.0,
                "/Info/DataTimeout": 60,
                "/Info/DataAge": 0,
            },
        ),
    }
    attach(reader, values)
    service.update()
    assert bool(service._dbusservice["/Connected"]) is expected
    assert service.chains[0].sample_age == (age if complete else None)
    assert (
        service.smartshunt.sample_age is None
    )  # A local read is not a sensor timestamp.


@pytest.mark.parametrize(
    "suffixes", [[], ["chain", "chain"], ["virtual_chain"], ["ss"]]
)
def test_invalid_membership_rejected(runtime, monkeypatch, suffixes):
    with pytest.raises(ValueError):
        make_service(
            runtime, monkeypatch, smartshunt_suffix="ss", chain_suffixes=suffixes
        )


def test_partial_soc_does_not_publish_an_average_of_remaining_chain(runtime):
    result = runtime.calculate_virtual_battery(
        52,
        10,
        [
            {"voltage": 52, "current": 2, "soc": 0},
            {"voltage": 52, "current": 3, "soc": None},
        ],
        280,
    )
    assert result["current"] == 5
    assert result["soc"] is None
    assert result["remaining_capacity"] is None


def test_reader_identifies_product_not_serial_port(runtime):
    bus = runtime.get_bus.return_value
    bus.get_object.return_value.GetValue.return_value = "SmartShunt 500A/50mV"
    reader = runtime.DbusReader()
    assert reader.get_product_name("ttyUSB0") == "SmartShunt 500A/50mV"
    bus.get_object.return_value.GetValue.return_value = []
    assert reader.get_product_name("ttyUSB0") is None


def test_auto_discovery_rejects_a_serial_bms(runtime, monkeypatch):
    service, reader = make_service(runtime, monkeypatch, discovered=["ttyUSB0"])
    # A ttyUSB suffix alone is insufficient; re-run an empty initial discovery.
    service.smartshunt.service = ""
    reader.get_product_name.return_value = "JBD serial BMS"
    reader.get_product_name.side_effect = None
    service._rediscover_missing_smartshunt()
    assert service.smartshunt.service == ""


def test_mqtt_requires_atomic_snapshot_and_measurement_metadata(runtime, monkeypatch):
    monkeypatch.setattr(runtime, "monotonic", lambda: 100.0)
    service, reader = make_service(
        runtime, monkeypatch, smartshunt_suffix="ss", chain_suffixes=["mqtt_chain1"]
    )
    values = {"ss": reading(10), "mqtt_chain1": reading(3)}
    attach(reader, values)
    service.update()
    assert service._dbusservice["/Connected"] == 0
    values["mqtt_chain1"] = mqtt_reading(3)
    service.update()
    assert service._dbusservice["/Dc/0/Current"] == 7
    assert service._dbusservice["/Io/AllowToCharge"] is None
    assert service._dbusservice["/Io/AllowToDischarge"] is None
    reader.get_snapshot.side_effect = lambda name: (
        values["ss"] if name.endswith(".ss") else None
    )
    service.update()
    assert service._dbusservice["/Connected"] == 0
    assert service._dbusservice["/Dc/0/Current"] is None


def test_reader_snapshot_is_one_uncached_reply(runtime):
    bus = runtime.get_bus.return_value
    bus.get_object.return_value.GetItems.side_effect = [
        {
            "/Connected": {"Value": 1},
            "/Dc/0/Voltage": {"Value": 52},
            "/Soc": {"Value": []},
            "/Dc/0/Current": {"Value": float("nan")},
            "/ProductName": {"Value": "MQTT battery"},
        },
        {"/Connected": {"Value": 0}},
    ]
    reader = runtime.DbusReader()
    assert reader.get_snapshot("battery") == {
        "/Connected": 1,
        "/Dc/0/Voltage": 52,
        "/Soc": None,
        "/Dc/0/Current": None,
        "/ProductName": None,
    }
    assert reader.get_snapshot("battery") == {"/Connected": 0}
    assert bus.get_object.return_value.GetValue.call_count == 0
    assert bus.get_object.return_value.GetItems.call_count == 2


def test_reader_snapshot_unavailable(runtime):
    from tests.fake_dbus import DBusException

    bus = runtime.get_bus.return_value
    reader = runtime.DbusReader()
    bus.get_object.return_value.GetItems.return_value = []
    assert reader.get_snapshot("battery") is None
    bus.get_object.return_value.GetItems.side_effect = DBusException("offline")
    assert reader.get_snapshot("battery") is None
    assert reader.bus is bus
    bus.get_object.return_value.GetItems.side_effect = DBusException(
        "Connection refused"
    )
    assert reader.get_snapshot("battery") is None
    assert reader.bus is None
    assert reader.get_snapshot("battery") is None
