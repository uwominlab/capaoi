"""
Helper function to show a given image.
"""


import cv2
import matplotlib.pyplot as plt


def show_img(img_name: str, img: cv2.typing.MatLike) -> None:
    """
    Displays an image using matplotlib.
        img_name (str): The title of the image to be displayed.
        img (cv2.typing.MatLike): The image to be displayed. It can be a color image (3 channels) or a grayscale image (1 channel).
    Returns:
        None
    Args:
        img_name (str): _description_
        img (cv2.typing.MatLike): _description_
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2RGB)
        plt.imshow(X=img)
    else:
        plt.imshow(img, 'gray')
    plt.axis('off')
    plt.title(label=img_name)
    plt.show()
