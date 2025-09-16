from __future__ import annotations

from typing import Optional

from flask import Blueprint, current_app, jsonify, redirect, request, url_for, abort

from app.extensions import db
from app.models import User, GmailToken
from app.services.google_oauth import (
	create_flow,
	exchange_code_for_tokens,
	fetch_userinfo,
	watch_user_gmail,
	get_history,
	process_gmail_history
)

import base64
import json

# Active users storage (In production, use a database)
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

		# Create watch service for Pub/Sub
		watch_user_gmail(token.access_token)

		return redirect(url_for("ui"))
	except Exception as exc:  # noqa: BLE001
		current_app.logger.error("OAuth callback error: %s", exc)
		return jsonify({"error": "oauth_callback_failed"}), 500

@bp.route('/active-users')
def get_active_users():
    users_list = [
        {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        }
        for user in User.query.all()
    ]
    return jsonify({'users': users_list})

@bp.route('/logout/<user_id>', methods=['POST'])
def logout_user(user_id):
	try:
		user = User.query.get(user_id)
		if not user:
			print(f"No user found with id {user_id}")
			return jsonify({'success': False, 'message': 'User not found'})

		# If you don't have cascade delete, manually delete tokens first
		tokens = GmailToken.query.filter_by(user_id=user.id).all()
		for token in tokens:
			db.session.delete(token)

		db.session.delete(user)
		db.session.commit()
		return jsonify({'success': True})

	except Exception as e:
		return jsonify({'success': False, 'message': f'Error: {str(e)}'})
	

@bp.route("/pubsub/push", methods=["POST"])
def pubsub_push():
	envelope = request.get_json()
	if not envelope or "message" not in envelope:
		abort(400, "Invalid Pub/Sub message")

	pubsub_message = envelope["message"]

	# Decode base64 data
	data = pubsub_message.get("data")
	if not data:
		abort(400, "No data in Pub/Sub message")

	decoded_data = base64.b64decode(data).decode("utf-8")
	message_data = json.loads(decoded_data)

	# Gmail notification contains 'emailAddress' and 'historyId'
	email = message_data.get("emailAddress")
	history_id = message_data.get("historyId")

	if not email or not history_id:
		abort(400, "Missing emailAddress or historyId")

	# Fetch user's Gmail history
	user = User.query.filter_by(email=email).first()
	if not user:
		abort(400, "not found the user")

	token = GmailToken.query.filter_by(user_id=user.id).first()
	if not token:
		abort(400, "Not found the access token")
	
	access_token = token.access_token
	history = get_history(access_token=access_token, start_history_id=history_id)

	print(f"New Gmail history for {email}: {history}")
	new_messages = process_gmail_history(access_token=access_token, history=history)

	# Pass this to LLM

	# Always respond with 204 for Pub/Sub push
	return ("", 204)