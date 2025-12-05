# app/ui.py
import streamlit as st
import requests
import pdfplumber
import docx
from io import BytesIO
import base64
import json
import re

# ========== CONFIG ==========
API_URL = st.secrets.get("APPLIFY_API_URL", "http://localhost:8000/generate-resume")
# If you store it in .env or Streamlit secrets, it will be picked up.
# ============================

st.set_page_config(page_title="Applify — CV & Cover Letter", layout="wide")
st.title("🇩🇪 Applify — AI German CV & Cover Letter Generator")

# Initialize session state for dynamic lists
if "experience" not in st.session_state:
    st.session_state.experience = []
if "education" not in st.session_state:
    st.session_state.education = []
if "parsed_resume_text" not in st.session_state:
    st.session_state.parsed_resume_text = ""
if "parsed_payload" not in st.session_state:
    st.session_state.parsed_payload = None
if "output_language" not in st.session_state:
    st.session_state.output_language = "de"  # default German

# Helpers: extract text from uploaded file
def extract_text_from_file(uploaded):
    if not uploaded:
        return ""
    name = uploaded.name.lower()
    if name.endswith(".pdf"):
        try:
            with pdfplumber.open(uploaded) as pdf:
                return "\n".join((p.extract_text() or "") for p in pdf.pages)
        except Exception as e:
            st.error(f"Failed to extract PDF text: {e}")
            return ""
    elif name.endswith(".docx"):
        try:
            doc = docx.Document(uploaded)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            st.error(f"Failed to extract DOCX text: {e}")
            return ""
    else:
        return uploaded.getvalue().decode("utf-8", errors="ignore")

# Helper: try to prefill top-level fields from parsed payload
def autofill_from_parsed(parsed):
    if not parsed:
        return
    # top-level fields
    if parsed.get("name") and not st.session_state.get("name"):
        st.session_state.name = parsed.get("name")
    if parsed.get("email") and not st.session_state.get("email"):
        st.session_state.email = parsed.get("email")
    if parsed.get("phone") and not st.session_state.get("phone"):
        st.session_state.phone = parsed.get("phone")
    if parsed.get("address") and not st.session_state.get("address"):
        st.session_state.address = parsed.get("address")
    if parsed.get("summary") and not st.session_state.get("summary"):
        st.session_state.summary = parsed.get("summary")

    # experience list
    parsed_exp = parsed.get("experience") or parsed.get("work_experience") or []
    if parsed_exp and not st.session_state.experience:
        # normalize to expected keys
        for e in parsed_exp:
            st.session_state.experience.append({
                "job_title": e.get("job_title") or e.get("title") or e.get("role") or "",
                "company": e.get("company") or e.get("employer") or "",
                "start_date": e.get("start_date") or e.get("from") or "",
                "end_date": e.get("end_date") or e.get("to") or "",
                "location": e.get("location") or "",
                "responsibilities": e.get("responsibilities") or e.get("description") or []
            })

    # education list
    parsed_edu = parsed.get("education") or []
    if parsed_edu and not st.session_state.education:
        for ed in parsed_edu:
            st.session_state.education.append({
                "institution": ed.get("institution") or ed.get("school") or "",
                "degree": ed.get("degree") or ed.get("qualification") or "",
                "start_date": ed.get("start_date") or "",
                "end_date": ed.get("end_date") or "",
                "location": ed.get("location") or "",
                "note": ed.get("note") or ""
            })

    # skills & languages
    if parsed.get("skills") and not st.session_state.get("skills"):
        st.session_state.skills = parsed.get("skills")
    if parsed.get("languages") and not st.session_state.get("languages"):
        st.session_state.languages = parsed.get("languages")

# UI layout: sidebar for inputs and upload
with st.sidebar:
    st.header("Your details")
    # Top-level inputs with session_state binding
    name = st.text_input("Full name", value=st.session_state.get("name", ""))
    email = st.text_input("Email", value=st.session_state.get("email", ""))
    phone = st.text_input("Phone", value=st.session_state.get("phone", ""))
    address = st.text_area("Address", value=st.session_state.get("address", ""), height=80)
    summary = st.text_area("Professional summary", value=st.session_state.get("summary", ""), height=120)

    st.markdown("---")
    st.subheader("Language / Output")
    lang = st.radio("Target language for generated documents", options=["de", "en"], index=0 if st.session_state.output_language=="de" else 1, format_func=lambda x: "German (Deutsch)" if x=="de" else "English")
    st.session_state.output_language = lang

    st.markdown("---")
    st.subheader("Resume Upload (PDF / DOCX)")
    uploaded_file = st.file_uploader("Upload your existing resume to auto-fill", type=["pdf", "docx", "txt"])

    # Controls for parsing and generation
    st.markdown("---")
    want_pdf = st.checkbox("Provide downloadable PDF/DOCX", value=True)
    st.markdown("Click parse to extract and fill the form before generating.")
    parse_button = st.button("Parse Resume" if uploaded_file else "Parse (no file)", type="primary")
    generate_button_sidebar = st.button("Generate (from sidebar)")

