"""Initialize Unipi Extension features."""

from unipi_control.features.map import FeatureMap
from unipi_control.config import Config, LogPrefix, UNIPI_LOGGER
from typing import TYPE_CHECKING, Optional

from unipi_control.helpers.typing import HardwareDefinition, ModbusClient, ModbusReadData
from unipi_control.modbus import ModbusCacheData, check_modbus_call
from unipi_control.unipi_board import UnipiBoard, UnipiBoardConfig

if TYPE_CHECKING:
    from pymodbus.pdu import ModbusResponse


class UnipiExtension:
    def __init__(
        self,
        config: Config,
        modbus_client: ModbusClient,
        modbus_cache_data: ModbusCacheData,
        definition: HardwareDefinition,
        features: FeatureMap,
    ) -> None:
        """Initialize Eastron SDM120M electricity meter."""
        self.config: Config = config
        self.modbus_client: ModbusClient = modbus_client
        self.modbus_cache_data: ModbusCacheData = modbus_cache_data
        self.definition: HardwareDefinition = definition
        self.features: FeatureMap = features
        self._sw_version: Optional[str] = None

    async def init(self) -> None:
        """Initialize internal and external hardware."""
        UNIPI_LOGGER.debug(
            "%s initializing features for extension %s %s",
            LogPrefix.CONFIG,
            self.definition.manufacturer,
            self.definition.model,
        )

        await self.read_board()

        UNIPI_LOGGER.info("%s %s extension features initialized.", LogPrefix.CONFIG, len(self.features))

    async def read_board(self) -> None:
        """Scan Modbus serial and initialize the extension."""
        UNIPI_LOGGER.info("%s Reading extension board", LogPrefix.MODBUS)

        data: ModbusReadData = {
            "address": 1000,
            "count": 1,
            "slave": self.definition.unit,
        }

        response: Optional[ModbusResponse] = await check_modbus_call(
            self.modbus_client.serial.read_input_registers, data
        )

        if response:
            firmware = UnipiBoard.get_firmware(response)
            UNIPI_LOGGER.info("%s Found firmware %s", LogPrefix.MODBUS, firmware)

            board = UnipiBoard(
                config=self.config,
                modbus_client=self.modbus_client,
                definition=self.definition,
                modbus_cache_data=self.modbus_cache_data,
                features=self.features,
                board_config=UnipiBoardConfig(
                    firmware=firmware,
                    major_group=1,
                ),
            )

            board.parse_features()
        else:
            UNIPI_LOGGER.info("%s No extension board on SPI %s", LogPrefix.MODBUS, self.definition.unit)
