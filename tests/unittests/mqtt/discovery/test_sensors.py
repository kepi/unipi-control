import asyncio
from asyncio import Task
from contextlib import AsyncExitStack
from typing import Iterator
from typing import List
from typing import Set
from unittest.mock import AsyncMock

import pytest
from _pytest.logging import LogCaptureFixture  # pylint: disable=import-private-name
from asyncio_mqtt import Client

from unipi_control.modbus import ModbusClient
from unipi_control.mqtt.discovery.sensors import HassSensorsDiscovery
from unipi_control.mqtt.discovery.sensors import HassSensorsMqttPlugin
from unipi_control.neuron import Neuron
from unittests.conftest import ConfigLoader
from unittests.conftest_data import CONFIG_CONTENT
from unittests.conftest_data import EXTENSION_HARDWARE_DATA_CONTENT
from unittests.conftest_data import HARDWARE_DATA_CONTENT
from unittests.mqtt.discovery.test_sensors_data import discovery_message_expected


class TestHappyPathHassSensorsMqttPlugin:
    @pytest.mark.parametrize(
        "_config_loader", [(CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT)], indirect=True
    )
    def test_init_tasks(
        self,
        _modbus_client: ModbusClient,
        _config_loader: ConfigLoader,
        _neuron: Neuron,
        caplog: LogCaptureFixture,
    ) -> None:
        async def run() -> None:
            mock_mqtt_client: AsyncMock = AsyncMock(spec=Client)
            plugin: HassSensorsMqttPlugin = HassSensorsMqttPlugin(neuron=_neuron, mqtt_client=mock_mqtt_client)

            async with AsyncExitStack() as stack:
                tasks: Set[Task] = set()

                await stack.enter_async_context(mock_mqtt_client)
                await plugin.init_tasks(tasks)
                await asyncio.gather(*tasks)

                for task in tasks:
                    assert task.done() is True

            logs: list = [record.getMessage() for record in caplog.records]

            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_voltage_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Voltage", "unique_id": "mocked_unipi_voltage_1", "state_topic": "mocked_unipi/meter/voltage_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "voltage", "state_class": "measurement", "unit_of_measurement": "V"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_current_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Current", "unique_id": "mocked_unipi_current_1", "state_topic": "mocked_unipi/meter/current_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_active_power_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Active Power", "unique_id": "mocked_unipi_active_power_1", "state_topic": "mocked_unipi/meter/active_power_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_mocked_id_apparent_power/config] Publishing message: {"name": "MOCKED_FRIENDLY_NAME - APPARENT_POWER", "unique_id": "mocked_unipi_mocked_id_apparent_power", "state_topic": "mocked_unipi/meter/apparent_power_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - MOCKED AREA 3", "identifiers": "MOCKED Eastron SDM120M - MOCKED AREA 3", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "MOCKED AREA 3", "via_device": "MOCKED UNIPI"}, "object_id": "mocked_id_apparent_power", "icon": "mdi:power-standby", "device_class": "apparent_power", "state_class": "measurement", "unit_of_measurement": "VA"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_reactive_power_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Reactive Power", "unique_id": "mocked_unipi_reactive_power_1", "state_topic": "mocked_unipi/meter/reactive_power_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "reactive_power", "state_class": "measurement", "unit_of_measurement": "var"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_power_factor_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Power Factor", "unique_id": "mocked_unipi_power_factor_1", "state_topic": "mocked_unipi/meter/power_factor_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power_factor", "state_class": "measurement"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_phase_angle_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Phase Angle", "unique_id": "mocked_unipi_phase_angle_1", "state_topic": "mocked_unipi/meter/phase_angle_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "state_class": "measurement"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_frequency_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Frequency", "unique_id": "mocked_unipi_frequency_1", "state_topic": "mocked_unipi/meter/frequency_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "frequency", "state_class": "measurement", "unit_of_measurement": "Hz"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_import_active_energy_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Import Active Energy", "unique_id": "mocked_unipi_import_active_energy_1", "state_topic": "mocked_unipi/meter/import_active_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "energy", "state_class": "total", "unit_of_measurement": "kWh"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_export_active_energy_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Export Active Energy", "unique_id": "mocked_unipi_export_active_energy_1", "state_topic": "mocked_unipi/meter/export_active_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "energy", "state_class": "measurement", "unit_of_measurement": "kWh"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_import_reactive_energy_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Import Reactive Energy", "unique_id": "mocked_unipi_import_reactive_energy_1", "state_topic": "mocked_unipi/meter/import_reactive_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "state_class": "total", "unit_of_measurement": "kvarh"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_export_reactive_energy_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Export Reactive Energy", "unique_id": "mocked_unipi_export_reactive_energy_1", "state_topic": "mocked_unipi/meter/export_reactive_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "state_class": "total", "unit_of_measurement": "kvarh"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_total_system_power_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Total System Power Demand", "unique_id": "mocked_unipi_total_system_power_demand_1", "state_topic": "mocked_unipi/meter/total_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_maximum_total_system_power_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Maximum Total System Power Demand", "unique_id": "mocked_unipi_maximum_total_system_power_demand_1", "state_topic": "mocked_unipi/meter/maximum_total_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "total", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_import_system_power_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Import System Power Demand", "unique_id": "mocked_unipi_import_system_power_demand_1", "state_topic": "mocked_unipi/meter/import_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_maximum_import_system_power_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Maximum Import System Power Demand", "unique_id": "mocked_unipi_maximum_import_system_power_demand_1", "state_topic": "mocked_unipi/meter/maximum_import_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_export_system_power_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Export System Power Demand", "unique_id": "mocked_unipi_export_system_power_demand_1", "state_topic": "mocked_unipi/meter/export_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_maximum_export_system_power_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Maximum Export System Power Demand", "unique_id": "mocked_unipi_maximum_export_system_power_demand_1", "state_topic": "mocked_unipi/meter/maximum_export_system_power_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "power", "state_class": "measurement", "unit_of_measurement": "W"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_current_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Current Demand", "unique_id": "mocked_unipi_current_demand_1", "state_topic": "mocked_unipi/meter/current_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_maximum_current_demand_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Maximum Current Demand", "unique_id": "mocked_unipi_maximum_current_demand_1", "state_topic": "mocked_unipi/meter/maximum_current_demand_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "current", "state_class": "measurement", "unit_of_measurement": "A"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_total_active_energy_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Total Active Energy", "unique_id": "mocked_unipi_total_active_energy_1", "state_topic": "mocked_unipi/meter/total_active_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "device_class": "energy", "state_class": "total", "unit_of_measurement": "kWh"}'
                in logs
            )
            assert (
                '[MQTT] [homeassistant/sensor/mocked_unipi_total_reactive_energy_1/config] Publishing message: {"name": "MOCKED Eastron SDM120M - Workspace: Total Reactive Energy", "unique_id": "mocked_unipi_total_reactive_energy_1", "state_topic": "mocked_unipi/meter/total_reactive_energy_1/get", "qos": 2, "force_update": true, "device": {"name": "MOCKED Eastron SDM120M - Workspace", "identifiers": "MOCKED Eastron SDM120M - Workspace", "model": "SDM120M", "sw_version": "202.04", "manufacturer": "Eastron", "suggested_area": "Workspace", "via_device": "MOCKED UNIPI"}, "state_class": "total", "unit_of_measurement": "kvarh"}'
                in logs
            )

        loop = asyncio.new_event_loop()
        loop.run_until_complete(run())

    @pytest.mark.parametrize(
        "_config_loader, expected",
        [
            (
                (CONFIG_CONTENT, HARDWARE_DATA_CONTENT, EXTENSION_HARDWARE_DATA_CONTENT),
                discovery_message_expected,
            ),
        ],
        indirect=["_config_loader"],
    )
    def test_discovery_message(
        self,
        _modbus_client: ModbusClient,
        _config_loader: ConfigLoader,
        _neuron: Neuron,
        expected: List[dict],
    ) -> None:
        mock_mqtt_client: AsyncMock = AsyncMock(spec=Client)
        plugin: HassSensorsMqttPlugin = HassSensorsMqttPlugin(neuron=_neuron, mqtt_client=mock_mqtt_client)
        features: Iterator = _neuron.features.by_feature_types(HassSensorsDiscovery.publish_feature_types)

        for index, feature in enumerate(features):
            topic, message = plugin._hass._get_discovery(feature)  # pylint: disable=protected-access

            assert message == expected[index]["message"]
            assert topic == expected[index]["topic"]