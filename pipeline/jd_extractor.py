from pathlib import Path
from pipeline.text_cleaner import clean_text


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "cleaned_jds"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_and_clean_jd(file_path: Path) -> str:
    text = file_path.read_text(encoding="utf-8")
    return clean_text(text).lower()


def save_cleaned_jd(role: str, cleaned_text: str) -> Path:
    path = OUTPUT_DIR / f"{role}_cleaned.txt"
    path.write_text(cleaned_text, encoding="utf-8")
    return path


def load_jds(role_files: dict, save: bool = True) -> dict:
    jd_texts = {}

    for role, filepath in role_files.items():
        cleaned = extract_and_clean_jd(filepath)

        if save:
            save_cleaned_jd(role, cleaned)

        jd_texts[role] = cleaned

    return jd_texts


if __name__ == "__main__":
    role_files = {
        "softwaredeveloper": DATA_DIR / "jd_swe.txt",
        "mlengineer": DATA_DIR / "jd_ml.txt",
        "datascientist": DATA_DIR / "jd_ds.txt",
        "webdeveloper": DATA_DIR / "jd_web.txt"
    }

    jds = load_jds(role_files)

    for role, jd in jds.items():
        print(f"\n===== {role.upper()} JD SAMPLE =====")
        print(jd[:300])
