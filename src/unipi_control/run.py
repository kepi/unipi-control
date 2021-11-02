#!/usr/bin/env python3
import argparse
import asyncio
import shutil
import signal
import subprocess
import sys
import uuid
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Optional

from asyncio_mqtt import Client as MqttClient
from asyncio_mqtt import MqttError
from config import config
from config import HardwareException
from config import logger
from covers import CoverMap
from modbus import Modbus
from modbus import ModbusException
from neuron import Neuron
from plugins.covers import CoversMqttPlugin
from plugins.devices import DevicesMqttPlugin
from plugins.hass.binary_sensors import HassBinarySensorsMqttPlugin
from plugins.hass.covers import HassCoversMqttPlugin
from plugins.hass.switches import HassSwitchesMqttPlugin
from termcolor import colored


class UnipiControl:
    def __init__(self, loop, modbus):
        self.neuron = Neuron(modbus)
        self.covers: Optional[CoverMap] = None

        self._mqtt_client_id: str = f"""{config.device_name.lower()}-{uuid.uuid4()}"""
        logger.info(f"[MQTT] Client ID: {self._mqtt_client_id}")

        self._tasks = None
        self._retry_reconnect: int = 0

    async def _init_tasks(self) -> None:
        async with AsyncExitStack() as stack:
            self._tasks = set()

            stack.push_async_callback(self.cancel_tasks)

            mqtt_client = MqttClient(
                config.mqtt.host,
                config.mqtt.port,
                client_id=self._mqtt_client_id,
                keepalive=config.mqtt.keepalive,
            )

            await stack.enter_async_context(mqtt_client)
            self._retry_reconnect = 0

            logger.info(f"""[MQTT] Connected to broker at `{config.mqtt.host}:{config.mqtt.port}`""")

            tasks = await DevicesMqttPlugin(self, mqtt_client).init_task(stack)
            self._tasks.update(tasks)

            tasks = await CoversMqttPlugin(self, mqtt_client).init_task(stack)
            self._tasks.update(tasks)

            if config.homeassistant.enabled:
                tasks = await HassBinarySensorsMqttPlugin(self, mqtt_client).init_task(stack)
                self._tasks.update(tasks)

                tasks = await HassCoversMqttPlugin(self, mqtt_client).init_task(stack)
                self._tasks.update(tasks)

                tasks = await HassSwitchesMqttPlugin(self, mqtt_client).init_task(stack)
                self._tasks.update(tasks)

            await asyncio.gather(*self._tasks)

    async def cancel_tasks(self):
        tasks = [t for t in self._tasks if not t.done()]
        [task.cancel() for task in tasks]

        if tasks:
            logger.info(f"Cancelling {len(tasks)} outstanding tasks.")

        await asyncio.gather(*tasks)

    async def shutdown(self, loop, signal=None):
        if signal:
            logger.info(f"Received exit signal {signal.name}...")

        tasks = [t for t in asyncio.all_tasks() if t is not (t.done() or asyncio.current_task())]
        [task.cancel() for task in tasks]

        logger.info(f"Cancelling {len(tasks)} outstanding tasks.")

        await asyncio.gather(*tasks)

    async def run(self) -> None:
        await self.neuron.initialise_cache()
        await self.neuron.read_boards()

        self.covers = CoverMap(devices=self.neuron.devices)

        reconnect_interval: int = config.mqtt.reconnect_interval
        retry_limit: Optional[int] = config.mqtt.retry_limit

        while True:
            try:
                logger.info("[MQTT] Connecting to broker ...")
                await self._init_tasks()
            except MqttError as error:
                logger.error(f"""[MQTT] Error `{error}`. Connecting attempt #{self._retry_reconnect + 1}. Reconnecting in {reconnect_interval} seconds.""")
            finally:
                if retry_limit and self._retry_reconnect > retry_limit:
                    sys.exit(1)

                self._retry_reconnect += 1

                await asyncio.sleep(reconnect_interval)


def install() -> None:
    src_config_path: str = Path(__file__).parents[1].joinpath("etc/unipi")
    src_systemd_path: str = Path(__file__).parents[1].joinpath("lib/systemd/system/unipi-control.service")
    dest_config_path: str = Path("/etc/unipi")

    print(colored(f"-> Copy config files to {dest_config_path}", "green"))

    dirs_exist_ok: bool = False
    copy_config_files: bool = True

    if dest_config_path.exists():
        overwrite_config: str = input("Overwrite existing config files? [Y/n]")

        if overwrite_config.lower() == "y":
            dirs_exist_ok = True
        else:
            copy_config_files = False

    if copy_config_files:
        shutil.copytree(src_config_path, dest_config_path, dirs_exist_ok=dirs_exist_ok)

    print(colored("-> Copy systemd service \"unipi-control.service\"", "green"))
    shutil.copyfile(src_systemd_path, "/lib/systemd/system/unipi-control.service")

    enable_and_start_systemd: str = input("Enable and start systemd service? [Y/n]")

    if enable_and_start_systemd.lower() == "y":
        print(colored("-> Enable systemd service \"unipi-control.service\"", "green"))
        status = subprocess.check_output("systemctl enable --now unipi-control", shell=True)
        logger.info(status)
    else:
        print(colored("\nYou can enable the systemd service with the command:", "white", attrs=["bold", ]))
        print(colored("systemctl enable --now unipi-control", "magenta", attrs=["bold", ]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="Control Unipi I/O with MQTT commands")

    parser.add_argument("-i", "--install", action="store_true", help="install Unipi Control")
    args = parser.parse_args()

    if args.install:
        install()
    else:
        loop = asyncio.new_event_loop()

        try:
            modbus = Modbus(loop)
            uc = UnipiControl(loop, modbus)

            signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)

            for s in signals:
                loop.add_signal_handler(
                    s, lambda s=s: asyncio.create_task(uc.shutdown(loop, s))
                )

            loop.run_until_complete(uc.run())
        except asyncio.exceptions.CancelledError:
            pass
        except HardwareException as error:
            logger.error(error)
            print(colored(error, "red"))
        except ModbusException as error:
            logger.error(f"[MODBUS] {error}")
        finally:
            # loop.close()
            logger.info("Successfully shutdown the Unipi Control service.")


if __name__ == "__main__":
    main()