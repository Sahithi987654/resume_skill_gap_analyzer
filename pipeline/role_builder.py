import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LEARNED_PATH = BASE_DIR / "data" / "learned_roles.json"


def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return text
STOPWORDS = {
    "with","and","the","for","from","that","this","will","have","has","are","was",
    "were","but","not","you","your","our","their","they","them","such","able",
    "seeking","looking","responsible","knowledgeable","dedicated","strong","excellent",
    "good","high","new","all","any","other","more","less","very","use","using",
    "experience","skills","work","working","team","role","job","position"
}

def extract_candidate_skills(jd_text):
    text = normalize(jd_text)

    phrases = re.findall(r'\b[a-z]{3,}(?:\s[a-z]{3,}){0,2}\b', text)

    clean = []
    for p in phrases:
        words = p.split()
        if any(w in STOPWORDS for w in words):
            continue
        if len(words) == 1 and len(words[0]) < 5:
            continue
        clean.append(p)

    unique = list(dict.fromkeys(clean))
    return unique[:20]



def build_new_role(role_name, jd_text, skills_file="data/skills.json"):
    with open(skills_file, encoding="utf-8") as f:
        config = json.load(f)

    extracted = extract_candidate_skills(jd_text)

    new_role_definition = {
        "core": extracted[:8],
        "preferred": extracted[8:14],
        "tools": extracted[14:20]
    }

    config["skills_dictionary"][role_name] = new_role_definition
    config["role_keywords"][role_name] = extracted[:6]

    with open(skills_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    save_learned_role(role_name, config["skills_dictionary"][role_name])

    return extracted


def save_learned_role(role_name, role_data):
    LEARNED_PATH.parent.mkdir(exist_ok=True)

    if LEARNED_PATH.exists():
        with open(LEARNED_PATH, "r", encoding="utf-8") as f:
            learned = json.load(f)
    else:
        learned = {}

    learned[role_name] = role_data

    with open(LEARNED_PATH, "w", encoding="utf-8") as f:
        json.dump(learned, f, indent=4)
