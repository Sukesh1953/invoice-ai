import pytesseract
from PIL import Image



image = Image.open("C:/Users/SwatiRP/Downloads/ChatGPT Image Feb 5, 2026, 11_41_48 PM.png")

text = pytesseract.image_to_string(image)

print("OCR RESULT:")
print(text)
