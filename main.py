from fastapi import FastAPI
from contextlib import asynccontextmanager
from os import getenv
import uuid
from datetime import datetime
from dotenv import load_dotenv
from models.models_for_sforms import CreateFormResponse, CreateFormRequest
from db_utils.db_handler import DBHandler, init_db, close_db, get_collection
from sform_utils.slug_creator import slugify

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()

app = FastAPI(lifespan=lifespan)

BASE_URL = getenv('BASE_URL')

forms_db = DBHandler(getenv('FORMS_COLLECTION'))
responses_db = DBHandler(getenv('RESPONSES_COLLECTION'))
users_db = DBHandler(getenv('USERS_COLLECTION'))

@app.post("/forms", response_model=CreateFormResponse)
def create_form(payload: CreateFormRequest):
    if not payload.form_id:
        payload.form_id = str(uuid.uuid4())

    if not payload.form_slug:
        payload.form_slug = slugify(payload.form_name)

    now = datetime.now()
    forms_data = payload.model_dump()
    forms_data.update({
        "created_at": now,
        "updated_at": now
    })

    forms_db.insert_document(forms_data)

    edit_path = f"/forms/{payload.form_slug}"
    edit_url = f"{BASE_URL.rstrip('/')}{edit_path}" if BASE_URL else edit_path

    return CreateFormResponse(
        success=True,
        form_id = payload.form_id,
        form_slug=payload.form_slug,
        edit_url=edit_url,
        message="Form data saved in DB as draft",
        created_at=now
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)