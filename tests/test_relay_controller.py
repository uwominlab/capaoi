"""
Test cases for the RelayController class.
"""

import unittest
from unittest.mock import patch, MagicMock
import usb.core
import usb.util

from src.relay_controller import RelayController
from src.params import (
    VENDOR_ID, PRODUCT_ID, RELAY_1,
    RELAY_2, RELAY_3, RELAY_4, RELAY_ON, RELAY_OFF)


class TestRelayController(unittest.TestCase):

    @patch('src.relay_controller.usb.core.find')
    @patch('src.relay_controller.usb.util.claim_interface')
    def test_init_device_found_without_kernel_driver(self, mock_claim, mock_find):
        # Create a fake USB device
        fake_device = MagicMock()
        fake_device.is_kernel_driver_active.return_value = False
        mock_find.return_value = fake_device

        rc = RelayController(VENDOR_ID, PRODUCT_ID)
        self.assertEqual(rc.device, fake_device)
        mock_claim.assert_called_with(fake_device, 0)

    @patch('src.relay_controller.usb.core.find', return_value=None)
    def test_init_device_not_found(self, mock_find):
        with self.assertRaises(ValueError):
            RelayController(VENDOR_ID, PRODUCT_ID)

    @patch('src.relay_controller.usb.util.claim_interface')
    @patch('src.relay_controller.usb.core.find')
    def test_detach_kernel_driver(self, mock_find, mock_claim):
        fake_device = MagicMock()
        # Simulate kernel driver active
        fake_device.is_kernel_driver_active.return_value = True
        mock_find.return_value = fake_device

        rc = RelayController(VENDOR_ID, PRODUCT_ID)
        fake_device.detach_kernel_driver.assert_called_with(0)
        mock_claim.assert_called_with(fake_device, 0)

    @patch('src.relay_controller.usb.core.find')
    @patch('src.relay_controller.usb.util.claim_interface')
    def test_turn_on_and_turn_off(self, mock_claim, mock_find):
        fake_device = MagicMock()
        fake_device.is_kernel_driver_active.return_value = False
        mock_find.return_value = fake_device

        rc = RelayController(VENDOR_ID, PRODUCT_ID)

        # Test turning ON RELAY_1
        rc.turn_on(RELAY_1)
        fake_device.ctrl_transfer.assert_called_with(
            bmRequestType=0x21,
            bRequest=9,
            wValue=0x200,
            wIndex=0,
            data_or_wLength=[RELAY_ON, RELAY_1, 1]
        )
        fake_device.ctrl_transfer.reset_mock()

        # Test turning OFF RELAY_1
        rc.turn_off(RELAY_1)
        fake_device.ctrl_transfer.assert_called_with(
            bmRequestType=0x21,
            bRequest=9,
            wValue=0x200,
            wIndex=0,
            data_or_wLength=[RELAY_OFF, RELAY_1, 1]
        )

    @patch('src.relay_controller.usb.util.dispose_resources')
    @patch('src.relay_controller.usb.util.release_interface')
    @patch('src.relay_controller.usb.core.find')
    @patch('src.relay_controller.usb.util.claim_interface')
    def test_release(self, mock_claim, mock_find, mock_release, mock_dispose):
        fake_device = MagicMock()
        fake_device.is_kernel_driver_active.return_value = False
        mock_find.return_value = fake_device

        rc = RelayController(VENDOR_ID, PRODUCT_ID)
        rc.release()
        mock_release.assert_called_with(fake_device, 0)
        mock_dispose.assert_called_with(fake_device)

    def test_multiple_relays(self):
        """
        Test turning on and off multiple relays in sequence.
        """
        with patch('src.relay_controller.usb.core.find') as mock_find, \
                patch('src.relay_controller.usb.util.claim_interface'), \
                patch('src.relay_controller.usb.util.release_interface'), \
                patch('src.relay_controller.usb.util.dispose_resources'):

            fake_device = MagicMock()
            fake_device.is_kernel_driver_active.return_value = False
            mock_find.return_value = fake_device

            rc = RelayController(VENDOR_ID, PRODUCT_ID)
            # Turn on all relays sequentially
            for relay in [RELAY_1, RELAY_2, RELAY_3, RELAY_4]:
                rc.turn_on(relay)
            # Ensure ctrl_transfer was called the proper number of times for ON commands
            self.assertEqual(fake_device.ctrl_transfer.call_count, 4)

            fake_device.ctrl_transfer.reset_mock()

            # Turn off all relays sequentially
            for relay in [RELAY_1, RELAY_2, RELAY_3, RELAY_4]:
                rc.turn_off(relay)
            self.assertEqual(fake_device.ctrl_transfer.call_count, 4)


if __name__ == "__main__":
    unittest.main()
