"""Basic class to get features from Unipi devices"""

from typing import NamedTuple, Optional

from pymodbus.pdu import ModbusResponse

from unipi_control.config import Config
from unipi_control.features.map import FeatureMap
from unipi_control.features.neuron import DigitalInput, DigitalOutput, Hardware, Led, Modbus, Relay
from unipi_control.features.utils import FeatureType
from unipi_control.helpers.typing import HardwareDefinition, ModbusClient, ModbusFeature
from unipi_control.modbus import ModbusCacheData


class UnipiBoardConfig(NamedTuple):
    major_group: Optional[int]
    firmware: Optional[str] = None


class UnipiBoard:
    """Class to parse board features and register it to the ``FeatureMap``."""

    def __init__(
        self,
        config: Config,
        modbus_client: ModbusClient,
        modbus_cache_data: ModbusCacheData,
        definition: HardwareDefinition,
        features: FeatureMap,
        board_config: UnipiBoardConfig,
    ) -> None:
        """Initialize board.

        Parameters
        ----------
        config: Config
            Dataclass with configuration settings from yaml file.
        modbus_client: ModbusClient
            Modbus named tuple with tcp and serial client.
        modbus_cache_data: ModbusCacheData
            Cached modbus registers.
        definition: HardwareDefinition
            Neuron and extension hardware definition data.
        features: FeatureMap
            Input and output features.
        board_config: UnipiBoardConfig
            Neuron board configuration e.g. major_group and firmware.

        """
        self.config: Config = config
        self.modbus_client: ModbusClient = modbus_client
        self.modbus_cache_data: ModbusCacheData = modbus_cache_data
        self.definition: HardwareDefinition = definition
        self.features: FeatureMap = features
        self.board_config: UnipiBoardConfig = board_config

    def _parse_feature_ro(self, max_count: int, modbus_feature: ModbusFeature) -> None:
        if modbus_feature["major_group"] == modbus_feature["major_group"]:
            for index in range(max_count):
                relay: Relay = Relay(
                    config=self.config,
                    modbus=Modbus(
                        client=self.modbus_client,
                        cache=self.modbus_cache_data,
                        val_reg=modbus_feature["val_reg"],
                        val_coil=modbus_feature["val_coil"],
                    ),
                    hardware=Hardware(
                        major_group=modbus_feature["major_group"],
                        feature_type=FeatureType[modbus_feature["feature_type"]],
                        feature_index=index,
                        definition=self.definition,
                        firmware=self.board_config.firmware,
                    ),
                )

                self.features.register(relay)

    def _parse_feature_di(self, max_count: int, modbus_feature: ModbusFeature) -> None:
        if modbus_feature["major_group"] == modbus_feature["major_group"]:
            for index in range(max_count):
                digital_input: DigitalInput = DigitalInput(
                    config=self.config,
                    modbus=Modbus(
                        client=self.modbus_client,
                        cache=self.modbus_cache_data,
                        val_reg=modbus_feature["val_reg"],
                    ),
                    hardware=Hardware(
                        major_group=modbus_feature["major_group"],
                        feature_type=FeatureType[modbus_feature["feature_type"]],
                        feature_index=index,
                        definition=self.definition,
                        firmware=self.board_config.firmware,
                    ),
                )

                self.features.register(digital_input)

    def _parse_feature_do(self, max_count: int, modbus_feature: ModbusFeature) -> None:
        if modbus_feature["major_group"] == modbus_feature["major_group"]:
            for index in range(max_count):
                digital_output: DigitalOutput = DigitalOutput(
                    config=self.config,
                    modbus=Modbus(
                        client=self.modbus_client,
                        cache=self.modbus_cache_data,
                        val_reg=modbus_feature["val_reg"],
                        val_coil=modbus_feature["val_coil"],
                    ),
                    hardware=Hardware(
                        major_group=modbus_feature["major_group"],
                        feature_type=FeatureType[modbus_feature["feature_type"]],
                        feature_index=index,
                        definition=self.definition,
                        firmware=self.board_config.firmware,
                    ),
                )

                self.features.register(digital_output)

    def _parse_feature_led(self, max_count: int, modbus_feature: ModbusFeature) -> None:
        if modbus_feature["major_group"] == modbus_feature["major_group"]:
            for index in range(max_count):
                led: Led = Led(
                    config=self.config,
                    modbus=Modbus(
                        client=self.modbus_client,
                        cache=self.modbus_cache_data,
                        val_reg=modbus_feature["val_reg"],
                        val_coil=modbus_feature["val_coil"],
                    ),
                    hardware=Hardware(
                        major_group=modbus_feature["major_group"],
                        feature_type=FeatureType[modbus_feature["feature_type"]],
                        feature_index=index,
                        definition=self.definition,
                        firmware=self.board_config.firmware,
                    ),
                )

                self.features.register(led)

    def _parse_feature(self, modbus_feature: ModbusFeature) -> None:
        max_count: int = modbus_feature["count"]
        feature_type: str = modbus_feature["feature_type"].lower()

        if func := getattr(self, f"_parse_feature_{feature_type}", None):
            func(max_count, modbus_feature)

    def parse_features(self) -> None:
        """Parse features from hardware definition."""
        for modbus_feature in self.definition.modbus_features:
            self._parse_feature(modbus_feature)

    @staticmethod
    def get_firmware(response: ModbusResponse) -> str:
        """Get the Unipi Neuron firmware version.

        Parameters
        ----------
        response: ModbusResponse
            Modbus response PDU

        Returns
        -------
        str:
            Unipi Neuron firmware version

        """
        versions = getattr(response, "registers", [0, 0])
        return f"{(versions[0] & 0xff00) >> 8}.{(versions[0] & 0x00ff)}"
