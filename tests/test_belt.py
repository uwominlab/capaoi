"""
Test the Belt class.
"""

import unittest
from src.belt import Belt


class TestBelt(unittest.TestCase):
    """
    TestBelt class to test the Belt class functionality.
    Args:
        unittest: Super class for unit testing.
    """

    def test_calculate_timing_normal(self):
        """
        Test calculate_timing with non-zero processing and actuator delays.
        For a belt with rotating_speed=0.5 m/s and distance_to_actuator=1.0 m:
            travel_time = 1.0 / 0.5 = 2.0 seconds.
        With processing_delay=0.1 s and actuator_response_time=0.2 s,
            expected effective delay = 2.0 - 0.1 - 0.2 = 1.7 seconds.
        """
        belt = Belt(rotating_speed=0.5, distance_to_actuator=1.0)
        processing_delay = 0.1
        actuator_response_time = 0.2
        expected_time = 2.0 - processing_delay - actuator_response_time
        result = belt.calculate_timing(
            processing_delay, actuator_response_time)
        self.assertAlmostEqual(result, expected_time, places=5)

    def test_calculate_timing_no_delays(self):
        """
        Test calculate_timing when no additional delays are provided.
        For a belt with rotating_speed=0.5 m/s and distance_to_actuator=1.0 m:
            expected effective delay = 1.0 / 0.5 = 2.0 seconds.
        """
        belt = Belt(rotating_speed=0.5, distance_to_actuator=1.0)
        expected_time = 1.0 / 0.5  # 2.0 seconds
        result = belt.calculate_timing()
        self.assertAlmostEqual(result, expected_time, places=5)

    def test_calculate_timing_invalid_speed(self):
        """
        Test that a ValueError is raised when rotating_speed is not greater than zero.
        """
        belt = Belt(rotating_speed=0.0, distance_to_actuator=1.0)
        with self.assertRaises(ValueError):
            belt.calculate_timing()

    def test_properties(self):
        """
        Test that the rotating_speed and distance_to_actuator properties return the expected values.
        """
        rotating_speed = 0.75
        distance = 2.0
        belt = Belt(rotating_speed=rotating_speed,
                    distance_to_actuator=distance)
        self.assertEqual(belt.rotating_speed, rotating_speed)
        self.assertEqual(belt.distance_to_actuator, distance)


if __name__ == "__main__":
    unittest.main()
