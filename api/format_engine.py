# api/format_engine.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(enabled_extensions=("j2",))
)

def render_cv_text(cv_data: Dict) -> str:
    template = env.get_template("german_resume_template.j2")
    return template.render(**cv_data)

def render_cover_letter_text(cl_data: Dict) -> str:
    template = env.get_template("german_cover_letter_template.j2")
    return template.render(**cl_data)
