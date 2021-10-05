import itertools
import re
from dataclasses import dataclass
from typing import Optional
from typing import Union

from config import config
from helpers import MutableMappingMixin


class DeviceMap(MutableMappingMixin):
    def register(self, device):
        if not self.mapping.get(device.type):
            self.mapping[device.type] = []

        self.mapping[device.type].append(device)

    def by_name(self, device_type: Union[str, list]) -> list:
        if isinstance(device_type, str):
            return self.mapping[device_type]
        elif isinstance(device_type, list):
            return list(
                itertools.chain.from_iterable(
                    map(self.mapping.get, device_type)
                )
            )


@dataclass
class Message:
    dev_name: str
    dev_type: str
    circuit: str
    value: bool
    topic: str


class FeatureMixin:
    def __init__(self, board, circuit: str, mask: Optional[int] = None, *args, **kwargs):
        self.__dict__.update(kwargs)
        self.board = board
        self.modbus = board.neuron.modbus
        self.circuit: str = circuit
        self.mask: int = mask
        self.reg_value = lambda: board.neuron.modbus_cache_map.get_register(1, self.reg, unit=0)[0]
        self._value: bool = False

    @property
    def value(self) -> int:
        return 1 if self.reg_value() & self.mask else 0

    @property
    def topic(self) -> str:
        topic: str = f"""{config.device_name.lower()}/{self.dev_name}"""

        if self.dev_type:
            topic += f"/{self.dev_type}"

        topic += f"/{self.circuit}"

        return topic

    @property
    def circuit_name(self) -> str:
        m = re.match(r"^[a-z]+_(\d{1})_(\d{2})$", self.circuit)
        return f"""{self.name} {m.group(1)}.{m.group(2).lstrip("0")}"""

    @property
    def changed(self) -> bool:
        value: bool = self.value == True  # noqa
        changed: bool = value != self._value

        if changed:
            self._value = value

        return changed

    @property
    def message(self) -> Message:
        return Message(
            self.dev_name,
            self.dev_type,
            self.circuit,
            self.value,
            f"{self.topic}/get",
        )


class Relay(FeatureMixin):
    name = "Relay"
    dev_name = "relay"
    dev_type = "physical"

    async def set_state(self, value: int) -> None:
        await self.modbus.write_coil(self.coil, value, unit=0)


class DigitalOutput(FeatureMixin):
    name = "Digital Output"
    dev_name = "relay"
    dev_type = "digital"

    async def set_state(self, value: int) -> None:
        await self.modbus.write_coil(self.coil, value, unit=0)


class DigitalInput(FeatureMixin):
    name = "Digital Input"
    dev_name = "input"
    dev_type = "digital"


class AnalogOutput(FeatureMixin):
    name = "Analog Output"
    dev_name = "output"
    dev_type = "analog"

    def __init__(self, board, circuit: str, mask: Optional[int] = None, *args, **kwargs):
        super().__init__(board, circuit, mask, *args, **kwargs)
        self.ai_config = board.neuron.modbus_cache_map.get_register(1, self.cal_reg, unit=0)
        self.ai_voltage_deviation = board.neuron.modbus_cache_map.get_register(1, self.cal_reg + 1, unit=0)
        self.ai_voltage_offset = board.neuron.modbus_cache_map.get_register(1, self.cal_reg + 2, unit=0)

    def _uint16_to_int(self, inp):
        if inp > 0x8000:
            return (inp - 0x10000)

        return inp

    @property
    def offset(self) -> float:
        _offset: float = 0

        if self.cal_reg > 0:
            _offset = self._uint16_to_int(self.ai_voltage_deviation[0]) / 10000.0

        return _offset

    @property
    def is_voltage(self) -> bool:
        _is_voltage: bool = True

        if self.circuit == "ao_1_01" and self.cal_reg >= 0:
            _is_voltage = self.ai_config == 0

        return _is_voltage

    @property
    def mode(self) -> str:
        _mode: str = "Resistance"

        if self.is_voltage:
            _mode: str = "Voltage"
        elif self.ai_config[0] == 1:
            _mode = "Current"

        return _mode

    @property
    def factor(self) -> float:
        _factor: float = self.board.volt_ref / 4095 * (1 / 10000.0)

        if self.circuit == "ao_1_01":
            _factor = self.board.volt_ref / 4095 * (1 + self._uint16_to_int(self.ai_voltage_deviation[0]) / 10000.0)

        if self.is_voltage:
            _factor *= 3
        else:
            _factor *= 10

        return _factor

    @property
    def factorx(self) -> float:
        _factorx: float = self.board.volt_refx / 4095 * (1 / 10000.0)

        if self.circuit == "ao_1_01":
            _factorx = self.board.volt_refx / 4095 * (1 + self._uint16_to_int(self.ai_config[0]) / 10000.0)

        if self.is_voltage:
            _factorx *= 3
        else:
            _factorx *= 10

        return _factorx

    @property
    def changed(self) -> bool:
        value: bool = self.value == True  # noqa
        changed: bool = value != self._value

        if changed:
            self._value = value

        return changed

    @property
    def value(self) -> int:
        _value = self.reg_value() * 0.0025

        if self.circuit == "ao_1_01":
            _value = self.reg_value() * self.factor + self.offset

        return _value

    async def set_state(self, value: int) -> None:
        valuei: int = int(float(value) / 0.0025)

        if self.circuit == "ao_1_01":
            valuei = int((float(value) - self.offset) / self.factor)

        if valuei < 0:
            valuei = 0
        elif valuei > 4095:
            valuei = 4095

        print(self.reg_value(), valuei)

        await self.modbus.write_register(self.cal_reg, valuei, unit=0)


class AnalogInput(FeatureMixin):
    name = "Analog Input"
    dev_name = "input"
    dev_type = "analog"


class Led(FeatureMixin):
    name = "LED"
    dev_name = "led"
    dev_type = None

    async def set_state(self, value: int) -> None:
        await self.modbus.write_coil(self.coil, value, unit=0)


devices = DeviceMap()
