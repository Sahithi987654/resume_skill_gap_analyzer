import subprocess
from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def get_pdftotext_path():
    
    system_path = shutil.which("pdftotext")
    if system_path:
        return system_path

    
    local_poppler = BASE_DIR / "pipeline" / "poppler" / "poppler-25.12.0" / "Library" / "bin" / "pdftotext.exe"
    if local_poppler.exists():
        return str(local_poppler)

    raise RuntimeError("pdftotext not found. Please install Poppler.")

def extract_text_from_pdf(pdf_path):
    output_file = OUTPUT_DIR / "resume_text_final.txt"
    pdftotext = get_pdftotext_path()

    subprocess.run(
        [pdftotext, "-layout", str(pdf_path), str(output_file)],
        check=True
    )

    return output_file.read_text(encoding="utf-8", errors="ignore")

if __name__ == "__main__":
    text = extract_text_from_pdf(DATA_DIR / "Resume.pdf")
    print("Resume text extracted successfully.")
