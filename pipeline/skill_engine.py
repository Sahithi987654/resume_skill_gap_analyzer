import json
import re
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4

def load_skill_config():
    with open("data/skills.json", encoding="utf-8") as f:
        config = json.load(f)
    return (
        config["skills_dictionary"],
        config["role_aliases"],
        config.get("skill_aliases", {})
    )
SKILLS_DICTIONARY, ROLE_ALIASES, SKILL_ALIASES = load_skill_config()
def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9+.# ]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text
def normalize_skill(skill,skill_aliases):
    return skill_aliases.get(skill, skill)

def extract_project_sections(text):
    lines = text.splitlines()

    project_lines = []
    capture = False

    START_HEADERS = ["projects", "project experience"]
    STOP_HEADERS = ["education", "skills", "certifications", "summary", "interests", "objective", "objectives"]

    for line in lines:
        clean = line.strip().lower()

        if clean in START_HEADERS:
            capture = True
            continue
        if capture and clean in STOP_HEADERS:
            break

        if capture and line.strip():
            project_lines.append(line.strip())

    return " ".join(project_lines)
def project_strength_multiplier(project_text):
    keywords = ["built", "implemented", "designed", "developed", "deployed"]
    has_numbers = bool(re.search(r'\d+', project_text.lower()))
    score = 1
    if any(k in project_text.lower() for k in keywords):
        score += 1
    if has_numbers:
        score += 1
    return score

def extract_skills(text, role):
    skills_dictionary = SKILLS_DICTIONARY
    role_aliases = ROLE_ALIASES
    skill_aliases = SKILL_ALIASES

    text = normalize(text)
    for alias, canonical in skill_aliases.items():
        text = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text)

    from collections import Counter
    found = {"core": Counter(), "preferred": Counter(), "tools": Counter()}


    role = role_aliases.get(role, role)
    role_skills = skills_dictionary[role]

    for tier in ["core", "preferred", "tools"]:
        for skill in role_skills[tier]:

            words = skill.split()

            if len(words) == 1:
                pattern = r'\b' + re.escape(skill) + r'\b'
            else:
                pattern = r'\b' + r'\s+'.join(map(re.escape, words)) + r'\b'

            if re.search(pattern, text):
                normalised=normalize_skill(skill,skill_aliases)
                found[tier][normalised]+=1

    return found

def compare_skills(resume, jd):
    report = {}

    for tier in ["core", "preferred", "tools"]:
        resume_counter = resume[tier]
        jd_set = set(jd[tier].keys())

        matched = {s: resume_counter[s] for s in resume_counter if s in jd_set}
        missing = [s for s in jd_set if s not in resume_counter]
        extra   = [s for s in resume_counter if s not in jd_set]

        report[tier] = {
            "matched": matched,
            "missing": missing if missing else None,
            "extra": extra if extra else None
        }

    return report


WEIGHTS = {
    "core": 0.6,
    "preferred": 0.25,
    "tools": 0.15
}

def compute_weighted_score(report):
    weights = {"core": 3, "preferred": 2, "tools": 1}

    total_score = 0
    total_possible = 0

    for tier in ["core", "preferred", "tools"]:
        tier_weight = weights[tier]

        matched_weighted = sum(report[tier]["matched"].values()) if report[tier]["matched"] else 0
        missing_count = len(report[tier]["missing"]) if report[tier]["missing"] else 0

        total_score += matched_weighted * tier_weight
        total_possible += (matched_weighted + missing_count) * tier_weight

    if total_possible == 0:
        return 0.0

    return round((total_score / total_possible) * 100, 2)

def hiring_verdict(report, score,role):
    if role == "mlengineer" and report["core"]["missing"]:
        return "NOT HIRE READY (core ML gaps)"
    if score >= 70:
        return "STRONG FIT"
    if score >= 40:
        return "MODERATE FIT"
    return "NOT HIRE READY"


def improvement_plan(report):
    if report["core"]["missing"]:
        return f"FIX FIRST (core): {report['core']['missing']}"
    if report["preferred"]["missing"]:
        return f"IMPROVE NEXT (preferred): {report['preferred']['missing']}"
    return "NO MAJOR GAPS"
MIN_ACCEPTABLE_SCORE = 20
def evaluate_multiple_roles(cleaned_resume_text, raw_resume_text, jd_texts):
    allowed_roles = set(jd_texts.keys())
    results = []

    project_text = extract_project_sections(raw_resume_text)

    for role,jd in jd_texts.items():
        
        resume_skills = extract_skills(raw_resume_text, role)
        project_skills = extract_skills(project_text, role)

        PROJECT_WEIGHT = project_strength_multiplier(project_text) 

        for tier in ["core", "preferred", "tools"]:
            for skill,count in project_skills[tier].items():
                resume_skills[tier][skill]+=count*PROJECT_WEIGHT


        jd_skills = extract_skills(jd, role)

        report = compare_skills(resume_skills, jd_skills)
        score = compute_weighted_score(report)
        verdict = hiring_verdict(report, score, role)
        role_core_skills = SKILLS_DICTIONARY.get(role, {}).get("core", [])

        if not role_core_skills:
            verdict = "INVALID ROLE DEFINITION"
            score = 0

        results.append({
            "role": role,
            "score": score,
            "verdict": verdict,
            "report": report
        })
    results.sort(key=lambda x: x["score"], reverse=True)

    if results[0]["score"] < MIN_ACCEPTABLE_SCORE:
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
    results = [r for r in results if r["role"] in allowed_roles]

    return results