# MAIN: two-column layout
left_col, right_col = st.columns([1, 1], gap="large")

# LEFT: dynamic form for experience / education
with left_col:
    st.subheader("Work Experience")
    # Add / remove controls
    c1, c2 = st.columns([1, 1])
    if c1.button("➕ Add experience"):
        st.session_state.experience.append({
            "job_title": "",
            "company": "",
            "start_date": "",
            "end_date": "",
            "location": "",
            "responsibilities": []
        })
    if c2.button("➖ Remove last experience"):
        if st.session_state.experience:
            st.session_state.experience.pop()

    # render each experience item
    for i, exp in enumerate(st.session_state.experience):
        st.markdown(f"**Experience #{i+1}**")
        exp_job = st.text_input(f"Job title {i+1}", value=exp.get("job_title",""), key=f"job_title_{i}")
        exp_company = st.text_input(f"Company {i+1}", value=exp.get("company",""), key=f"company_{i}")
        exp_start = st.text_input(f"Start (MM/YYYY) {i+1}", value=exp.get("start_date",""), key=f"start_{i}")
        exp_end = st.text_input(f"End (MM/YYYY or 'Present') {i+1}", value=exp.get("end_date",""), key=f"end_{i}")
        exp_loc = st.text_input(f"Location {i+1}", value=exp.get("location",""), key=f"loc_{i}")
        exp_desc = st.text_area(f"Responsibilities (comma separated) {i+1}", value=", ".join(exp.get("responsibilities") if isinstance(exp.get("responsibilities"), list) else [exp.get("responsibilities") or ""]), key=f"res_{i}", height=80)

        # update back to session_state
        st.session_state.experience[i]["job_title"] = exp_job
        st.session_state.experience[i]["company"] = exp_company
        st.session_state.experience[i]["start_date"] = exp_start
        st.session_state.experience[i]["end_date"] = exp_end
        st.session_state.experience[i]["location"] = exp_loc
        # store responsibilities as list
        st.session_state.experience[i]["responsibilities"] = [s.strip() for s in re.split(r",|\n", exp_desc) if s.strip()]

    st.markdown("---")
    st.subheader("Education")
    c3, c4 = st.columns([1,1])
    if c3.button("➕ Add education"):
        st.session_state.education.append({
            "institution": "",
            "degree": "",
            "start_date": "",
            "end_date": "",
            "location": "",
            "note": ""
        })
    if c4.button("➖ Remove last education"):
        if st.session_state.education:
            st.session_state.education.pop()

    for i, edu in enumerate(st.session_state.education):
        st.markdown(f"**Education #{i+1}**")
        inst = st.text_input(f"Institution {i+1}", value=edu.get("institution",""), key=f"inst_{i}")
        deg = st.text_input(f"Degree {i+1}", value=edu.get("degree",""), key=f"deg_{i}")
        ed_start = st.text_input(f"Start (MM/YYYY) {i+1}", value=edu.get("start_date",""), key=f"edstart_{i}")
        ed_end = st.text_input(f"End (MM/YYYY) {i+1}", value=edu.get("end_date",""), key=f"edend_{i}")
        ed_loc = st.text_input(f"Location {i+1}", value=edu.get("location",""), key=f"edloc_{i}")
        note = st.text_area(f"Note {i+1}", value=edu.get("note",""), key=f"ednote_{i}", height=60)

        st.session_state.education[i]["institution"] = inst
        st.session_state.education[i]["degree"] = deg
        st.session_state.education[i]["start_date"] = ed_start
        st.session_state.education[i]["end_date"] = ed_end
        st.session_state.education[i]["location"] = ed_loc
        st.session_state.education[i]["note"] = note

