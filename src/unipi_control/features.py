import itertools
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from config import config
from config import logger
from helpers import DataStorage


class FeatureMap(DataStorage):
    def register(self, feature) -> None:
        if not self.data.get(feature.type):
            self.data[feature.type] = []

        self.data[feature.type].append(feature)

    def by_circuit(self, circuit: str):
        feature = None

        try:
            feature = next(
                filter(
                    lambda d: d.circuit == circuit,
                    itertools.chain.from_iterable(self.data.values())
                )
            )
        except StopIteration:
            logger.error(
                "[CONFIG] `%s` not found in %s!",
                (circuit,
                 self.__class__.__name__)
            )

        return feature

    def by_feature_type(self, feature_type: list) -> Iterator:
        return itertools.chain.from_iterable(
            filter(None,
                   map(self.data.get,
                       feature_type))
        )


@dataclass(frozen=True)
class FeatureState:
    ON: str = "ON"
    OFF: str = "OFF"


class Feature:
    def __init__(
        self,
        board,
        circuit: str,
        mask: Optional[int] = None,
        *args,
        **kwargs
    ):
        self.major_group = kwargs.get("major_group")
        self.type = kwargs.get("type")
        self.coil = kwargs.get("coil")
        self.cal_reg = kwargs.get("cal_reg")
        self.reg = kwargs.get("reg")

        self.board = board
        self.modbus = board.neuron.modbus
        self.circuit: str = circuit
        self.mask: int = mask

        self.reg_value = lambda: board.neuron.modbus_cache_map.get_register(
            address=1,
            index=self.reg
        )[0]

        self._value: bool = False

    @property
    def value(self) -> int:
        return 1 if self.reg_value() & self.mask else 0

    @property
    def topic(self) -> str:
        topic: str = f"{config.device_name.lower()}/{self.feature_name}"

        if self.feature_type:
            topic += f"/{self.feature_type}"

        topic += f"/{self.circuit}"

        return topic

    @property
    def circuit_name(self) -> str:
        m = re.match(r"^[a-z]+_(\d)_(\d{2})$", self.circuit)
        return f"{self.name} {m.group(1)}.{m.group(2)}"

    @property
    def changed(self) -> bool:
        value: bool = self.value == True  # noqa
        changed: bool = value != self._value

        if changed:
            self._value = value

        return changed

    @property
    def state(self) -> str:
        return FeatureState.ON if self.value == 1 else FeatureState.OFF

    def __repr__(self):
        return self.circuit_name


class Relay(Feature):
    name = "Relay"
    feature_name = "relay"
    feature_type = "physical"

    async def set_state(self, value: int):
        return await self.modbus.write_coil(self.coil, value, unit=0)


class DigitalOutput(Feature):
    name = "Digital Output"
    feature_name = "relay"
    feature_type = "digital"

    async def set_state(self, value: int):
        return await self.modbus.write_coil(self.coil, value, unit=0)


class DigitalInput(Feature):
    name = "Digital Input"
    feature_name = "input"
    feature_type = "digital"


class AnalogOutput(Feature):
    name = "Analog Output"
    feature_name = "output"
    feature_type = "analog"

    def __init__(
        self,
        board,
        circuit: str,
        mask: Optional[int] = None,
        *args,
        **kwargs
    ):
        super().__init__(board, circuit, mask, *args, **kwargs)

        self.ai_config = board.neuron.modbus_cache_map.get_register(
            address=1,
            index=self.cal_reg
        )

        self.ai_voltage_deviation = board.neuron.modbus_cache_map.get_register(
            address=1,
            index=self.cal_reg + 1
        )

        self.ai_voltage_offset = board.neuron.modbus_cache_map.get_register(
            address=1,
            index=self.cal_reg + 2
        )

    @staticmethod
    def _uint16_to_int(inp):
        if inp > 0x8000:
            return inp - 0x10000

        return inp

    @property
    def offset(self) -> float:
        _offset: float = 0

        if self.cal_reg > 0:
            _offset = self._uint16_to_int(
                self.ai_voltage_deviation[0]
            ) / 10000.0

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
            _factor = self.board.volt_ref / 4095 * (
                1 + self._uint16_to_int(self.ai_voltage_deviation[0]) / 10000.0
            )

        if self.is_voltage:
            _factor *= 3
        else:
            _factor *= 10

        return _factor

    @property
    def factor_x(self) -> float:
        _factor_x: float = self.board.volt_ref_x / 4095 * (1 / 10000.0)

        if self.circuit == "ao_1_01":
            _factor_x = self.board.volt_ref_x / 4095 * (
                1 + self._uint16_to_int(self.ai_config[0]) / 10000.0
            )

        if self.is_voltage:
            _factor_x *= 3
        else:
            _factor_x *= 10

        return _factor_x

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
        value_i: int = int(float(value) / 0.0025)

        if self.circuit == "ao_1_01":
            value_i = int((float(value) - self.offset) / self.factor)

        if value_i < 0:
            value_i = 0
        elif value_i > 4095:
            value_i = 4095

        await self.modbus.write_register(self.cal_reg, value_i, unit=0)


class AnalogInput(Feature):
    name = "Analog Input"
    feature_name = "input"
    feature_type = "analog"


class Led(Feature):
    name = "LED"
    feature_name = "led"
    feature_type = None

    async def set_state(self, value: int) -> None:
        await self.modbus.write_coil(self.coil, value, unit=0)