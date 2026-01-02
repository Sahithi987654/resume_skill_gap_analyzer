Resume Skill Gap Analyzer

This project builds a complete pipeline for analyzing resumes against job descriptions in order to determine role suitability, identify skill gaps, and generate actionable learning plans.

The system goes beyond basic keyword matching by modeling hiring expectations using a structured skill ontology and rule-based evaluation.
It also supports automatic learning of new job roles from previously unseen job descriptions.

Problem Statement

Choosing a career direction is difficult because job requirements are often vague and resumes are unstructured.
This project converts both into structured data and applies deterministic reasoning to produce measurable career-fit scores and concrete next steps for skill development.

The design emphasizes:

Explainability
Extensibility
Deterministic behavior

System Overview

Resume Pipeline

PDF Resume
 → full_resume_extractor.py
 → resume_text_final.txt
 → text_cleaner.py
 → resume_text_cleaned.txt
 → skill_engine.py
 → career_report.txt / career_report.pdf

Job Description Pipeline

Job Description
 → role_detector.py
 → role_builder.py (for new roles)
 → text_cleaner.py
 → skill_engine.py

Key Features

PDF resume extraction using Poppler
Text normalization and cleaning
Role-based skill ontology (core / preferred / tools)
Weighted scoring model for career fit
Automatic job role detection
Automatic learning of new job roles
Detailed skill gap analysis
Personalized learning roadmap generation
Streamlit-based interactive interface
Exportable reports (TXT and PDF)

Project Structure

resume_skill_gap_analyzer/
│
├── data/
│   ├── skills.json
│   ├── learned_roles.json
│   ├── jd_ml.txt
│   ├── jd_ds.txt
│   ├── jd_web.txt
│   └── sample_resume.pdf
│
├── pipeline/
│   ├── full_resume_extractor.py
│   ├── text_cleaner.py
│   ├── skill_engine.py
│   ├── role_detector.py
│   ├── role_builder.py
│   ├── role_inference.py
│   └── poppler/
│
├── outputs/
│   ├── career_report_*.txt
│   ├── career_report_*.pdf
│
├── ui.py
├── README.md
└── requirements.txt

Example Output

Recommended Role: DATASCIENTIST
Match Score: 83.33%
Verdict: STRONG FIT

Gap Analysis:
Critical core skills missing: statistics

Learning Roadmap:
- Learn core skill: statistics

How to Run

Install dependencies:
pip install -r requirements.txt

Launch the application:
streamlit run ui.py

Design Principles

No black-box ML — decisions are explainable and deterministic
New roles can be added without modifying core logic
Clear separation between data, processing, and UI layers
Built for experimentation and extension

Possible Extensions

Course recommendation engine
Resume rewriting and ATS optimization
Job description ingestion from job portals
Multi-resume comparison
Deployment as a web service

Author

Sahithi Mandapuri
