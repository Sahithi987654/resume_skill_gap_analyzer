import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LEARNED_PATH = BASE_DIR / "data" / "learned_roles.json"
SKILLS_PATH = BASE_DIR / "data" / "skills.json"

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return text

def detect_role(jd_text):
    text = normalize(jd_text)

    if LEARNED_PATH.exists():
        with open(LEARNED_PATH, "r", encoding="utf-8") as f:
            learned = json.load(f)

        for role in learned:
            if role in text:
                return role

    with open(SKILLS_PATH, encoding="utf-8") as f:
        config = json.load(f)

    matches = {}
    for role, keywords in config["role_keywords"].items():
        matches[role] = sum(1 for k in keywords if k in text)

    best_role = max(matches, key=matches.get)

    if matches[best_role] < 2:
        return None

    return best_role
