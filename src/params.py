#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Contains the hyper parameter required for the project.
"""

from pathlib import Path
# Project structure hyper parameters

# Define the base directory as the directory containing this file
ROOT_DIR: Path = Path(__file__).resolve().parent

# Define global paths
DATA_DIR: Path = ROOT_DIR / 'data'

# Camera image hyper parameters
INIT_EXPOSURE_TIME: int = 12490
INIT_FRAME_RATE: int = 40
INIT_GAIN: int = 10

MAX_WIDTH: int = 4196
MAX_HEIGHT: int = 2128

# Visualization window hyper parameters
INIT_WIDTH: int = 2160
INIT_HEIGHT: int = 1440

GRABBING_TIMEOUT_MS: int = 5000
