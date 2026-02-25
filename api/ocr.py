import pytesseract
from PIL import Image
import io
import cv2
import numpy as np


def extract_text_from_image(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    open_cv_image = np.array(image)

    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # Image quality score (sharpness)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    quality_score = min(variance / 1000, 1.0)

    # Preprocess
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    text = pytesseract.image_to_string(gray)

    return text, round(quality_score, 2)


