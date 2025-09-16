from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from flask import current_app, url_for
import requests
import base64

try:
	from google_auth_oauthlib.flow import Flow
	from google.oauth2.credentials import Credentials
	from google.auth.transport.requests import Request
	from googleapiclient.discovery import build
except Exception:  # pragma: no cover - optional until packages installed
	Flow = None  # type: ignore
	Credentials = None  # type: ignore
	Request = None  # type: ignore
	build = None  # type: ignore


def _scopes() -> list[str]:
	return current_app.config.get("GOOGLE_SCOPES", [])


def create_flow(state: Optional[str] = None) -> Flow:
	"""Create OAuth 2.0 Flow for Google."""
	if Flow is None:
		raise RuntimeError("google-auth-oauthlib not installed")

	client_config = {
		"web": {
			"client_id": current_app.config.get("GOOGLE_CLIENT_ID"),
			"client_secret": current_app.config.get("GOOGLE_CLIENT_SECRET"),
			"auth_uri": "https://accounts.google.com/o/oauth2/auth",
			"token_uri": "https://oauth2.googleapis.com/token",
		}
	}

	redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI") or url_for(
		"oauth.callback", _external=True
	)

	flow = Flow.from_client_config(
		client_config,
		scopes=_scopes(),
		redirect_uri=redirect_uri,
	)
	return flow


def exchange_code_for_tokens(code: str) -> dict[str, Any]:
	flow = create_flow()
	flow.fetch_token(code=code)
	creds = flow.credentials
	return {
		"access_token": creds.token,
		"refresh_token": getattr(creds, "refresh_token", None),
		"expiry": creds.expiry,
		"scopes": creds.scopes,
		"token_type": creds.token_uri and "Bearer" or None,
	}


def fetch_userinfo(access_token: str) -> dict[str, Any]:
	"""Fetch userinfo (email, sub) using the access token.

	Tries OIDC userinfo first, then Google OAuth2 v2 as fallback.
	"""
	headers = {"Authorization": f"Bearer {access_token}"}
	endpoints = [
		"https://openidconnect.googleapis.com/v1/userinfo",
		"https://www.googleapis.com/oauth2/v2/userinfo",
	]
	for url in endpoints:
		try:
			resp = requests.get(url, headers=headers, timeout=10)
			if resp.ok:
				return resp.json()
		except Exception:  # noqa: BLE001
			continue
	return {}

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
def refresh_access_token(refresh_token: str) -> dict[str, Any]:
	if Credentials is None or Request is None:
		raise RuntimeError("google-auth not installed")

	creds = Credentials(
		None,
		refresh_token=refresh_token,
		client_id=current_app.config.get("GOOGLE_CLIENT_ID"),
		client_secret=current_app.config.get("GOOGLE_CLIENT_SECRET"),
		token_uri=GOOGLE_TOKEN_URI,
		scopes=_scopes(),
	)
	creds.refresh(Request())
	return {
		"access_token": creds.token,
		"expiry": creds.expiry,
	}


def build_gmail_service(access_token: str) -> Any:
	if build is None:
		raise RuntimeError("google-api-python-client not installed")
	creds = Credentials(access_token, scopes=_scopes())
	return build("gmail", "v1", credentials=creds, cache_discovery=False)


def watch_user_gmail(access_token: str):	
    service = build_gmail_service(access_token=access_token)
    request = {
        "topicName": "projects/PROJECT_ID/topics/gmail-updates"
    }
    response = service.users().watch(userId="me", body=request).execute()
    return response

def get_history(access_token, start_history_id):
    service = build_gmail_service(access_token=access_token)
    history = service.users().history().list(
        userId="me", startHistoryId=start_history_id
    ).execute()
    return history

def get_message_content(access_token, message_id):
    service = build_gmail_service(access_token=access_token)
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'  # options: 'minimal', 'full', 'metadata', 'raw'
    ).execute()
    
    # Extract payload
    payload = message.get('payload', {})
    headers = payload.get('headers', [])

    # Parse useful headers
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    from_ = next((h['value'] for h in headers if h['name'] == 'From'), '')
    
    # Extract body (handle multipart)
    body = ''
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    else:
        body_data = payload.get('body', {}).get('data')
        if body_data:
            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
    
    return {
        "subject": subject,
        "from": from_,
        "body": body
    }

def process_gmail_history(access_token, history):
	messages_array = []

	for record in history.get('history', []):
		# Only process new messages
		for added in record.get('messagesAdded', []):
			message_id = added['message']['id']
			content = get_message_content(access_token=access_token, message_id=message_id)
			messages_array.append(content)
			print("New email:", content['subject'], "from", content['from'])

	return messages_array