import heapq
import time
from unittest.mock import MagicMock, patch
import unittest

from src.params import ACTUATOR_RETRACTION_TIME, RELAY_1


class MockRelay:
    def __init__(self):
        self.state = False

    def turn_on(self, relay_number):
        self.state = True

    def turn_off(self, relay_number):
        self.state = False


class MockMainWindow:
    def __init__(self):
        self.camera_thread = MagicMock()
        self.relay = MockRelay()
        self.actuation_timestamps = []
        self.last_actuation_time = None

    def process_actuation_timestamps(self, abs_actuation_timestamps):
        # Add new actuation timestamps to the existing list
        # self.actuation_timestamps += abs_actuation_timestamps
        # heapq.heapify(self.actuation_timestamps)
        for timestamp in abs_actuation_timestamps:
            heapq.heappush(self.actuation_timestamps, timestamp)

        current_timestamp: float = time.time()
        # Remove expired timestamps
        while self.actuation_timestamps and self.actuation_timestamps[0] < current_timestamp:
            heapq.heappop(self.actuation_timestamps)

        # if self.actuation_timestamps:
        #     earliest_timestamp: float = self.actuation_timestamps[0]
        #     latest_timestamp: float = heapq.nlargest(
        #         1, self.actuation_timestamps)[0]
        #     latest_timestamp = max(
        #         latest_timestamp, earliest_timestamp + ACTUATOR_RETRACTION_TIME)
        #     target_timestamp: float = current_timestamp + ACTUATOR_RETRACTION_TIME
        #     if earliest_timestamp <= target_timestamp:
        #         self.relay.turn_on(relay_number=RELAY_1)
        # else:
        #     self.relay.turn_off(relay_number=RELAY_1)

        # Actuate relay based on timestamp comparison
        if self.actuation_timestamps:
            earliest_timestamp = self.actuation_timestamps[0]
            current_timestamp: float = time.time()
            target_timestamp: float = current_timestamp + ACTUATOR_RETRACTION_TIME

            # If within actuation window or still within retention time, keep the relay on
            if earliest_timestamp <= target_timestamp:
                if self.last_actuation_time is None or \
                        (current_timestamp - self.last_actuation_time) >= ACTUATOR_RETRACTION_TIME:
                    self.relay.turn_on(relay_number=RELAY_1)
                    self.last_actuation_time = current_timestamp
            else:
                # Not yet the time to actuate
                # Turn off only if the last actuation period has ended
                if self.last_actuation_time and \
                        (current_timestamp - self.last_actuation_time) >= ACTUATOR_RETRACTION_TIME:
                    self.relay.turn_off(relay_number=RELAY_1)
                    self.last_actuation_time = None
        else:
            # No more valid timestamps, turn off relay if needed
            if self.last_actuation_time and \
                    (current_timestamp - self.last_actuation_time) >= ACTUATOR_RETRACTION_TIME:
                self.relay.turn_off(relay_number=RELAY_1)
                self.last_actuation_time = None


class TestProcessActuationTimestamps(unittest.TestCase):

    instance: MockMainWindow

    def setUp(self):
        self.instance = MockMainWindow()

    def test_add_timestamps(self):
        fixed_time = time.time()
        timestamps = [fixed_time + 2, fixed_time + 10]

        with patch('time.time', return_value=fixed_time):
            self.instance.process_actuation_timestamps(timestamps)

        self.assertEqual(self.instance.actuation_timestamps,
                         [fixed_time + 2, fixed_time + 10])

    def test_process_first_timestamp(self):
        fixed_time = time.time()
        timestamps = [fixed_time + 2, fixed_time + 10]

        with patch('time.time', return_value=fixed_time):
            self.instance.process_actuation_timestamps(timestamps)
        self.assertFalse(self.instance.relay.state)
        assert self.instance.last_actuation_time is None

        with patch('time.time', return_value=fixed_time + 1.9):
            self.instance.process_actuation_timestamps([])
        self.assertTrue(self.instance.relay.state)
        self.assertEqual(self.instance.last_actuation_time, fixed_time + 1.9)

        with patch('time.time', return_value=fixed_time + 3):
            self.instance.process_actuation_timestamps([])
        self.assertFalse(self.instance.relay.state)
        assert self.instance.last_actuation_time is None
        self.assertEqual(self.instance.actuation_timestamps, [fixed_time + 10])

        with patch(
            'time.time',
                return_value=fixed_time + 10 - ACTUATOR_RETRACTION_TIME + 0.001):
            self.instance.process_actuation_timestamps([])
        self.assertTrue(self.instance.relay.state)
        assert self.instance.last_actuation_time is not None
        self.assertEqual(self.instance.last_actuation_time,
                         fixed_time + 10 - ACTUATOR_RETRACTION_TIME + 0.001)

    def test_clear_all_timestamps(self):
        fixed_time = time.time()
        timestamps = [fixed_time + 2, fixed_time + 10]

        with patch('time.time', return_value=fixed_time):
            self.instance.process_actuation_timestamps(timestamps)

        # First timestamp processed
        with patch('time.time', return_value=fixed_time + 3):
            self.instance.process_actuation_timestamps([])

        # Second timestamp processed + retention period ended
        with patch('time.time', return_value=fixed_time + 10 + ACTUATOR_RETRACTION_TIME + 1):
            self.instance.process_actuation_timestamps([])

        self.assertEqual(self.instance.actuation_timestamps, [])
        self.assertFalse(self.instance.relay.state)

    def test_relay_turns_off_after_retraction(self):
        fixed_time = time.time()
        timestamps = [fixed_time + 2]

        with patch('time.time', return_value=fixed_time):
            self.instance.process_actuation_timestamps(timestamps)

        # Actuate relay
        with patch('time.time', return_value=fixed_time + 2):
            self.instance.process_actuation_timestamps([])

        # Retract relay after retraction time
        with patch('time.time', return_value=fixed_time + 2 + ACTUATOR_RETRACTION_TIME + 1):
            self.instance.process_actuation_timestamps([])

        self.assertFalse(self.instance.relay.state)

    def test_no_timestamps_no_actuation(self):
        fixed_time = time.time()

        with patch('time.time', return_value=fixed_time):
            self.instance.process_actuation_timestamps([])

        self.assertFalse(self.instance.relay.state)


if __name__ == '__main__':
    unittest.main()