jd_texts = {
    "webdeveloper": open(r"data\jd_web.txt", encoding="utf-8").read(),
    "datascientist": open(r"data\jd_ds.txt", encoding="utf-8").read(),
    "mlengineer": open(r"data\jd_ml.txt", encoding="utf-8").read(),
    "softwaredeveloper": open(r"data\jd_swe.txt", encoding="utf-8").read()
}
def explain_gaps(report):
    lines = []
    if report["core"]["missing"]:
        lines.append("Critical core skills missing: " + ", ".join(report["core"]["missing"]))
    if report["preferred"]["missing"]:
        lines.append("Recommended skills to strengthen: " + ", ".join(report["preferred"]["missing"]))
    if report["tools"]["missing"]:
        lines.append("Tools to learn: " + ", ".join(report["tools"]["missing"]))
    return "\n".join(lines) if lines else "Your profile aligns well with the job requirements."
def generate_learning_plan(report):
    plan = []
    if report["core"]["missing"]:
        for s in report["core"]["missing"]:
            plan.append(f"Learn core skill: {s}")
    if report["preferred"]["missing"]:
        for s in report["preferred"]["missing"]:
            plan.append(f"Improve skill: {s}")
    if report["tools"]["missing"]:
        for s in report["tools"]["missing"]:
            plan.append(f"Practice tool: {s}")
    return plan

def save_final_report(result):
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"career_report_{timestamp}.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Recommended Role: {result['role'].upper()}\n")
        f.write(f"Match Score: {result['score']}%\n")
        f.write(f"Verdict: {result['verdict']}\n\n")

        f.write("Gap Analysis:\n")
        f.write(explain_gaps(result["report"]) + "\n\n")

        f.write("Learning Roadmap:\n")
        for step in generate_learning_plan(result["report"]):
            f.write("- " + step + "\n")

    return report_path

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def generate_pdf_report(result, txt_path):
    pdf_path = txt_path.with_suffix(".pdf")

    styles = getSampleStyleSheet()
    story = []

    title = f"Career Fit Report"
    subtitle = f"Recommended Role: {result['role'].upper()}"

    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(subtitle, styles["Heading2"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Match Score:</b> {result['score']}%", styles["BodyText"]))
    story.append(Paragraph(f"<b>Verdict:</b> {result['verdict']}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Gap Analysis</b>", styles["Heading3"]))
    for line in explain_gaps(result["report"]).split("\n"):
        story.append(Paragraph(line, styles["BodyText"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Learning Roadmap</b>", styles["Heading3"]))

    for step in generate_learning_plan(result["report"]):
        story.append(Paragraph("• " + step, styles["BodyText"]))

    doc = SimpleDocTemplate(str(pdf_path))
    doc.build(story)

    return pdf_path

def print_career_ranking(results):
    print("\n" + "="*45)
    print("           CAREER FIT RANKING")
    print("="*45)

    for rank, r in enumerate(results, start=1):
        print(f"\n{rank}. ROLE: {r['role'].upper()}")
        print("-"*35)
        print(f"MATCH SCORE : {r['score']}%")
        print(f"VERDICT     : {r['verdict']}")
        print(f"NEXT ACTION : {improvement_plan(r['report'])}")

        for tier in ["core", "preferred", "tools"]:
            info = r["report"][tier]
            print(f"\n{tier.upper()} SKILLS")
            print(f"  matched : {info['matched'] if info['matched'] else 'None'}")
            print(f"  missing : {info['missing'] if info['missing'] else 'None'}")
            print(f"  extra   : {info['extra'] if info['extra'] else 'None'}")

        print("\n" + "-"*45)
def explain_best_fit(results):
    best = results[0]
    others = results[1:]

    reasons = []
    for tier in ["core", "preferred", "tools"]:
        best_match = len(best["report"][tier]["matched"])
        other_match = sum(len(o["report"][tier]["matched"]) for o in others)

        if best_match > other_match:
            reasons.append(f"stronger {tier} skill alignment")

    return ", ".join(reasons) if reasons else "overall higher skill match"
def explain_recommendation(result):
    reasons = []

    for tier in ["core", "preferred", "tools"]:
        matched = result["report"][tier]["matched"] or []
        missing = result["report"][tier]["missing"] or []

        if matched:
            reasons.append(f"strong {tier} skill match ({', '.join(matched)})")

        if missing:
            reasons.append(f"some gaps in {tier} skills ({', '.join(missing)})")

    return "This role was recommended because " + ", and ".join(reasons) + "."

if __name__ == "__main__":
    raw_resume = open("resume_text_final.txt", encoding="utf-8").read()
    cleaned_resume = open("resume_text_cleaned.txt", encoding="utf-8").read()

    project_text = extract_project_sections(raw_resume)

    print("\n--- PROJECT CONTENT ---\n")
    print(project_text)

    results = evaluate_multiple_roles(cleaned_resume, raw_resume, jd_texts)

    print_career_ranking(results)
