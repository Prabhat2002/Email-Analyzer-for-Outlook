import requests
from datetime import datetime, timezone


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def fetch_emails(access_token: str, start_date: str, end_date: str) -> list[dict]:
    """
    Fetch emails from Outlook via Microsoft Graph API.
    start_date / end_date: 'YYYY-MM-DD'
    Returns list of normalized email dicts.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Build OData filter
    start_iso = f"{start_date}T00:00:00Z"
    end_iso   = f"{end_date}T23:59:59Z"

    params = {
        "$filter":  f"receivedDateTime ge {start_iso} and receivedDateTime le {end_iso}",
        "$orderby": "receivedDateTime desc",
        "$top":     100,
        "$select":  "id,subject,from,receivedDateTime,bodyPreview,body",
    }

    emails = []
    url = f"{GRAPH_BASE}/me/messages"

    while url:
        resp = requests.get(url, headers=headers, params=params if url == f"{GRAPH_BASE}/me/messages" else None)
        if resp.status_code != 200:
            break

        data = resp.json()
        for item in data.get("value", []):
            emails.append(_normalize(item))

        url = data.get("@odata.nextLink")  # pagination

    return emails


def _normalize(item: dict) -> dict:
    sender = item.get("from", {}).get("emailAddress", {})
    body   = item.get("body", {}).get("content", "") or item.get("bodyPreview", "")

    # Strip HTML tags roughly
    import re
    clean_body = re.sub(r"<[^>]+>", " ", body)
    clean_body = re.sub(r"\s+", " ", clean_body).strip()

    return {
        "id":            item.get("id", ""),
        "subject":       item.get("subject", "(No Subject)"),
        "sender_name":   sender.get("name", ""),
        "sender_email":  sender.get("address", ""),
        "received_at":   item.get("receivedDateTime", ""),
        "body_preview":  item.get("bodyPreview", "")[:500],
        "full_body":     clean_body[:3000],  # limit for AI
    }
