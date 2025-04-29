#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parameters to update the threshold values for defect detection algorithm.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class DefectDetectionParams:
    """
    Dataclass to hold the parameters for defect detection parameter.

    Attributes:
        normal_length_lower (int): Lower bound for the normal defect length.
        normal_length_upper (int): Upper bound for the normal defect length.
        normal_area_lower (int): Lower bound for the normal defect area.
        normal_area_upper (int): Upper bound for the normal defect area.
        similarity_threshold (float): Threshold for similarity comparison, must be non-negative.
        local_defect_length (int): Length threshold for detecting local defects.

    Methods:
        __post_init__: Validates that the lower bounds are positive
                       and less than their respective upper bounds.

    Example:
        >>> params = DefectDetectionParams(
        ...     normal_length_lower=310,
        ...     normal_length_upper=330,
        ...     normal_area_lower=30500,
        ...     normal_area_upper=35000,
        ...     similarity_threshold=0.05,
        ...     local_defect_length=75
        ... )
        >>> params.normal_length_lower
        310
        >>> params.normal_length_upper
        330
        >>> params.normal_area_lower
        30500
        >>> params.normal_area_upper
        35000
        >>> params.similarity_threshold
        0.05
        >>> params.local_defect_length
        75

        # Test for invalid bounds (should raise AssertionError)
        >>> DefectDetectionParams(normal_length_lower=350, normal_length_upper=300)
        Traceback (most recent call last):
        ...
        AssertionError

        >>> DefectDetectionParams(normal_area_lower=35000, normal_area_upper=30500)
        Traceback (most recent call last):
        ...
        AssertionError

        # Test for invalid similarity threshold (should raise AssertionError)
        >>> DefectDetectionParams(similarity_threshold=-0.05)
        Traceback (most recent call last):
        ...
        AssertionError
    """

    normal_length_lower: int = 310
    normal_length_upper: int = 330

    normal_area_lower: int = 30500
    normal_area_upper: int = 35000

    similarity_threshold: float = 0.05
    local_defect_length: int = 75

    def __post_init__(self):
        def requires_positive_lower_upper(lower: int, upper: int) -> bool:
            return 0 < lower < upper

        assert requires_positive_lower_upper(
            self.normal_length_lower, self.normal_length_upper)

        assert requires_positive_lower_upper(
            self.normal_area_lower, self.normal_area_upper)

        assert self.similarity_threshold >= 0


if __name__ == "__main__":
    import doctest
    doctest.testmod()
