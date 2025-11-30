from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QuestionModel(BaseModel):
    id: str
    type: str
    label: str
    required: bool = False

class CreateFormRequest(BaseModel):
    created_by: str
    form_id: Optional[str] = None
    form_name: str
    questions: List[QuestionModel]
    status: str = "draft"
    form_slug: Optional[str] = None
    published_at: Optional[datetime] = None

class CreateFormResponse(BaseModel):
    success: bool
    form_id: str
    form_slug: str
    edit_url: str
    message: str
    created_at: datetime

class SubmitResponseRequest(BaseModel):
    form_slug: str
    response: str
