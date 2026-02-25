from pdf2image import convert_from_path

images = convert_from_path(
    "sample.pdf",
    poppler_path="poppler/Library/bin"
)

print(len(images))
