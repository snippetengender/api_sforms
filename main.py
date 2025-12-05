from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from os import getenv
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from models.models_for_sforms import CreateFormResponse, CreateFormRequest, SubmitResponseRequest, SlugCreationRequest
from db_utils.db_handler import DBHandler, init_db, close_db
from sform_utils.slug_creator import SlugCreator
from models.models_for_auth import GoogleLoginRequest
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

cred = credentials.Certificate("prod_config.json")
firebase_admin.initialize_app(cred)


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)


BASE_URL = getenv('BASE_URL')

forms_db = DBHandler(getenv('FORMS_COLLECTION'))
responses_db = DBHandler(getenv('RESPONSES_COLLECTION'))
users_db = DBHandler(getenv('USERS_COLLECTION'))

slug_creator = SlugCreator(forms_db)

@app.post("/forms", response_model=CreateFormResponse)
def create_form(payload: CreateFormRequest):
    if not payload.form_id:
        payload.form_id = str(uuid.uuid4())

    if not payload.form_slug:
        payload.form_slug = slug_creator.generate_unique_slug(payload.form_name)

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

@app.post("/forms/create-slug")
async def create_form_slug(request: SlugCreationRequest):
    if not request:
        raise HTTPException(status_code=400, detail="Form name is required")

    slug = slug_creator.generate_unique_slug(request.form_title)
    return {"form_slug": slug}

@app.post("/forms/auth/login")
async def user_login(payload: GoogleLoginRequest):
    try:
        # Step 1: Verify Firebase token
        decoded_token = firebase_auth.verify_id_token(payload.id_token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        picture = decoded_token.get("picture")

        user_data = {
            "uid": uid,
            "email": email,
            "name": name,
            "picture": picture,
            "last_login": datetime.now()
        }

        existing_user = users_db.find_document({"uid": uid})

        if existing_user:
            users_db.update_document({"uid": uid}, user_data)
        else:
            user_data["created_at"] = datetime.now()
            users_db.insert_document(user_data)

        return {
            "success": True,
            "message": f"User {name} authenticated",
            "uid": uid,
        }

    except Exception as e:
        print("Login error:", e)
        return {"success": False, "error": "Invalid ID token"}

@app.get("/forms/{form_slug}")
def get_form_by_slug(form_slug: str):
    form = forms_db.find_document({"form_slug": form_slug})

    if "_id" in form:
        form.pop("_id")

    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    form["created_at"] = str(form.get("created_at"))
    form["updated_at"] = str(form.get("updated_at"))

    return form


@app.post("/forms/submit-response")
def submit_response(payload: SubmitResponseRequest):
    form = forms_db.find_document({"form_slug": payload.form_slug})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    now = datetime.now()

    response_data = {
        "form_slug": payload.form_slug,
        "form_id": form["form_id"],
        "response": payload.response,
        "submitted_at": now
    }

    responses_db.insert_document(response_data)

    return {
        "success": True,
        "message": "Response saved successfully",
        "submitted_at": now
    }

@app.get("/forms/{form_slug}/responses")
def get_form_responses(form_slug: str):

    responses = responses_db.find_documents({"form_slug": form_slug})

    for response in responses:
        if "_id" in response:
            response.pop("_id")
        response["submitted_at"] = str(response.get("submitted_at"))

    return {
        "form_slug": form_slug,
        "responses": responses
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
