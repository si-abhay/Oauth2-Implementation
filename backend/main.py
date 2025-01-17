import os
import json
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from integrations.airtable import (
    authorize_airtable,
    get_items_airtable,
    oauth2callback_airtable,
    get_airtable_credentials
)
from integrations.notion import (
    authorize_notion,
    get_items_notion,
    oauth2callback_notion,
    get_notion_credentials
)
from integrations.hubspot import (
    authorize_hubspot,
    get_hubspot_credentials,
    get_items_hubspot,
    oauth2callback_hubspot,
    get_contact,
    create_contact,
    update_contact,
    delete_contact
)

app = FastAPI()

# For production environments
# TO DO: configure these in ENV or other config
ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Ping": "Pong"}

# -----------------------
# Airtable
# -----------------------
@app.post("/integrations/airtable/authorize")
async def authorize_airtable_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    return await authorize_airtable(user_id, org_id)

@app.get("/integrations/airtable/oauth2callback")
async def oauth2callback_airtable_integration(request: Request):
    return await oauth2callback_airtable(request)

@app.post("/integrations/airtable/credentials")
async def get_airtable_credentials_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    return await get_airtable_credentials(user_id, org_id)

@app.post("/integrations/airtable/load")
async def get_airtable_items(credentials: str = Form(...)):
    """
    Called by the frontend to load Airtable data,
    passing raw JSON credentials in the 'credentials' form field.
    """
    return await get_items_airtable(credentials)

# -----------------------
# Notion
# -----------------------
@app.post("/integrations/notion/authorize")
async def authorize_notion_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    return await authorize_notion(user_id, org_id)

@app.get("/integrations/notion/oauth2callback")
async def oauth2callback_notion_integration(request: Request):
    return await oauth2callback_notion(request)

@app.post("/integrations/notion/credentials")
async def get_notion_credentials_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    return await get_notion_credentials(user_id, org_id)

@app.post("/integrations/notion/load")
async def get_notion_items(credentials: str = Form(...)):
    return await get_items_notion(credentials)

# -----------------------
# HubSpot
# -----------------------
@app.post("/integrations/hubspot/authorize")
async def authorize_hubspot_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """
    Returns the HubSpot authorization URL.
    """
    return await authorize_hubspot(user_id, org_id)

@app.get("/integrations/hubspot/oauth2callback")
async def oauth2callback_hubspot_integration(request: Request):
    return await oauth2callback_hubspot(request)

@app.post("/integrations/hubspot/credentials")
async def get_hubspot_credentials_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """
    Returns the credentials from Redis, if they exist, or raises an error.
    Also contains refresh_token, access_token etc.
    """
    return await get_hubspot_credentials(user_id, org_id)

@app.post("/integrations/hubspot/load")
async def load_hubspot_data_integration(credentials: str = Form(...)):
    """
    Expects a JSON string with at least: "user_id" and "org_id".
    Then calls get_items_hubspot, which auto-refreshes if needed.
    """
    return await get_items_hubspot(credentials)

@app.post("/integrations/hubspot/contact/get")
async def hubspot_get_contact(
    user_id: str = Form(...),
    org_id: str = Form(...),
    contact_id: str = Form(...)
):
    """
    Retrieve a single HubSpot contact by ID.
    """
    return await get_contact(org_id, user_id, contact_id)

@app.post("/integrations/hubspot/contact/create")
async def hubspot_create_contact(
    user_id: str = Form(...),
    org_id: str = Form(...),
    properties_str: str = Form(...),
):
    """
    Create a new contact with the given properties.
    `properties_str` is JSON, e.g.:
       {"email": "jonedoe@hubspot.com", "firstname": "Jone"}
    """
    try:
        props = json.loads(properties_str)
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'properties_str'.")

    return await create_contact(org_id, user_id, props)

@app.post("/integrations/hubspot/contact/update")
async def hubspot_update_contact(
    user_id: str = Form(...),
    org_id: str = Form(...),
    contact_id: str = Form(...),
    properties_str: str = Form(...),
):
    """
    Update an existing contact identified by `contact_id`.
    `properties_str` is JSON with the updated fields.
    """
    try:
        props = json.loads(properties_str)
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'properties_str'.")

    return await update_contact(org_id, user_id, contact_id, props)

@app.post("/integrations/hubspot/contact/delete")
async def hubspot_delete_contact(
    user_id: str = Form(...),
    org_id: str = Form(...),
    contact_id: str = Form(...)
):
    """
    Delete the HubSpot contact with the given contact_id.
    """
    return await delete_contact(org_id, user_id, contact_id)