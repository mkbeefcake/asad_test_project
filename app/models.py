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


class ProcessedMessage(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "processed_messages"

	# Gmail message id to avoid duplicate processing
	gmail_message_id = db.Column(db.String(255), unique=True, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


class Order(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "orders"

	# Example fields for refund lookup
	order_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
	user_email = db.Column(db.String(255), nullable=False)
	status = db.Column(db.String(32), nullable=False, default="completed")
	refund_requested = db.Column(db.Boolean, default=False, nullable=False)


class RefundRequest(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "refund_requests"

	order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
	order_number = db.Column(db.String(64), nullable=True)
	requester_email = db.Column(db.String(255), nullable=False)
	status = db.Column(db.String(32), nullable=False, default="requested")
	conversation_thread_id = db.Column(db.String(255), nullable=True)


class NotFoundRefund(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "not_found_refunds"

	order_number = db.Column(db.String(64), nullable=True)
	requester_email = db.Column(db.String(255), nullable=False)
	reason = db.Column(db.String(255), nullable=True)
	conversation_thread_id = db.Column(db.String(255), nullable=True)


class UnhandledEmail(db.Model, TimestampMixin):  # type: ignore[arg-type]
	__tablename__ = "unhandled_emails"

	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
	subject = db.Column(db.Text, nullable=True)
	body_snippet = db.Column(db.Text, nullable=True)
	importance = db.Column(db.String(16), nullable=True)  # low/medium/high
	reason = db.Column(db.String(64), nullable=True)  # classification rationale