with right_col:
    st.subheader("Skills, Languages & Job Description")
    skills_input = st.text_input("Skills (comma separated)", value=",".join(st.session_state.get("skills", [])))
    languages_input = st.text_input("Languages (comma separated)", value=",".join(st.session_state.get("languages", [])))
    job_description = st.text_area("Job Description (paste full job ad or leave empty)", value=st.session_state.get("job_description",""), height=200)

    # update session_state
    st.session_state.skills = [s.strip() for s in skills_input.split(",") if s.strip()]
    st.session_state.languages = [l.strip() for l in languages_input.split(",") if l.strip()]
    st.session_state.job_description = job_description

    st.markdown("---")
    st.subheader("Preview / Actions")

    # Show parsed resume text preview area
    if st.session_state.parsed_resume_text:
        st.info("Parsed resume text available (from uploaded file). You can still edit fields above before generating.")
        st.text_area("Parsed resume (raw)", value=st.session_state.parsed_resume_text, height=160)

    # Parse resume (uses existing generate endpoint to parse)
    if parse_button:
        if uploaded_file:
            st.session_state.parsed_resume_text = extract_text_from_file(uploaded_file)
            if not st.session_state.parsed_resume_text:
                st.warning("No text was extracted from the uploaded file.")
            else:
                # send parsed text to backend to extract structured fields
                with st.spinner("Parsing resume using Applify..."):
                    payload = {
                        "name": st.session_state.get("name",""),
                        "email": st.session_state.get("email",""),
                        "phone": st.session_state.get("phone",""),
                        "address": st.session_state.get("address",""),
                        "summary": st.session_state.get("summary",""),
                        "experience": st.session_state.experience,
                        "education": st.session_state.education,
                        "skills": st.session_state.get("skills", []),
                        "languages": st.session_state.get("languages", []),
                        "job_description": st.session_state.get("job_description",""),
                        "parsed_resume_text": st.session_state.parsed_resume_text,
                        # instruct backend to parse and return structured fields (non-final)
                        "parse_only": True,
                    }
                    try:
                        r = requests.post(API_URL, json=payload, timeout=60)
                        if r.status_code != 200:
                            st.error(f"Parsing failed: {r.text}")
                        else:
                            data = r.json()
                            # Expect backend to return parsed structure inside "parsed" or top-level fields
                            parsed = data.get("parsed") or data.get("parsed_payload") or data
                            st.session_state.parsed_payload = parsed
                            autofill_from_parsed(parsed)
                            st.success("Resume parsed and form auto-filled. Please review/edit fields before generating.")
                    except Exception as e:
                        st.error(f"Failed to call backend for parsing: {e}")

        else:
            st.warning("Please upload a PDF or DOCX file first to parse.")

    # Generate final CV & Cover Letter
    if generate_button_sidebar:
        # Build final payload from session state
        final_payload = {
            "name": name or st.session_state.get("name",""),
            "email": email or st.session_state.get("email",""),
            "phone": phone or st.session_state.get("phone",""),
            "address": address or st.session_state.get("address",""),
            "summary": summary or st.session_state.get("summary",""),
            "experience": st.session_state.experience,
            "education": st.session_state.education,
            "skills": st.session_state.get("skills", []),
            "languages": st.session_state.get("languages", []),
            "job_description": st.session_state.get("job_description",""),
            "parsed_resume_text": st.session_state.parsed_resume_text,
            "include_simple_version": True,
            "output_language": st.session_state.output_language,
            "want_pdf": want_pdf
        }
        with st.spinner("Generating CV and Cover Letter..."):
            try:
                r = requests.post(API_URL, json=final_payload, timeout=120)
                if r.status_code != 200:
                    st.error(f"Generation failed: {r.text}")
                else:
                    out = r.json()
                    # show outputs
                    st.success("Generation complete!")
                    st.subheader("CV Preview")
                    st.markdown(out.get("cv_text",""))
                    st.subheader("Cover Letter Preview")
                    st.markdown(out.get("cover_letter_text",""))

                    # downloads
                    if want_pdf and out.get("pdf_base64"):
                        pdf_bytes = base64.b64decode(out["pdf_base64"])
                        st.download_button("Download PDF", data=pdf_bytes, file_name="applify_output.pdf", mime="application/pdf")
                    if want_pdf and out.get("docx_base64"):
                        docx_bytes = base64.b64decode(out["docx_base64"])
                        st.download_button("Download DOCX", data=docx_bytes, file_name="applify_output.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            except Exception as e:
                st.error(f"Error while generating: {e}")

# Also allow generate from main area
if st.button("Generate (main)"):
    st.experimental_rerun()
