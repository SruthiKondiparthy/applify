# tests/test_ai_engine.py

import json
import sys
from pathlib import Path

# Add repo root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from api.ai_engine import AIEngine

def main():
    # Initialize the AIEngine
    engine = AIEngine()

    # Dummy candidate payload
    candidate_payload = {
        "name": "Max Mustermann",
        "email": "max.mustermann@example.com",
        "phone": "+49 123 456789",
        "education": "M.Sc. in Computer Science, TU Berlin",
        "experience": "3 years as Software Engineer at Example GmbH",
        "skills": ["Python", "FastAPI", "Streamlit", "Machine Learning"],
        "languages": ["German", "English"],
        "want_pdf": False
    }

    try:
        result = engine.generate_documents(candidate_payload)
        print("✅ generate_documents output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print("❌ Error during document generation:")
        print(str(e))


if __name__ == "__main__":
    main()
