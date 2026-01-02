from pathlib import Path
from pipeline.skill_engine import generate_learning_plan,explain_recommendation
import streamlit as st
from pipeline.full_resume_extractor import extract_text_from_pdf
from pipeline.text_cleaner import clean_text
from pipeline.skill_engine import evaluate_multiple_roles, save_final_report,generate_pdf_report
from pipeline.role_detector import detect_role
from pipeline.role_builder import build_new_role
from pipeline.role_inference import infer_role_name

import tempfile
import os
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

BASE_DIR = Path(__file__).resolve().parent
if (BASE_DIR / "data").exists() is False:
    BASE_DIR = BASE_DIR.parent
roles = ["mlengineer", "datascientist", "webdeveloper", "softwaredeveloper"]

DATA_DIR = BASE_DIR / "data"
JD_FILES = {
    "mlengineer": "jd_ml.txt",
    "datascientist": "jd_ds.txt",
    "webdeveloper": "jd_web.txt",
    "softwaredeveloper": "jd_swe.txt"
}


st.set_page_config(page_title="Resume Skill Gap Analyzer", layout="centered")

st.title("Resume Skill Gap Analyzer")
st.write("Upload your resume and analyze your career fit.")

resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

jd_input = st.text_area("Paste Job Description (optional)")
input_signature = (
    resume_file.name if resume_file else "",
    jd_input.strip()
)

if "last_input" not in st.session_state or st.session_state.last_input != input_signature:
    st.session_state.analysis_done = False
    st.session_state.last_input = input_signature

if st.button("Analyze"):
    if resume_file is None:
        st.error("Please upload a resume.")
    else:
        with st.spinner("Processing resume..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(resume_file.read())
                resume_path = tmp.name

            raw_text = extract_text_from_pdf(resume_path)
            cleaned_resume = clean_text(raw_text)

            os.remove(resume_path)

        jd_texts = {}

        if jd_input.strip():
            detected_role = detect_role(jd_input)

            if detected_role is None:
                inferred_name = infer_role_name(jd_input)
                build_new_role(inferred_name, jd_input)
                st.warning(f"New role learned: {inferred_name.upper()}")
                detected_role = inferred_name

            st.success(f"Detected Job Role: {detected_role.upper()}")

            jd_texts = {detected_role: jd_input}
            st.session_state.target_role = detected_role

        else:
            for role in roles:
                with open(DATA_DIR / JD_FILES[role], encoding="utf-8") as f:
                    jd_texts[role] = f.read()
            st.session_state.target_role = None

        with st.spinner("Analyzing skills..."):
            results = evaluate_multiple_roles(raw_text, raw_text, jd_texts)
        best = results[0]
        if st.session_state.target_role and best["role"] != st.session_state.target_role:
            st.warning("The resume aligns better with another role than the detected job description.")


        if not st.session_state.analysis_done:
            report_path = save_final_report(best)
            pdf_path = generate_pdf_report(best, report_path)

            st.session_state.report_path = report_path
            st.session_state.pdf_path = pdf_path
            st.session_state.best = best
            st.session_state.analysis_done = True
        else:
            report_path = st.session_state.report_path
            pdf_path = st.session_state.pdf_path
            best = st.session_state.best

        st.success("Analysis complete")
        st.markdown("---")

        st.subheader("Recommended Role")
        st.write(best["role"].upper())

        st.subheader("Match Score")
        st.write(f"{best['score']}%")
        st.progress(best["score"] / 100)

        if best["verdict"] == "NO SUITABLE ROLE FOUND":
            st.warning("The resume currently does not align well with this job role. Review the skill gaps below.")


        st.subheader("Verdict")
        st.write(best["verdict"])
        if best["verdict"] != "NO SUITABLE ROLE FOUND":
            st.subheader("Why This Role?")
            st.write(explain_recommendation(best))

        if best["verdict"] != "NO SUITABLE ROLE FOUND":
            st.subheader("Skill Gap Breakdown")

            for tier in ["core", "preferred", "tools"]:
                missing = best["report"][tier]["missing"] or []
                matched = best["report"][tier]["matched"] or []

                st.write(f"**{tier.upper()} SKILLS**")
                st.write("Matched:", ", ".join(matched) if matched else "None")
                st.write("Missing:", ", ".join(missing) if missing else "None")

        else:
            st.info("Try uploading a resume relevant to the detected job description, or paste a different job description.")

        if best["verdict"] != "NO SUITABLE ROLE FOUND":
            st.subheader("Personalized Learning Roadmap")
            for step in generate_learning_plan(best["report"]):
                st.write("•", step)

        with open(report_path, "r", encoding="utf-8") as f:
            st.download_button("Download TXT Report", f.read(), file_name=report_path.name)
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF Report", f, file_name=pdf_path.name)