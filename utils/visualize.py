#!usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper function to show a given image.
"""


import cv2
import matplotlib.pyplot as plt
import numpy as np
import pyautogui


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


def cvimshow(img_name: str, img: cv2.typing.MatLike) -> None:
    """
    Displays an image in a resizable window using OpenCV while maintaining aspect ratio.

    Parameters:
    img_name (str): The name of the window in which the image will be displayed.
    img (cv2.typing.MatLike): The image to be displayed.

    Returns:
    None
    """
    cv2.namedWindow(img_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(img_name, cv2.WND_PROP_ASPECT_RATIO, cv2.WND_PROP_ASPECT_RATIO)

    # Get image dimensions
    img_h, img_w = img.shape[:2]

    # Get screen dimensions
    screen_w, screen_h = pyautogui.size()

    # Define the maximum window size (leave some margin)
    max_w, max_h = int(screen_w * 0.8), int(screen_h * 0.8)

    # Compute the scaling factor while maintaining aspect ratio
    scale_factor = min(max_w / img_w, max_h / img_h)

    # Compute new dimensions
    new_w, new_h = int(img_w * scale_factor), int(img_h * scale_factor)

    # Resize the window (but not the image itself)
    cv2.resizeWindow(img_name, new_w, new_h)

    # Display the image without resizing it
    cv2.imshow(img_name, img)
