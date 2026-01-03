from pathlib import Path
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)

    text = []
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text.append(content)

    final_text = "\n".join(text)

    output_file = OUTPUT_DIR / "resume_text_final.txt"
    output_file.write_text(final_text, encoding="utf-8")

    return final_text
