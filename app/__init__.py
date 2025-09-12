from flask import Flask
from .config import get_config
from .extensions import register_extensions, db
from .routes import register_routes


def create_app(config_name: str | None = None) -> Flask:
	"""Application factory for creating Flask app instances.

	Args:
		config_name: Optional configuration name (e.g., "development", "production").

	Returns:
		Configured Flask app instance.
	"""
	app = Flask(__name__, template_folder="../templates", static_folder="../static")

	# Load configuration
	config_object = get_config(config_name)
	app.config.from_object(config_object)

	# Register extensions (db, migrate, cache, etc.)
	register_extensions(app)

	# Register HTTP routes and blueprints
	register_routes(app)

	# Simple root route
	@app.get("/")
	def root():
		return {"status": "ok", "service": "asad_test_project"}, 200

	# Shell context for Flask CLI
	@app.shell_context_processor
	def make_shell_context():  # pragma: no cover - dev helper
		from . import models
		return {"db": db, "models": models}

	return app

