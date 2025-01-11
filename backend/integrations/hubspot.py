import os
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import time
from typing import Optional, Union

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

BASE_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

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
    Handle the OAuth2 callback from HubSpot:
        - validate 'state'
        - exchange 'code' for access_token + refresh_token
        - store tokens with expiration info in Redis
        - close the popup
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
    # Could have implemented by passing parameter 'expire' in 'add_key_value_redis'
    # But, I wanted to use 'delete_key_redis' as well! :)
    await delete_key_redis(f"hubspot_state:{state}")

    state_data = json.loads(saved_state)
    user_id = state_data["user_id"]
    org_id = state_data["org_id"]

    # Exchange code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }

    tokens = await hubspot_exchange_for_tokens(token_data)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange code for access token.")

    # Save tokens in Redis
    await store_tokens_in_redis(org_id, user_id, tokens)

    # Return a script that closes the popup
    return HTMLResponse("<script>window.close()</script>", status_code=200)

async def get_hubspot_credentials(user_id: str, org_id: str) -> dict:
    """
    Fetch stored tokens from Redis if they exist.
    Raise HTTPException(400) if missing.
    """
    key = f"hubspot_credentials:{org_id}:{user_id}"
    stored = await get_value_redis(key)
    if not stored:
        # Here user needs to login again, as we don't have any stored tokens
        # Because with time, tokens are cleared from Redis
        raise HTTPException(
            status_code=400,
            detail=f"No HubSpot credentials found for org={org_id}, user={user_id}.\nPlease refresh and Login again."
        )
    return json.loads(stored)

async def get_valid_hubspot_access_token(org_id: str, user_id: str) -> str:
    """
    Ensure we have a valid (non-expired) access token for the given org/user.
    If expired or near expiry then refresh it.
    Returns the valid access token.
    """
    # Loading stored tokens
    credentials = await get_hubspot_credentials(user_id, org_id)
    access_token = credentials.get("access_token")
    refresh_token = credentials.get("refresh_token")

    # We also stored custom 'expires_at' time in func 'store_tokens_in_redis'
    # if you remember! :)
    expires_at = credentials.get("expires_at_utc")
    if not expires_at:
        # If we have no expires_at then a fallback to just returning the token.
        return await refresh_access_token(org_id, user_id, refresh_token)

    now_utc = int(time.time())
    # If the token expires in next ~30 seconds, refresh it!
    # Isn't this cool? We can refresh the token before it expires! :)
    if now_utc > (expires_at - 30):
        return await refresh_access_token(org_id, user_id, refresh_token)

    # Otherwise, it's still good
    return access_token

async def refresh_access_token(org_id: str, user_id: str, refresh_token: str) -> str:
    """
    Use the stored refresh_token to get a new access_token from HubSpot.
    Store the new tokens in Redis. Return the new access_token.
    """
    print(f"[REFRESH] Attempting to refresh token for org={org_id}, user={user_id}")
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh_token available to refresh access token."
        )

    token_data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
    }

    new_tokens = await hubspot_exchange_for_tokens(token_data)
    if not new_tokens:
        raise HTTPException(
            status_code=400,
            detail="Failed to refresh HubSpot access token."
        )

    # Store updated tokens
    await store_tokens_in_redis(org_id, user_id, new_tokens)

    return new_tokens["access_token"]

async def hubspot_exchange_for_tokens(token_data: dict) -> dict:
    """
    Helper function to call HubSpotfor both 'authorization_code' and 'refresh_token' flows.
    Returns the JSON token payload, or None if error.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if resp.status_code != 200:
            return None
        return resp.json()

async def store_tokens_in_redis(org_id: str, user_id: str, tokens: dict):
    """
    Store 'access_token', 'refresh_token', 'expires_in' from HubSpot
    in Redis and a custom 'expires_at_utc' for easy checking.
    """
    expires_in = tokens.get("expires_in", 600)  # fallback 10 mins if missing
    expires_in = 60  # Forcing a super short TTL for testing the automatic silent refresh in BG

    now_utc = int(time.time())
    expires_at_utc = now_utc + expires_in

    new_payload = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": expires_in,
        "expires_at_utc": expires_at_utc,
        "token_type": tokens.get("token_type", "bearer"),
        "scope": tokens.get("scope"),
    }

    key = f"hubspot_credentials:{org_id}:{user_id}"
    await add_key_value_redis(key, json.dumps(new_payload), expire=expires_in + 120)
    # We set Redis key to expire a bit after the token actually expires

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
        # Somethng is better than nothing, right? :)
        name=response_json.get("properties", {}).get("firstname"), 
        email=response_json.get("properties", {}).get("email", ""),
        last_name=response_json.get("properties", {}).get("lastname", ""),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
        creation_time=response_json.get("createdAt"),
        last_modified_time=response_json.get("updatedAt"),
    )

async def get_items_hubspot(credentials_or_str: Union[dict, str]) -> list:
    """
    Fetch contacts from HubSpot using the provided credentials.
    Return a list of IntegrationItem objects.
    """

    if isinstance(credentials_or_str, str):
        credentials = json.loads(credentials_or_str)
    else:
        credentials = credentials_or_str

    user_id = credentials.get("user_id")
    org_id = credentials.get("org_id")

    if not user_id or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Missing 'user_id' or 'org_id' to fetch HubSpot data."
        )

    # First ensure we have valid (non-expired) token
    access_token = await get_valid_hubspot_access_token(org_id, user_id)

    # Then fetch contacts from HubSpot
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            BASE_URL,
            headers=headers
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch HubSpot contacts. Maybe invalid/expired token."     # Maybe!! Hmmmm :(
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


async def get_contact(org_id: str, user_id: str, contact_id: str) -> dict:
    """
    Retrieve a single contact by ID.
    """
    access_token = await get_valid_hubspot_access_token(org_id, user_id)
    url = f"{BASE_URL}/{contact_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"Contact {contact_id} does not exist or is already deleted."
        )
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to retrieve HubSpot contact {contact_id}. {response.text}"
        )


async def create_contact(org_id: str, user_id: str, properties: dict):
    """
    Create a new contact. `properties` is a dict like:
      {
        "email": "jonedoe@hubspot.com",
        "firstname": "Jone",
        "lastname": "Doe (Sample Contact)"
      }
    """
    access_token = await get_valid_hubspot_access_token(org_id, user_id)
    url = BASE_URL
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"properties": properties}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create HubSpot contact. {response.text}"
        )


async def update_contact(org_id: str, user_id: str, contact_id: str, properties: dict):
    """
    Update an existing contact. `properties` is a dict like:
      {
        "email": "newemail@hubspot.com",
        "firstname": "NewName"
      }
    """
    access_token = await get_valid_hubspot_access_token(org_id, user_id)
    url = f"{BASE_URL}/{contact_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"properties": properties}

    async with httpx.AsyncClient() as client:
        response = await client.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update HubSpot contact {contact_id}. {response.text}"
        )


async def delete_contact(org_id: str, user_id: str, contact_id: str):
    """
    Delete a contact by ID.
    """
    access_token = await get_valid_hubspot_access_token(org_id, user_id)
    url = f"{BASE_URL}/{contact_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers)

    if response.status_code == 204:
        return {"message": f"Contact {contact_id} successfully deleted."}
    # HubSpot returns 204 even if the contact is already deleted or doesn't exist
    # So, though I tried to handle 404 separately
    # But, it's not working and any random ID when deleting
    # says successfully deleted. I TRIED!! :)
    elif response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"Contact {contact_id} does not exist or is already deleted."
        )
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to delete HubSpot contact {contact_id}. {response.text}"
        )