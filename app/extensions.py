from __future__ import annotations

from typing import Any

from flask import Flask

try:
	from flask_sqlalchemy import SQLAlchemy
except Exception:  # pragma: no cover - optional until DB task
	SQLAlchemy = None  # type: ignore

try:
	from flask_migrate import Migrate
except Exception:  # pragma: no cover - optional until DB task
	Migrate = None  # type: ignore


db = SQLAlchemy() if SQLAlchemy else None  # lazy placeholder until installed
migrate = Migrate() if Migrate else None


def register_extensions(app: Flask) -> None:
	"""Register Flask extensions safely with error handling."""
	# Initialize SQLAlchemy
	if db is not None:
		try:
			db.init_app(app)
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Failed to init SQLAlchemy: %s", exc)

	# Initialize Flask-Migrate
	if migrate is not None and db is not None:
		try:
			migrate.init_app(app, db)
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Failed to init Flask-Migrate: %s", exc)

