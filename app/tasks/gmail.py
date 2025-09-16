from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from flask import current_app

from app.extensions import db
from app.models import GmailToken
from app.services.google_oauth import build_gmail_service, refresh_access_token

def _needs_refresh(expiry: datetime | None) -> bool:
    if not expiry:
        return False
    if expiry.tzinfo is None:  # make naive datetime UTC
        expiry = expiry.replace(tzinfo=timezone.utc)
    return expiry <= datetime.now(timezone.utc)


@shared_task(bind=True, name="gmail.sync_user")
def sync_user_gmail(self, user_id: int, max_results: int = 10) -> dict[str, Any]:
	"""Fetch a user's recent Gmail message IDs, refreshing token if needed."""
	try:
		token = GmailToken.query.filter_by(user_id=user_id).first()
		if not token:
			return {"ok": False, "error": "no_token"}

		# Refresh access token if expired
		if _needs_refresh(token.token_expiry):
			try:
				res = refresh_access_token(token.refresh_token)
				token.access_token = res.get("access_token") or token.access_token
				token.token_expiry = res.get("expiry") or token.token_expiry
				db.session.commit()
			except Exception as exc:  # noqa: BLE001
				current_app.logger.error("Token refresh failed for user %s: %s", user_id, exc)
				return {"ok": False, "error": "refresh_failed"}

		# Build Gmail client and fetch messages
		service = build_gmail_service(token.access_token)
		resp = (
			service.users()
			.messages()
			.list(userId="me", maxResults=max_results, q="is:unread")
			.execute()
		)

		messages = []
		for msg in resp.get("messages", []):
			msg_id = msg.get("id")
			msg_detail = service.users().messages().get(userId="me", id=msg_id, format="metadata", metadataHeaders=["From","Subject"]).execute()
			headers = {h["name"]: h["value"] for h in msg_detail.get("payload", {}).get("headers", [])}
			messages.append({
                "id": msg_id,
                "from": headers.get("From"),
                "subject": headers.get("Subject"),
                "snippet": msg_detail.get("snippet")
			})

		return {"ok": True, "count": len(messages), "message_ids": messages}
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("Gmail sync error for user %s: %s", user_id, exc)
		raise
