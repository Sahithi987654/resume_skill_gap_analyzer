import re
from pathlib import Path

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'http\S+', ' ', text)
    text = re.sub(r'[^a-z0-9+.#,()/\- ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

if __name__ == "__main__":
    input_path = Path("outputs/resume_text_final.txt")
    output_path = Path("outputs/resume_text_cleaned.txt")

    input_path.parent.mkdir(exist_ok=True)

    with open(input_path, encoding="utf-8") as f:
        raw = f.read()

    cleaned = clean_text(raw)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("Cleaned resume saved:", output_path)
