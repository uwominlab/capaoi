#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test relay hardware functionality using the RelayController class.
"""

import logging
import time
import unittest

import usb.core
import usb.util
from usb.core import Device

from src.params import (
    RELAY_1, RELAY_2, RELAY_3, RELAY_4,
    RELAY_OFF, RELAY_ON, VENDOR_ID, PRODUCT_ID)

# Logging configuration block
from src.relay_controller import RELAY_DEBUG
logging.basicConfig(
    level=logging.DEBUG if RELAY_DEBUG else logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class TestRelayHardware(unittest.TestCase):
    """
    TestRelayController class to test the RelayController class functionality.
    Args:
        unittest: Super class for unit testing.
    """

    def test_turn_on_and_off_relay(self):
        """
        Turn on each relay.
        """
        dev: Device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if dev is None:
            raise ValueError('Device not found')

        logging.debug("Device found: %s", dev)

        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_ON, RELAY_1, 1])
        logging.debug("Relay turned ON")
        time.sleep(3)
        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_OFF, RELAY_1, 1])
        logging.debug("Relay turned OFF")

        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_ON, RELAY_2, 1])
        logging.debug("Relay turned ON")
        time.sleep(3)
        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_OFF, RELAY_2, 1])
        logging.debug("Relay turned OFF")

        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_ON, RELAY_3, 1])
        logging.debug("Relay turned ON")
        time.sleep(3)
        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_OFF, RELAY_3, 1])
        logging.debug("Relay turned OFF")

        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_ON, RELAY_4, 1])
        logging.debug("Relay turned ON")
        time.sleep(3)
        dev.ctrl_transfer(bmRequestType=0x21, bRequest=9, wValue=0x200,
                          wIndex=0, data_or_wLength=[RELAY_OFF, RELAY_4, 1])
        logging.debug("Relay turned OFF")

        usb.util.release_interface(dev, 0)
        usb.util.dispose_resources(dev)
        logging.debug("Exiting...")


if __name__ == "__main__":
    unittest.main()
