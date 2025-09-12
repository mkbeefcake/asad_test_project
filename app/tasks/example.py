from __future__ import annotations

import time

from celery import shared_task
from app.celery_app import celery  # ensure Celery app is configured/eager


@shared_task(bind=True, name="example.add")
def add(self, x: int, y: int) -> int:  # noqa: D401 - trivial
	"""Add two numbers with a tiny delay to simulate work."""
	try:
		time.sleep(1)
		return x + y
	except Exception as exc:  # noqa: BLE001
		self.retry(exc=exc, countdown=2, max_retries=1)
		return 0

