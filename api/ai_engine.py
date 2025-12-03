# api/ai_engine.py

import os
import json
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from services.llm_service import hybrid_llm   # <-- NEW IMPORT (replaces OpenAI direct call)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "applify_super_prompt.txt"


def load_system_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


class AIEngine:
    """
    Uses the Applify Super Prompt to generate:
    - German CV
    - German Cover Letter
    - Unterlagen Info
    - Simple-language versions
    via JSON output.

    NOW uses hybrid LLM provider:
        1. Gemini 1.5 Flash (free)
        2. DeepSeek Chat (free/cheap)
        3. OpenAI (fallback)
    """
    def __init__(self, model: str = None):
        # Model is irrelevant now because hybrid engine chooses the best backend
        self.model = model
        self.system_prompt = load_system_prompt()

    def generate_documents(self, candidate_payload: Dict[str, Any], max_tokens: int = 3000) -> Dict[str, Any]:
        """
        Builds the prompt and sends it to the hybrid LLM engine.
        Expects a strict JSON object per Applify Super Prompt spec.
        """

        # Build user message as JSON
        user_json = json.dumps({"candidate": candidate_payload}, ensure_ascii=False)

        # Combine system + user into single prompt for Gemini/DeepSeek compatibility
        full_prompt = (
            self.system_prompt
            + "\n\nUSER_CANDIDATE_DATA:\n"
            + user_json
        )

        # Call LLM (Gemini → DeepSeek → OpenAI)
        try:
            raw_output = hybrid_llm(full_prompt)
        except Exception as e:
            raise RuntimeError(f"LLM engine error: {str(e)}")

        # Parse JSON output
        try:
            parsed = json.loads(raw_output)
        except Exception:
            # Try extracting JSON substring
            try:
                start = raw_output.index("{")
                end = raw_output.rindex("}") + 1
                parsed = json.loads(raw_output[start:end])
            except Exception as e:
                raise RuntimeError(
                    f"Failed to parse LLM output as JSON.\nRaw Output:\n{raw_output}"
                ) from e

        # Must be dict
        if not isinstance(parsed, dict):
            raise RuntimeError("Model output parsed but is not a JSON object.")

        return parsed
