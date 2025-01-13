[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](https://forthebadge.com)[![forthebadge](https://forthebadge.com/images/badges/powered-by-coffee.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/uses-brains.svg)](https://forthebadge.com)

#                       OAuth2 Integration (using HubSpot)

A FastAPI + React demo that integrates with third-party service HubSpot. It demonstrates OAuth2.0 **Authorization Code Flow** (Generally the most secure approach), storing credentials in Redis, and performing basic data operations like listing items, CRUD actions.

## ⚡ Setup & Installation

### Option 1: Using Docker (You Will Like It!!)

1. Clone this repository:
   ```bash
   git clone git@github.com:si-abhay/Oauth2-Implementation.git
   cd Oauth2-Implementation
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```

   This will start:
   - Frontend on http://localhost:3000
   - Backend on http://localhost:8000
   - Redis on port 6379

### Option 2: Manual Setup

1. Clone this repository:
    ```bash
    git clone git@github.com:si-abhay/Oauth2-Implementation.git
    cd Oauth2-Implementation
    ```

2. Install Python dependencies (in a virtual environment if you wish):
    ```bash
    pip install -r requirements.txt
    ```

3. Set up Redis:
    ```bash
    redis-server
    ```

Ensure you have a Redis server running locally on default port 6379, or update the settings in `redis_client.py` to match your environment.

4. Run the FastAPI server (Backend):
    ```bash
    cd backend
    uvicorn main:app --reload
    ```

   This starts your API on [http://localhost:8000](http://localhost:8000).

5. Install & run the React frontend:
    ```bash
    cd frontend
    npm i
    npm run start
    ```

   This starts your React app on [http://localhost:3000](http://localhost:3000).


### OVERVIEW

1. Authorize a user via OAuth2 to HubSpot (and similarly Notion, Airtable).
2. Store OAuth tokens (including refresh tokens) in Redis.
3. Automatically refresh expired access tokens to avoid re-prompting users.
4. Load data from each service.
5. Perform CRUD actions on HubSpot contacts (create, retrieve, update, delete).

### OAuth Flow

Implemented the **Authorization Code Flow**, considered the most secure among OAuth 2.0 methods:

1. **Initiate** – The user clicks "Connect," opening a HubSpot (or Notion/Airtable) authorization screen in a pop-up.
2. **Consent** – The service prompts the user to grant permissions to our application.
3. **Redirect** – After approval, the user is sent back with a one-time **authorization code**.
4. **Exchange** – Our FastAPI backend exchanges that code for an **access token** and **refresh token**, securely storing them in **Redis**.
5. **Reuse & Refresh** – With tokens in Redis, the app can **automatically refresh** them when they expire, eliminating repeated prompts.  
6. **Access & CRUD** – Finally, the app uses valid tokens to perform **CRUD** operations (e.g., fetching contacts, creating records) in HubSpot or other integrated services.
###
This flow ensures minimal user hassle, more security (no credentials stored on the frontend), and smooth data retrieval/updates once authorization is granted.


### Features

- **FastAPI** backend:
  - Endpoints for OAuth **authorization**, **callback**, and retrieving **credentials**.
  - **Redis** for storing access/refresh tokens securely.
  - Automatic token **refresh** logic, so users don’t have to re-authenticate frequently.
  - Integration with **HubSpot**, **Notion**, **Airtable** for loading items and performing CRUD.
  - **Automatic re-login**: If tokens are missing or expired, the frontend detects it and redirects the user to re-authenticate.

- **React** frontend:
  - Simple forms for **User**, **Organization**, and **Integration Type**.
  - **Pop-up** OAuth flow (e.g., HubSpot) with post-auth retrieval of tokens.
  - **Load Data** features to fetch and display items from each service.
  - **CRUD** operations for HubSpot contacts (create, retrieve, update, delete).
  - **Auto-redirect** upon “No HubSpot credentials found”: If Redis no longer has stored tokens, the user is prompted and immediately taken back to the connect flow.

- Clean, modern **Material UI** layout:
  - **Two-column** view (DataForm on the left, ContactForm on the right) for HubSpot.
  - Clear buttons to reset fields, making the user experience straightforward.

- **Docker** containerization:
  - **Multi-container** setup with Docker Compose
  - Separate containers for **Frontend**, **Backend**, and **Redis**
  - **Hot-reload** enabled for both frontend and backend development
  - **Volume mounting** for real-time code changes
  - **Environment variables** configured for service communication
  - **Single command** to start all services (`docker-compose up --build`)
  - To rebuild containers (remove and build from scratch) `docker-compose down`
  - **Isolated environments** ensuring consistent development experience

## ⚡ Technologies


![Python](https://img.shields.io/badge/-Python-black?style=flat-square&logo=Python)
![JavaScript](https://img.shields.io/badge/-JavaScript-black?style=flat-square&logo=javascript)
![HubSpot](https://img.shields.io/badge/-HubSpot-563D7C?style=flat-square&logo=)
![OAuth 2.0](https://img.shields.io/badge/-OAuth2.0-A9A9A9?style=flat-square&logo=OAuth)
![Git](https://img.shields.io/badge/-Git-black?style=flat-square&logo=git)
![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github)
![Docker](https://img.shields.io/badge/-Docker-black?style=flat-square&logo=Docker)
![HTML5](https://img.shields.io/badge/-HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/-CSS3-1572B6?style=flat-square&logo=css3)


### ONE WEIRD THING
In **DELETE**, there is a **weird** behavior shown by HubSpot: even if the provided contact ID does **not exist**, it returns a **204** (no content) instead of returning **404**! Thus, the UI sees “successfully deleted” even for random IDs. Workaround which I implemented is to **GET** the contact first if you truly want to validate its existence before deleting.

Of course:
[![forthebadge](https://forthebadge.com/images/badges/not-a-bug-a-feature.svg)](https://forthebadge.com)

[My LinkedIn](https://www.linkedin.com/in/abhay3104/)

[![coffee](https://forthebadge.com/images/badges/powered-by-coders-sweat.svg)](https://forthebadge.com)
