from __future__ import annotations

from datetime import datetime

from .extensions import db


class TimestampMixin:
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	updated_at = db.Column(
		db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
	)


class User(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "users"

	email = db.Column(db.String(255), unique=True, nullable=False)
	name = db.Column(db.String(255), nullable=True)

	tokens = db.relationship("GmailToken", backref="user", lazy=True)


class GmailToken(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "gmail_tokens"

	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
	access_token = db.Column(db.Text, nullable=False)
	refresh_token = db.Column(db.Text, nullable=False)
	token_expiry = db.Column(db.DateTime, nullable=True)
	token_scope = db.Column(db.Text, nullable=True)
	token_type = db.Column(db.String(50), nullable=True)

