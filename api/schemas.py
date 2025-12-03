# api/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any


class ExperienceItem(BaseModel):
    job_title: str
    company: str
    start_date: Optional[str] = None  # MM/YYYY recommended
    end_date: Optional[str] = None
    location: Optional[str] = None
    responsibilities: Optional[List[str]] = []


class EducationItem(BaseModel):
    institution: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None


class LanguageItem(BaseModel):
    language: str
    level: str  # e.g. A1-C2


class CandidateInput(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    address: Optional[str] = ""
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    summary: Optional[str] = ""
    skills: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    experience: Optional[List[ExperienceItem]] = []
    education: Optional[List[EducationItem]] = []
    languages: Optional[List[LanguageItem]] = []
    additional_info: Optional[str] = ""
    job_description: str = Field(..., description="Full text of the target job ad")
    include_simple_version: Optional[bool] = False
    want_pdf: Optional[bool] = False
