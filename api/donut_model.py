# api/donut_model.py
from transformers import DonutProcessor, VisionEncoderDecoderModel
from PIL import Image

processor = DonutProcessor.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-cord-v2"
)
model = VisionEncoderDecoderModel.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-cord-v2"
)

def extract_with_donut(image: Image.Image) -> dict:
    pixel_values = processor(image, return_tensors="pt").pixel_values
    outputs = model.generate(pixel_values, max_length=512)

    text = processor.batch_decode(outputs, skip_special_tokens=True)[0]

    return {
        "raw_donut_output": text
    }
