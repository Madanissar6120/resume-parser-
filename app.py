# app.py

import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import matplotlib.pyplot as plt
import re

# -----------------------------
# STREAMLIT CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="Advanced AI Resume Analyzer",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# GEMINI API CONFIGURATION
# -----------------------------
# Streamlit Cloud -> Settings -> Secrets
# Add:
# GOOGLE_API_KEY="your_api_key"

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# -----------------------------
# APP TITLE
# -----------------------------
st.title("🤖 Advanced AI Resume Analyzer & Career Dashboard")
st.caption("Developed by Madan Kumar Issar")
st.markdown("---")

# -----------------------------
# FILE UPLOADER
# -----------------------------
uploaded_file = st.file_uploader(
    "📤 Upload Resume (PDF/DOCX)",
    type=["pdf", "docx"]
)

# -----------------------------
# TEXT EXTRACTION FUNCTION
# -----------------------------
def extract_text(file):
    text = ""

    if file.type == "application/pdf":
        reader = PdfReader(file)

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)

        for para in doc.paragraphs:
            text += para.text + "\n"

    return text.strip()

# -----------------------------
# MAIN ANALYSIS
# -----------------------------
if uploaded_file:

    st.success("✅ Resume Uploaded Successfully!")

    resume_text = extract_text(uploaded_file)

    if resume_text:

        with st.spinner("⏳ Analyzing Resume with Gemini AI..."):

            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            You are an expert AI Resume Analyzer.

            Analyze the following resume and provide:

            1. Candidate Overview
            2. Education
            3. Experience
            4. Technical Skills
            5. Soft Skills
            6. Recommended Job Roles with Fit Score %
            7. Missing Skills
            8. Resume Improvement Suggestions

            Resume:
            {resume_text}
            """

            response = model.generate_content(prompt)

            result_text = response.text

        st.success("✅ Resume Analysis Completed!")

        # -----------------------------
        # DISPLAY RESULT
        # -----------------------------
        st.subheader("📄 Resume Analysis Report")

        st.markdown(result_text)

        # -----------------------------
        # EXTRACT ROLE + SCORE
        # -----------------------------
        st.subheader("🎯 Recommended Roles")

        roles = []
        missing_skills_dict = {}

        for line in result_text.split("\n"):

            match = re.search(
                r"^(?P<role>.+?)[:\-]?\s*(?P<score>\d{1,3})%",
                line
            )

            if match:
                role_name = match.group("role").strip()
                role_score = int(match.group("score"))

                roles.append((role_name, role_score))

            missing_match = re.search(
                r"Missing Skills[:\-]\s*(.*)",
                line,
                re.IGNORECASE
            )

            if missing_match and roles:
                missing_skills_dict[roles[-1][0]] = [
                    s.strip()
                    for s in missing_match.group(1).split(",")
                ]

        # -----------------------------
        # ROLE DISPLAY
        # -----------------------------
        if roles:

            for role, score in roles:

                st.markdown(f"### {role}")
                st.progress(score / 100)

                st.write(f"Fit Score: {score}%")

                if role in missing_skills_dict:
                    st.warning(
                        f"Missing Skills: {', '.join(missing_skills_dict[role])}"
                    )

        else:
            st.info("No role predictions found.")

        # -----------------------------
        # SKILL GAP VISUALIZATION
        # -----------------------------
        st.subheader("📊 Top Missing Skills")

        all_missing_skills = []

        for skills in missing_skills_dict.values():

            if isinstance(skills, list):
                all_missing_skills.extend(skills)

        if all_missing_skills:

            skill_counts = (
                pd.Series(all_missing_skills)
                .value_counts()
                .head(10)
            )

            fig, ax = plt.subplots(figsize=(8, 5))

            skill_counts.sort_values().plot(
                kind="barh",
                ax=ax
            )

            ax.set_xlabel("Count")
            ax.set_ylabel("Skills")
            ax.set_title("Top Missing Skills")

            st.pyplot(fig)

        else:
            st.info("No missing skills found.")

        # -----------------------------
        # DOWNLOAD CSV
        # -----------------------------
        if roles:

            st.subheader("💾 Download Analysis")

            df = pd.DataFrame({
                "Role": [r[0] for r in roles],
                "Fit Score": [r[1] for r in roles],
                "Missing Skills": [
                    ", ".join(
                        missing_skills_dict.get(r[0], [])
                    )
                    for r in roles
                ]
            })

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="📥 Download CSV Report",
                data=csv,
                file_name="resume_analysis.csv",
                mime="text/csv"
            )

    else:
        st.error("Unable to extract text from resume.")

else:
    st.info("👆 Upload a Resume to Start Analysis")