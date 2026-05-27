import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from msal import ConfidentialClientApplication
from streamlit import echo

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

SCOPES = ["Mail.Read", "User.Read"]


def _get_app():
    client_id     = os.getenv("MS_CLIENT_ID", "")
    client_secret = os.getenv("MS_CLIENT_SECRET", "")
    tenant_id     = os.getenv("MS_TENANT_ID", "common")
    authority     = f"https://login.microsoftonline.com/{tenant_id}"
    return ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )


def get_auth_url() -> str:
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")
    app = _get_app()
    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )


def exchange_code_for_token(code: str) -> str | None:
    redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")
    app = _get_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    if "access_token" in result:
        return result["access_token"]
    return None


def get_user_info(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return {}


