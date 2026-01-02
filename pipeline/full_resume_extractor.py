from pathlib import Path
from PIL import Image
import pytesseract
import pdf2image

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_text_from_pdf(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    text = ""

    for img in images:
        text += pytesseract.image_to_string(img)

    output_file = OUTPUT_DIR / "resume_text_final.txt"
    output_file.write_text(text, encoding="utf-8")

    return text
