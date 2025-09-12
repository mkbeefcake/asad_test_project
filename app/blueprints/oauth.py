from __future__ import annotations

from typing import Optional

from flask import Blueprint, current_app, jsonify, redirect, request, url_for

from app.extensions import db
from app.models import User, GmailToken
from app.services.google_oauth import (
	create_flow,
	exchange_code_for_tokens,
	fetch_userinfo,
)


bp = Blueprint("oauth", __name__, url_prefix="/oauth2")


@bp.get("/login")
def login():
	try:
		flow = create_flow()
		auth_url, state = flow.authorization_url(
			include_granted_scopes="false",
			access_type="offline",
			prompt="consent",
		)
		return redirect(auth_url)
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("OAuth login error: %s", exc)
		return jsonify({"error": "oauth_login_failed"}), 500


@bp.get("/callback")
def callback():
	code: Optional[str] = request.args.get("code")
	if not code:
		return jsonify({"error": "missing_code"}), 400
	try:
		tokens = exchange_code_for_tokens(code)
		access_token = tokens.get("access_token")
		refresh_token = tokens.get("refresh_token")
		expiry = tokens.get("expiry")
		scopes = tokens.get("scopes")
		token_type = tokens.get("token_type")

		# Fetch real user email via userinfo
		userinfo = fetch_userinfo(access_token or "")
		email = (userinfo.get("email") or request.args.get("email") or "").strip()
		if not email:
			return jsonify({"error": "email_not_found"}), 400

		user = User.query.filter_by(email=email).first()
		if not user:
			user = User(email=email)
			db.session.add(user)
			db.session.flush()

		# Upsert GmailToken
		token = GmailToken.query.filter_by(user_id=user.id).first()
		if not token:
			token = GmailToken(
				user_id=user.id,
				access_token=access_token,
				refresh_token=refresh_token or "",
				token_expiry=expiry,
				token_scope=",".join(scopes or []),
				token_type=token_type,
			)
			db.session.add(token)
		else:
			token.access_token = access_token
			if refresh_token:
				token.refresh_token = refresh_token
			token.token_expiry = expiry
			token.token_scope = ",".join(scopes or [])
			token.token_type = token_type

		try:
			db.session.commit()
		except Exception as db_exc:  # noqa: BLE001
			current_app.logger.error("DB commit failed: %s", db_exc)
			db.session.rollback()
			return jsonify({"error": "db_commit_failed"}), 500

		return jsonify({"ok": True, "user_id": user.id}), 200
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("OAuth callback error: %s", exc)
		return jsonify({"error": "oauth_callback_failed"}), 500

