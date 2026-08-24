# Phase 5: Production Deployment & Polish

This is the final phase of the project! We will upgrade our development-level tools to a production-ready stack suitable for deployment on an AWS EC2 instance using Docker. We will also secure the backend and polish the Chrome Extension UI.

## User Review Required

> [!IMPORTANT]
> **Extension Configuration:** To deploy the backend to AWS EC2, the Chrome extension needs to know the IP address or domain of your EC2 instance, and it needs to send an authentication token to prevent unauthorized usage of your AI credits.
> 
> **Proposed Solution:** I will create a clean "Options" page for the Chrome extension where you can specify both the `Backend Server URL` (e.g., `ws://<your-ec2-ip>:8000`) and your `Secret Auth Token`. Is this acceptable?

## Proposed Changes

### 1. Docker Containerization (Deployment Level)

To deploy cleanly on AWS EC2, we will use Docker to spin up the entire production stack (App + Postgres + Redis + Qdrant) with a single command.

#### [NEW] `backend/Dockerfile`
- Create an optimized, production-ready Python 3.11+ image.
- Install dependencies and expose port 8000.
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

#### [NEW] `docker-compose.yml`
- Service `backend`: The FastAPI application.
- Service `postgres`: Production database replacing SQLite.
- Service `redis`: Production cache and rate-limiter replacing `MemoryStore`.
- Service `qdrant`: Production vector store replacing in-memory Qdrant.

### 2. Backend Upgrades (Production Readiness)

#### [MODIFY] `backend/app/config.py` & `backend/.env.example`
- Add `server_auth_token` configuration.
- Ensure the config intelligently falls back to local sqlite/memory defaults if running locally, but uses the Docker URLs when running in production.

#### [MODIFY] `backend/app/schemas.py` & `backend/app/websocket/router.py`
- Add `auth_token` to `CoachRequest`.
- Update the WebSocket router to reject requests (with an "Unauthorized" error message) if the token doesn't match the `.env` value.

### 3. Extension Upgrades (Dynamic Config & UI Polish)

#### [NEW] `extension/src/options/`
- Create a simple Vite+React Options page for the Chrome extension.
- Allow the user to input and save their `BACKEND_URL` and `SERVER_AUTH_TOKEN` in `chrome.storage.local`.

#### [MODIFY] `extension/src/content/wsClient.js`
- Remove the hardcoded `ws://localhost:8000` and read the `BACKEND_URL` and `auth_token` from `chrome.storage.local`. Include the token in the WebSocket payloads.
- Improve error handling: if the backend is down, show a clear message in the UI ("Backend offline. Please start the server.") instead of just failing silently.

#### [MODIFY] `extension/src/panel/components/ResponseDisplay.jsx`
- Add a smooth auto-scroll to the bottom of the response as new tokens stream in, so you don't have to manually scroll when the AI writes long hints.

## Verification Plan

### Automated Tests
- Update `test_websocket.py` to include the `auth_token` in its test requests and verify that requests *without* the token are properly rejected.

### Manual Verification
- Install the updated extension, open the Options page, set a mock IP and token.
- Test that the panel correctly attempts to connect using the configured URL.
- Test `docker-compose up --build` to ensure the containers start correctly and connect to the robust DB/Redis infrastructure.
