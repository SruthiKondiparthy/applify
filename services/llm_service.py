import google.generativeai as genai
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Configure Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)


# ----------------------------------------------------
# GEMINI (primary)
# ----------------------------------------------------
def call_gemini(prompt: str):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("[Gemini failed]:", e)
        return None


# ----------------------------------------------------
# DEEPSEEK (fallback #1)
# ----------------------------------------------------
def call_deepseek(prompt: str):
    try:
        client = OpenAI(
            api_key=DEEPSEEK_KEY,
            base_url="https://api.deepseek.com"
        )
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message["content"]
    except Exception as e:
        print("[DeepSeek failed]:", e)
        return None


# ----------------------------------------------------
# OPENAI (fallback #2)
# ----------------------------------------------------
def call_openai(prompt: str):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message["content"]
    except Exception as e:
        print("[OpenAI failed]:", e)
        return None


# ----------------------------------------------------
# MASTER fallback engine
# ----------------------------------------------------
def hybrid_llm(prompt: str):
    # Try Gemini
    if GEMINI_KEY:
        response = call_gemini(prompt)
        if response:
            return response

    # Then DeepSeek
    if DEEPSEEK_KEY:
        response = call_deepseek(prompt)
        if response:
            return response

    # Then OpenAI
    if OPENAI_KEY:
        response = call_openai(prompt)
        if response:
            return response

    raise Exception("All LLM providers failed, check API keys or quota.")
