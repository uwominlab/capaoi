# -- coding: utf-8 -*-
# Vision Agent Sample Code
# This code demonstrates how to use the vision agent to detect capsules on a roller belt
# and draw bounding boxes around them with confidence scores.

import matplotlib.pyplot as plt

from vision_agent.tools import load_image, overlay_bounding_boxes, save_image
from vision_agent.tools import owlv2_object_detection

def detect_capsules_on_roller_belt(image_path: str) -> str:
    """
    Detect capsules on the roller belt in an image, draw bounding boxes and confidence
    scores on them, and return the path to the annotated image.

    Args:
        image_path (str): The path to the image in which we want to detect capsules.

    Returns:
        str: The file path to the annotated image with capsules bounding boxes and scores.
    """
    # 1. Load the image
    img = load_image(image_path)

    # 2. Use the owlv2_object_detection tool to detect capsules
    detections = owlv2_object_detection("capsule, pill", img)

    # 3. Overlay bounding boxes and confidence scores on the image
    img_with_bboxes = overlay_bounding_boxes(img, detections)

    # 4. Save the result
    output_path = "capsule_detections.jpg"
    save_image(img_with_bboxes, output_path)

    # 5. Return the path of the final image
    return output_path


def main():
    test_image_path = "../backup/AAA/Figs/Fig1.png"
    test_image = load_image(test_image_path)
    # Detect capsules on the roller belt
    detection_result = detect_capsules_on_roller_belt(test_image)

    visualization = load_image(detection_result)
    # Show the visualization
    plt.imshow(visualization)
    plt.show()


if __name__ == "__main__":
    main()
