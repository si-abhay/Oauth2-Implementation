import os
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# Best to read these from environment variables, A good practice which I have learnt! :)
CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID", "33895f84-1a6f-4eeb-99b6-9524cd678494")
CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET", "99f06fcb-ff8c-4fea-87c2-2c855a7e11d6")
REDIRECT_URI = os.getenv(
    "HUBSPOT_REDIRECT_URI",
    "http://localhost:8000/integrations/hubspot/oauth2callback"
)

AUTHORIZATION_URL = "https://app.hubspot.com/oauth/authorize"
TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
SCOPES = "crm.objects.contacts.read crm.objects.contacts.write oauth"

async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """
    Generate and return the HubSpot authorization URL.
    Stores 'state' in Redis to correlate the callback.
    """
    state = secrets.token_urlsafe(32)
    state_data = {
        "state": state,
        "user_id": user_id,
        "org_id": org_id,
    }
    # Store state with a short expiration
    await add_key_value_redis(f"hubspot_state:{state}", json.dumps(state_data), expire=600)

    auth_url = (
        f"{AUTHORIZATION_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&state={state}"
    )
    return auth_url

async def oauth2callback_hubspot(request: Request):
    """
    Handle the OAuth2 callback from HubSpot,
    exchange the 'code' for access tokens, store them in Redis.
    """
    if "error" in request.query_params:
        error_detail = request.query_params.get("error_description", "HubSpot OAuth error")
        raise HTTPException(status_code=400, detail=error_detail)

    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter.")

    saved_state = await get_value_redis(f"hubspot_state:{state}")
    if not saved_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state token.")

    # Cleaning up the state key (it's single-use), why not use a TTL? :(
    await delete_key_redis(f"hubspot_state:{state}")

    state_data = json.loads(saved_state)
    user_id = state_data["user_id"]
    org_id = state_data["org_id"]

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Failed to exchange code for access token."
        )

    tokens = response.json()

    # Store tokens in Redis
    # For real usage, consider also storing refresh_token and expiration metadata
    await add_key_value_redis(
        f"hubspot_credentials:{org_id}:{user_id}",
        json.dumps(tokens),
        expire=3600
    )

    # Return a script that closes the popup
    return HTMLResponse(
        content="<script>window.close()</script>",
        status_code=200
    )

async def get_hubspot_credentials(user_id: str, org_id: str) -> dict:
    """
    Retrieve HubSpot credentials from Redis for the given user/org.
    """
    key = f"hubspot_credentials:{org_id}:{user_id}"
    credentials = await get_value_redis(key)
    if not credentials:
        raise HTTPException(
            status_code=400,
            detail=f"No HubSpot credentials found for org={org_id}, user={user_id}."
        )
    return json.loads(credentials)

async def create_integration_item_metadata_object(
    response_json: dict,
    item_type: str,
    parent_id: str = None,
    parent_name: str = None
) -> IntegrationItem:
    """
    Build an IntegrationItem from a HubSpot contact record.
    """
    return IntegrationItem(
        id=response_json.get("id", "0000000"), # Default value if ID is missing!! :)
        # For contacts, let's default to "email" if "firstname" is missing
        # Somethng is better than nothing, right? :)
        name=response_json.get("properties", {}).get("firstname") 
             or response_json.get("properties", {}).get("email", ""),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
        creation_time=response_json.get("createdAt"),
        last_modified_time=response_json.get("updatedAt"),
    )

async def get_items_hubspot(credentials: dict) -> list:
    """
    Fetch contacts from HubSpot using the provided credentials.
    Return a list of IntegrationItem objects.
    """
    access_token = credentials["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers=headers
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch HubSpot contacts."
        )

    items = response.json().get("results", [])
    integration_items = []
    for item in items:
        integration_items.append(
            await create_integration_item_metadata_object(
                item, 
                item_type="Contact"
            )
        )

    return integration_items
