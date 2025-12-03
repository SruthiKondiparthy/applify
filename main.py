# api/main.py
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict
from api.schemas import CandidateInput
from api.ai_engine import AIEngine
from api.format_engine import render_cv_text, render_cover_letter_text
from api.utils import create_pdf_from_text, create_docx_from_text
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(title="Applify Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# instantiate AI engine
#ai = AIEngine(model=os.getenv("APPLIFY_MODEL"))
ai = AIEngine()

@app.post("/generate-resume", response_model=Dict[str, Any])
async def generate_resume(candidate: CandidateInput):
    """
    Generate CV + Cover Letter + Unterlagen Info
    """
    payload = candidate.model_dump() if hasattr(candidate, "model_dump") else candidate.dict()
    try:
        model_out = ai.generate_documents(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Extract expected fields from the model output
    cv_text = model_out.get("cv_text", "")
    cover_letter_text = model_out.get("cover_letter_text", "")
    unterlagen_info = model_out.get("unterlagen_info", "")
    cv_simple = model_out.get("cv_simple", "")
    cover_letter_simple = model_out.get("cover_letter_simple", "")

    # If model returned structured data for templating, render templates
    try:
        if isinstance(model_out.get("cv_data"), dict):
            cv_text = render_cv_text(model_out["cv_data"])
        if isinstance(model_out.get("cover_letter_data"), dict):
            cover_letter_text = render_cover_letter_text(model_out["cover_letter_data"])
    except Exception:
        # if rendering fails, continue: use text fields from model
        pass

    response = {
        "cv_text": cv_text,
        "cover_letter_text": cover_letter_text,
        "unterlagen_info": unterlagen_info,
        "cv_simple": cv_simple,
        "cover_letter_simple": cover_letter_simple,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    # Optionally return PDF/DOCX if requested by client; to keep payload small we provide endpoints for downloads.
    if candidate.want_pdf:
        try:
            pdf_bytes = create_pdf_from_text(f"Lebenslauf - {candidate.name}", cv_text + "\n\n" + cover_letter_text)
            docx_bytes = create_docx_from_text(f"Lebenslauf - {candidate.name}", cv_text + "\n\n" + cover_letter_text)
            # In this simple implementation we return base64 representations (or you can return presigned urls)
            import base64
            response["pdf_base64"] = base64.b64encode(pdf_bytes).decode("utf-8")
            response["docx_base64"] = base64.b64encode(docx_bytes).decode("utf-8")
        except Exception as e:
            # Do not fail the whole request for PDF errors
            response["pdf_error"] = str(e)

    return response

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
