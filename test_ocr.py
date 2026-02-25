import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

image = Image.open("C:/Users/SwatiRP/Downloads/ChatGPT Image Feb 5, 2026, 11_41_48 PM.png")

text = pytesseract.image_to_string(image)

print("OCR RESULT:")
print(text)
