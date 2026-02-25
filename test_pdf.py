from pdf2image import convert_from_path

images = convert_from_path("sample.pdf")

print(f"Pages extracted: {len(images)}")
