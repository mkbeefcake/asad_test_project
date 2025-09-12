from __future__ import annotations

import logging
from typing import Any

from celery import Celery

from . import create_app


def make_celery(flask_config_name: str | None = None) -> Celery:
	"""Create and configure Celery bound to the Flask app context."""
	flask_app = create_app(flask_config_name)

	broker_url = flask_app.config.get("CELERY_BROKER_URL")
	result_backend = flask_app.config.get("CELERY_RESULT_BACKEND")

	celery = Celery(
		flask_app.import_name,
		broker=broker_url,
		backend=result_backend,
		include=["app.tasks.example"],
	)

	# Propagate Flask config into Celery namespace if needed
	celery.conf.update(
		task_serializer="json",
		result_serializer="json",
		accept_content=["json"],
		task_track_started=True,
		task_time_limit=60 * 15,
	)

	# Dev-only eager mode support
	if flask_app.config.get("CELERY_TASK_ALWAYS_EAGER"):
		celery.conf.task_always_eager = True
		celery.conf.task_eager_propagates = True

	# Ensure tasks run within Flask app context
	TaskBase = celery.Task

	class ContextTask(TaskBase):
		abstract = True

		def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
			try:
				with flask_app.app_context():
					return TaskBase.__call__(self, *args, **kwargs)
			except Exception as exc:  # noqa: BLE001
				flask_app.logger.error("Celery task error: %s", exc)
				raise

	celery.Task = ContextTask  # type: ignore[assignment]
	return celery


# Create a default Celery instance for imports and eager mode usage
celery = make_celery()

# Worker entrypoint: `celery -A app.celery_app.celery worker --loglevel=info`

