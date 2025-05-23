#!usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Contains the hyper parameter required for the project.
"""

from pathlib import Path
from typing import Annotated


# Project structure hyper parameters
# Define the base directory as the directory containing this file
ROOT_DIR: Path = Path(__file__).parent.parent.resolve()
# Define global paths
DATA_DIR: Path = ROOT_DIR / 'data'
IMAGES_DIR: Path = ROOT_DIR / 'images'
BACKUP_DIR: Path = ROOT_DIR / 'backup'
LOG_DIR: Path = ROOT_DIR / 'logs'

DEFAULT_EXPOSURE_TIME: int = 5000
DEFAULT_FRAME_RATE: int = 100
DEFAULT_WIDTH: int = 4200
DEFAULT_HEIGHT: int = 2128
DEFAULT_OFFSET_Y: int = 16

# Camera image hyper parameters
INIT_EXPOSURE_TIME: int = 12490
INIT_FRAME_RATE: int = 15
INIT_GAIN: int = 10

MAX_WIDTH: int = 4196
MAX_HEIGHT: int = 2128

# Visualization window hyper parameters
INIT_WIDTH: int = 2160
INIT_HEIGHT: int = 1440
# INIT_WIDTH: int = 1920
# INIT_HEIGHT: int = 1080

GRABBING_TIMEOUT_MS: int = 5000

FOV_WIDTH_MM: float = 131.5
# FOV_HEIGHT_MM: int = 100
MM_PER_PIXEL: float = FOV_WIDTH_MM / INIT_WIDTH

# Belt hyper parameters
# BELT_LENGTH_MM: int = 390
BELT_LENGTH_MM: int = 390
STRICTLY_FLAT_BELT_LENGTH_MM: int = 340
# BELT_SPEED_MM_S: float = 43.5
# BELT_SPEED_MM_S: float = 108.1558
BELT_SPEED_MM_S: float = 114.0
# BELT_SPEED_MM_S: float = 108.56

# Relay parameter
VENDOR_ID: Annotated[int, "16-bit unsigned"] = 0x16C0
PRODUCT_ID: Annotated[int, "16-bit unsigned"] = 0x05DF

# Relay will switch to Normally Open (NO) position
RELAY_ON: Annotated[int, "16-bit unsigned"] = 0xFF

# Relay will switch to Normally Closed (NC) position
RELAY_OFF: Annotated[int, "16-bit unsigned"] = 0xFC

RELAY_1: Annotated[int, "16-bit unsigned"] = 0x01
RELAY_2: Annotated[int, "16-bit unsigned"] = 0x01 + 1
RELAY_3: Annotated[int, "16-bit unsigned"] = 0x01 + 2
RELAY_4: Annotated[int, "16-bit unsigned"] = 0x01 + 3

ACTUATOR_RETRACTION_TIME: float = 0.15
