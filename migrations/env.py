from __future__ import annotations

import logging
import os
from logging.config import fileConfig

from alembic import context
from flask import current_app

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name and os.path.exists(config.config_file_name):
	fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")


def get_app_metadata():
	# Import app and models lazily to have app context
	from app import create_app
	flask_app = create_app()
	from app.extensions import db
	from app import models as _  # noqa: F401 - ensure models are imported
	return flask_app, db.metadata


def run_migrations_offline() -> None:
	"""Run migrations in 'offline' mode."""
	flask_app, metadata = get_app_metadata()
	with flask_app.app_context():
		url = flask_app.config.get("SQLALCHEMY_DATABASE_URI")
		context.configure(url=url, target_metadata=metadata, literal_binds=True)
		with context.begin_transaction():
			context.run_migrations()


def run_migrations_online() -> None:
	"""Run migrations in 'online' mode."""
	flask_app, metadata = get_app_metadata()
	with flask_app.app_context():
		from app.extensions import db
		connectable = db.engine
		with connectable.connect() as connection:
			context.configure(connection=connection, target_metadata=metadata)
			with context.begin_transaction():
				context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()

