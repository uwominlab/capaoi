#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper function to show a given image.
"""


import cv2
import matplotlib.pyplot as plt
import numpy as np


def show_img(img_name: str, img: np.ndarray) -> None:
    """
    Displays an image using matplotlib.

    Args:
        img_name (str): The title of the image to be displayed.
        img (np.ndarray): The image to be displayed. 
                          Can be a color image (3 channels) or a grayscale image (1 channel).

    Returns:
        None
    """
    if not isinstance(img, np.ndarray):
        raise TypeError("The 'img' parameter must be a NumPy ndarray.")

    # Handle color image conversion
    if len(img.shape) == 3:  # Color image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(img)
    else:  # Grayscale image
        plt.imshow(img, cmap='gray')

    plt.axis('off')
    plt.title(img_name)
    plt.show()
