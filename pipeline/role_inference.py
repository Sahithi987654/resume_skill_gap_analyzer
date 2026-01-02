import re

KNOWN_BASE_ROLES = {
    "teacher": ["teacher", "educator", "instructor", "professor", "tutor"],
    "datascientist": ["data scientist", "data science"],
    "dataanalyst": ["data analyst", "business analyst"],
    "softwaredeveloper": ["software developer", "developer", "programmer"],
    "webdeveloper": ["web developer", "frontend", "backend"],
    "mlengineer": ["machine learning engineer", "ml engineer"],
    "productmanager": ["product manager"],
    "projectmanager": ["project manager"],
    "nurse": ["nurse", "nursing"],
    "doctor": ["doctor", "physician", "mbbs", "md"]
}

def infer_role_name(jd_text):
    text = jd_text.lower()

    for canonical, aliases in KNOWN_BASE_ROLES.items():
        for alias in aliases:
            if alias in text:
                return canonical

    for line in jd_text.splitlines():
        clean = line.lower().strip()
        if 2 <= len(clean.split()) <= 4:
            if any(word in clean for word in ["engineer", "manager", "teacher", "analyst", "developer", "nurse", "doctor"]):
                return clean.replace(" ", "")

    return "customrole"
