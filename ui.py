# app/ui.py
import streamlit as st
import requests
import base64
import json
import os

API_URL = os.getenv("APPLIFY_API_URL", "http://localhost:8000/generate-resume")

st.set_page_config(page_title="Applify", page_icon="📝", layout="centered")
st.title("Applify — Create professional German CVs & cover letters in one click.")

with st.form("candidate_form"):
    st.header("Candidate information")
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    address = st.text_input("Address")
    birth_date = st.text_input("Birth date (MM/YYYY)")
    birth_place = st.text_input("Birth place")
    summary = st.text_area("Profile summary (short)")
    skills = st.text_area("Skills (comma separated)")
    interests = st.text_area("Interests (comma separated)")

    st.header("Experience (optional)")
    exp_json = st.text_area("Paste experience as JSON list (optional). Example format:\n[{'job_title':'Dev','company':'X','start_date':'01/2022','end_date':'07/2023','location':'Berlin','responsibilities':['...']}]")

    st.header("Education (optional)")
    edu_json = st.text_area("Paste education as JSON list (optional)")

    st.header("Job description (paste full text)")
    job_description = st.text_area("Job description", height=200)

    include_simple = st.checkbox("Also generate einfache Sprache versions", value=False)
    want_pdf = st.checkbox("Return PDF/DOCX (base64)", value=False)

    submitted = st.form_submit_button("Generate")

if submitted:
    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "address": address,
        "birth_date": birth_date,
        "birth_place": birth_place,
        "summary": summary,
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "interests": [s.strip() for s in interests.split(",") if s.strip()],
        "experience": [],
        "education": [],
        "languages": [],
        "additional_info": "",
        "job_description": job_description,
        "include_simple_version": include_simple,
        "want_pdf": want_pdf
    }

    # Try parse JSON fields if provided
    if exp_json:
        try:
            payload["experience"] = json.loads(exp_json)
        except Exception:
            st.error("Invalid JSON for experience")
    if edu_json:
        try:
            payload["education"] = json.loads(edu_json)
        except Exception:
            st.error("Invalid JSON for education")

    st.info("Sending your data to Applify backend...")
    try:
        res = requests.post(API_URL, json=payload, timeout=120)
        if res.status_code != 200:
            st.error(f"Backend error: {res.text}")
        else:
            data = res.json()
            st.success("Generated!")
            st.subheader("Lebenslauf (CV)")
            st.code(data.get("cv_text",""), language="text")
            st.subheader("Anschreiben (Cover Letter)")
            st.code(data.get("cover_letter_text",""), language="text")
            st.subheader("Unterlagen (What to include)")
            st.text(data.get("unterlagen_info",""))
            if include_simple:
                st.subheader("Lebenslauf (einfache Sprache)")
                st.code(data.get("cv_simple",""), language="text")
                st.subheader("Anschreiben (einfache Sprache)")
                st.code(data.get("cover_letter_simple",""), language="text")

            if want_pdf and data.get("pdf_base64"):
                st.download_button(
                    label="Download combined PDF",
                    data=base64.b64decode(data["pdf_base64"]),
                    file_name=f"applify_{name.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                st.download_button(
                    label="Download combined DOCX",
                    data=base64.b64decode(data["docx_base64"]),
                    file_name=f"applify_{name.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

    except Exception as e:
        st.exception(e)
