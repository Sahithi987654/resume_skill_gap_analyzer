import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

with open(DATA_DIR / "skills.json", encoding="utf-8") as f:
    CONFIG = json.load(f)

SKILLS_DICTIONARY = CONFIG["skills_dictionary"]
ROLE_ALIASES = CONFIG["role_aliases"]
SKILL_ALIASES = CONFIG.get("skill_aliases", {})

DERIVED_SKILLS = {
    "supervisedlearning": ["machine learning", "classification", "regression", "model training"],
    "unsupervisedlearning": ["clustering", "dimensionality reduction"],
    "featureengineering": ["data preprocessing", "feature extraction", "data cleaning"],
    "statistics": ["statistical", "hypothesis", "probability"],
    "datavisualization": ["visualization", "dashboard", "plot", "graph"],

    "lessonplanning": ["lesson plan", "teaching plan", "course planning"],
    "classroommanagement": ["discipline", "class control", "behavior management"],
    "studentassessment": ["exam", "test", "grading", "evaluation"],
    "curriculumdesign": ["syllabus", "curriculum", "course structure"]
}


def repair_broken_spacing(text):
    fixed_lines = []
    for line in text.splitlines():
        if re.match(r'^(?:[A-Za-z]\s+){3,}[A-Za-z]$', line.strip()):
            fixed_lines.append(line.replace(" ", ""))
        else:
            fixed_lines.append(line)
    return "\n".join(fixed_lines)

def rebuild_word_boundaries(text):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    return text

