"""Read hardware to initialize neuron device."""

from unipi_control.extensions.unipi import UnipiExtension
from unipi_control.unipi_board import UnipiBoardConfig, UnipiBoard
from typing import List
from typing import Optional

from pymodbus.pdu import ModbusResponse

from unipi_control.config import Config
from unipi_control.config import HardwareMap
from unipi_control.config import HardwareType
from unipi_control.config import LogPrefix
from unipi_control.config import UNIPI_LOGGER
from unipi_control.extensions.eastron import EastronSDM120M
from unipi_control.features.map import FeatureMap
from unipi_control.helpers.typing import ModbusClient
from unipi_control.helpers.typing import ModbusReadData
from unipi_control.modbus import ModbusCacheData
from unipi_control.modbus import check_modbus_call


class Neuron:
    """Class that reads all boards and scan modbus registers from an Unipi Neuron, extensions and third-party devices.

    The Unipi Neuron has one or more boards and each board has its features (e.g. Relay, Digital Input). This class
    reads out all boards and append it to the boards ``list``.

    Attributes
    ----------
    modbus_client: ModbusClient
        A modbus tcp client.
    hardware: HardwareMap
        The Unipi Neuron hardware definitions.
    boards: list
        All available boards from the Unipi Neuron.
    features: FeatureMap
        All registered features (e.g. Relay, Digital Input, ...) from the
        Unipi Neuron.

    """

    def __init__(self, config: Config, modbus_client: ModbusClient) -> None:
        self.config: Config = config
        self.modbus_client: ModbusClient = modbus_client
        self.hardware: HardwareMap = HardwareMap(config=config)
        self.features = FeatureMap()
        self.boards: List[UnipiBoard] = []

        self.modbus_cache_data: ModbusCacheData = ModbusCacheData(
            modbus_client=self.modbus_client,
            hardware=self.hardware,
        )

    async def init(self) -> None:
        """Initialize internal and external hardware."""
        UNIPI_LOGGER.debug("%s %s hardware definition(s) found.", LogPrefix.CONFIG, len(self.hardware))

        await self.read_boards()
        await self.read_extensions()

        UNIPI_LOGGER.info("%s %s features initialized.", LogPrefix.CONFIG, len(self.features))

    async def read_boards(self) -> None:
        """Scan Modbus TCP and initialize Unipi Neuron board."""
        UNIPI_LOGGER.info("%s Reading SPI boards", LogPrefix.MODBUS)

        for index in (1, 2, 3):
            data: ModbusReadData = {
                "address": 1000,
                "count": 1,
                "slave": index,
            }

            response: Optional[ModbusResponse] = await check_modbus_call(
                self.modbus_client.tcp.read_input_registers, data
            )

            if response:
                firmware = UnipiBoard.get_firmware(response)
                UNIPI_LOGGER.info("%s Found firmware %s", LogPrefix.MODBUS, firmware)

                board = UnipiBoard(
                    config=self.config,
                    modbus_client=self.modbus_client,
                    definition=self.hardware["neuron"],
                    modbus_cache_data=self.modbus_cache_data,
                    features=self.features,
                    board_config=UnipiBoardConfig(
                        firmware=UnipiBoard.get_firmware(response),
                        major_group=index,
                    ),
                )
                board.parse_features()

                self.boards.append(board)
            else:
                UNIPI_LOGGER.info("%s No board on SPI %s", LogPrefix.MODBUS, index)

        await self.modbus_cache_data.scan("tcp", hardware_types=[HardwareType.NEURON])

    async def read_extensions(self) -> None:
        """Scan Modbus RTU and initialize extension classes."""
        UNIPI_LOGGER.info("%s Reading extensions", LogPrefix.MODBUS)

        for key, definition in self.hardware.items():
            UNIPI_LOGGER.info(
                "%s found key: %s, manufacturer: %s, model: %s",
                LogPrefix.MODBUS,
                key,
                definition.manufacturer,
                definition.model,
            )
            if (
                key != "neuron"
                and (definition.manufacturer and definition.manufacturer.lower() == "eastron")
                and (definition.model and definition.model == "SDM120M")
            ):
                await EastronSDM120M(
                    config=self.config,
                    modbus_client=self.modbus_client,
                    modbus_cache_data=self.modbus_cache_data,
                    definition=definition,
                    features=self.features,
                ).init()
            elif key != "neuron" and (definition.manufacturer and definition.manufacturer.lower() == "unipi"):
                await UnipiExtension(
                    config=self.config,
                    modbus_client=self.modbus_client,
                    modbus_cache_data=self.modbus_cache_data,
                    definition=definition,
                    features=self.features,
                ).init()

        await self.modbus_cache_data.scan("serial", hardware_types=[HardwareType.EXTENSION])
