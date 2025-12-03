# tests/test_prompt_parsing.py
from api.ai_engine import load_system_prompt
def test_prompt_loads():
    s = load_system_prompt()
    assert "Applify" in s and "Lebenslauf" in s
