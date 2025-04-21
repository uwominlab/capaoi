#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the Belt class,
which is an abstract representation of a conveyor belt system.
t (effective_time) = d (distance_to_actuator) / v (rotating_speed) \
    - processing_delay - actuator_response_time
"""


import logging

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Belt:
    """
    A class representing a conveyor belt system.
    Provides the functionality to calculate the effective time delay
    to control the actuator based on the belt speed and other parameters.
    In this context, the actuator is a device that filters out defected capsules.
    """
    _rotating_speed: float
    _distance_to_actuator: float

    @property
    def rotating_speed(self) -> float:
        """
        Get the rotating speed of the belt.
        """
        return self._rotating_speed

    @property
    def distance_to_actuator(self) -> float:
        """
        Get the distance from the detection point to the actuator.
        """
        return self._distance_to_actuator

    def __init__(self, rotating_speed: float, distance_to_actuator: float) -> None:
        """
        Initialize the Belt with a the distance from the detection point
        to the actuator.

        Parameters:
            rotating_speed (float): Speed of the belt rotation in meters per second.
            distance_to_actuator (float): Distance from the camera/detection point to the actuator (meters).
        """
        self._rotating_speed = rotating_speed
        self._distance_to_actuator = distance_to_actuator

    def calculate_timing(
            self, processing_delay: float = 0.0, actuator_response_time: float = 0.0
    ) -> float:
        """
        Calculate the effective time delay to trigger the actuator.

        The delay is computed based on the time it takes for a capsule to travel the distance
        to the actuator minus any additional delays
        (e.g., image processing and actuator response time).

        Parameters:
            processing_delay (float): Delay due to image processing in seconds (default 0.0).
            actuator_response_time (float):Aactuator's response delay in seconds (default 0.0).

        Returns:
            float: Effective delay time in seconds.
        """
        if self.rotating_speed <= 0:
            logging.error("Belt speed must be greater than 0.")
            raise ValueError("Belt speed must be greater than 0.")

        # Calculate travel time from detection to actuator.
        travel_time = self.distance_to_actuator / self.rotating_speed
        # Effective delay subtracts processing and actuation delays.
        effective_time = travel_time - processing_delay - actuator_response_time
        return effective_time


if __name__ == "__main__":
    # Create a Belt object with an actuator 0.5m away from the detection point.
    belt = Belt(rotating_speed=0.25, distance_to_actuator=0.5)

    # Suppose the belt speed is 0.25 m/s, the image processing delay is 0.05 seconds,
    # and the actuator has a response time of 0.1 seconds.
    timing = belt.calculate_timing(
        processing_delay=0.05, actuator_response_time=0.1)

    # Print the effective delay time based on the given parameters.
    print("Effective delay time:", timing, "seconds")
