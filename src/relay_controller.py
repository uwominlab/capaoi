#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains the RelayController class to control a USB relay board using pyusb.

Raises:
    ValueError: Device not found
"""

import logging
# pylint: disable=no-name-in-module
from PyQt6.QtCore import QSettings
import usb.core
import usb.util
from usb.core import Device
from src.params import RELAY_OFF, RELAY_ON, VENDOR_ID, PRODUCT_ID

# Logging configuration block
settings: QSettings = QSettings("MinLab", "CapAOI")
RELAY_DEBUG: bool = settings.value("relay2/debug", type=bool, defaultValue=False)
logging.basicConfig(
    level=logging.DEBUG if RELAY_DEBUG else logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class RelayController:
    """
    RelayController encapsulates operations to control a USB relay board using pyusb.

    Methods:
        __init__(vendor_id, product_id): Initializes the USB relay device.
        turn_on(relay_number, on_value): Turns on a specified relay.
        turn_off(relay_number, off_value): Turns off a specified relay.
        release(): Releases the claimed interface and disposes of device resources.
    """
    vendor_id: int
    product_id: int
    device: Device

    def __repr__(self) -> str:
        return f"RelayController(vendor_id={self.vendor_id}, product_id={self.product_id})"

    def __init__(self, vendor_id=VENDOR_ID, product_id=PRODUCT_ID) -> None:
        """
        Initialize the USB relay device.
        :param vendor_id: USB Vendor ID
        :param product_id: USB Product ID
        :raises ValueError: if device is not found.

        >>> relay_controller = RelayController(vendor_id=0x16C0, product_id=0x05DF)
        >>> relay_controller.device is not None
        True
        >>> relay_controller.release()
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)  # type: ignore
        if self.device is None:
            raise ValueError("Device not found")
        usb.util.claim_interface(self.device, 0)
        logging.debug("Interface 0 claimed.")

    def turn_on(self, relay_number, on_value=RELAY_ON) -> None:
        """
        Turn ON a specified relay.
        :param relay_number: Relay identifier (e.g., RELAY_1)
        :param on_value: Command value to turn relay ON (default is RELAY_ON)

        >>> relay_controller = RelayController()
        >>> relay_controller.turn_on(1)
        >>> relay_controller.release()
        """
        try:
            self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=9,
                wValue=0x200,
                wIndex=0,
                data_or_wLength=[on_value, relay_number, 1]
            )
            logging.debug("Relay %s turned ON (value: %s)", relay_number, on_value)
        except usb.core.USBError as e:
            logging.error("Error turning ON relay %s: %s", relay_number, e)

    def turn_off(self, relay_number, off_value=RELAY_OFF) -> None:
        """
        Turn OFF a specified relay.
        :param relay_number: Relay identifier (e.g., RELAY_1)
        :param off_value: Command value to turn relay OFF (default is RELAY_OFF)

        >>> relay_controller = RelayController()
        >>> relay_controller.turn_off(1)
        >>> relay_controller.release()
        """
        try:
            self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=9,
                wValue=0x200,
                wIndex=0,
                data_or_wLength=[off_value, relay_number, 1]
            )
            logging.debug("Relay %s turned OFF (value: %s)", relay_number, off_value)
        except usb.core.USBError as e:
            logging.error("Error turning OFF relay %s: %s", relay_number, e)

    def release(self) -> None:
        """
        Release the claimed interface and dispose of the device resources.
        """
        usb.util.release_interface(self.device, 0)
        usb.util.dispose_resources(self.device)
        logging.debug("Released interface 0 and disposed device resources.")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