def normalize(text):
    text = text.lower()
    text = re.sub(r'(?<=\b[a-z])\s+(?=[a-z]\b)', '', text)
    text = text.replace("postgre sql", "postgresql")
    text = text.replace("my sql", "mysql")
    text = text.replace("sci kit learn", "scikitlearn")
    text = re.sub(r'[^a-z0-9+.# ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_skill(skill):
    return SKILL_ALIASES.get(skill, skill)

def extract_project_sections(text):
    lines = text.splitlines()
    capture = False
    collected = []

    for line in lines:
        clean = line.strip().lower()

        if clean in ["projects", "project experience"]:
            capture = True
            continue

        if capture and clean in ["education", "skills", "summary", "experience"]:
            break

        if capture and line.strip():
            collected.append(line)

    return " ".join(collected)


def extract_skills(text, role):
    text = normalize(text)
    found = {"core": Counter(), "preferred": Counter(), "tools": Counter()}

    role = ROLE_ALIASES.get(role, role)
    role_skills = SKILLS_DICTIONARY[role]

    for tier in ["core", "preferred", "tools"]:
        for skill in role_skills[tier]:
            skill_norm = normalize_skill(skill)
            pattern = rf'\b{re.escape(skill_norm)}\b'

            if re.search(pattern, text):
                found[tier][skill_norm] += 1

                if skill_norm in ("postgresql", "mysql"):
                    found["core"]["sql"] += 1

            else:
                if tier in ("core", "preferred"):
                    for trigger in DERIVED_SKILLS.get(skill_norm, []):
                        if trigger in text:
                            found[tier][skill_norm] += 0.5


    return found


def compare_skills(resume, target):
    report = {}

    for tier in ["core", "preferred", "tools"]:
        r = resume[tier]
        t = set(target[tier].keys())

        matched = {k: r[k] for k in r if k in t}
        missing = [k for k in t if k not in r]
        extra = [k for k in r if k not in t]

        report[tier] = {"matched": matched, "missing": missing, "extra": extra}

    return report


def compute_weighted_score(report):
    weights = {"core": 3, "preferred": 1.5, "tools": 1}

    total = 0
    possible = 0

    for tier, w in weights.items():
        matched = len(report[tier]["matched"])
        missing = len(report[tier]["missing"])

        total += matched * w
        possible += (matched + missing) * w

    return round((total / possible) * 100, 2) if possible else 0


MIN_ACCEPTABLE_SCORE = 10

def evaluate_multiple_roles(cleaned_resume, raw_resume, jd_texts):
    raw_resume = repair_broken_spacing(raw_resume)
    cleaned_resume = repair_broken_spacing(cleaned_resume)

    project_text = extract_project_sections(raw_resume)

    results = []

    for role in jd_texts:
        resume_skills = extract_skills(cleaned_resume, role)
        project_skills = extract_skills(project_text, role)

        for tier in project_skills:
            for skill, count in project_skills[tier].items():
                PROJECT_MULTIPLIER = 3

                for tier in project_skills:
                    for skill, count in project_skills[tier].items():
                        resume_skills[tier][skill] += count * PROJECT_MULTIPLIER


        target = {
            tier: {s: 1 for s in SKILLS_DICTIONARY[role][tier]}
            for tier in ["core", "preferred", "tools"]
        }

        report = compare_skills(resume_skills, target)
        score = compute_weighted_score(report)
        core_matches = len(report["core"]["matched"])

        if core_matches == 0:
            continue

        verdict = (
            "STRONG FIT" if score >= 70 else
            "MODERATE FIT" if score >= 40 else
            "NOT HIRE READY"
        )

        results.append({"role": role, "score": score, "verdict": verdict, "report": report})

    valid_results = []
    for r in results:
        total_matches = sum(len(r["report"][tier]["matched"]) for tier in ["core", "preferred", "tools"])
        if total_matches > 0:
            valid_results.append(r)

    if not valid_results:
        return [{
            "role": "none",
            "score": 0.0,
            "verdict": "NO SUITABLE ROLE FOUND",
            "report": {
                "core": {"matched": None, "missing": None, "extra": None},
                "preferred": {"matched": None, "missing": None, "extra": None},
                "tools": {"matched": None, "missing": None, "extra": None}
            }
     }]

    valid_results.sort(key=lambda x: x["score"], reverse=True)

    best = valid_results[0]
    if best["score"] < MIN_ACCEPTABLE_SCORE:
        best["verdict"] = "NO SUITABLE ROLE FOUND"
    elif best["score"] >= 70:
        best["verdict"] = "STRONG FIT"
    elif best["score"] >= 50:
        best["verdict"] = "HIRE READY"
    elif best["score"] >= 35:
        best["verdict"] = "ALMOST READY"
    elif best["score"] >= 20:
        best["verdict"] = "FOUNDATION PRESENT"
    else:
        best["verdict"] = "NOT HIRE READY"

    return valid_results

def generate_learning_plan(report):
    plan = []
    for tier in ["core", "preferred", "tools"]:
        missing = report[tier].get("missing")
        if not missing:
            continue
        for skill in missing:
            plan.append(f"Learn {skill}")
    return plan


def explain_recommendation(result):
    reasons = []
    for tier in result["report"]:
        if result["report"][tier]["matched"]:
            reasons.append(f"{tier} strength: {', '.join(result['report'][tier]['matched'])}")
    return "This role was recommended because " + ", ".join(reasons) + "."

def explain_gaps(report):
    lines = []
    for tier in ["core", "preferred", "tools"]:
        missing = report[tier].get("missing")
        if missing:
            lines.append(f"{tier.upper()} missing: " + ", ".join(missing))
    return "\n".join(lines) if lines else "No major skill gaps detected."

def save_final_report(result):
    out = Path("outputs")
    out.mkdir(exist_ok=True)
    path = out / f"career_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Role: {result['role']}\nScore: {result['score']}%\nVerdict: {result['verdict']}\n")

    return path


def generate_pdf_report(result, txt_path):
    pdf = txt_path.with_suffix(".pdf")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Career Fit Report", styles["Title"]),
        Paragraph(f"Role: {result['role']}", styles["Heading2"]),
        Paragraph(f"Score: {result['score']}%", styles["BodyText"]),
        Paragraph(f"Verdict: {result['verdict']}", styles["BodyText"]),
        Spacer(1, 12),
    ]

    for step in generate_learning_plan(result["report"]):
        story.append(Paragraph(step, styles["BodyText"]))

    SimpleDocTemplate(str(pdf)).build(story)
    return pdf
