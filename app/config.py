import os


class BaseConfig:
	SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
	JSON_SORT_KEYS = False
	# Database URI will be set later when models are added
	SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///local.db")
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# Celery / Redis
	CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
	CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

	# OAuth / Gmail placeholders
	GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
	GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
	GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2/callback")
	GOOGLE_SCOPES = [
		"https://www.googleapis.com/auth/gmail.readonly",
		"https://www.googleapis.com/auth/userinfo.email",
		"openid",
	]

	# LLM API Keys
	OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
	ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class DevelopmentConfig(BaseConfig):
	DEBUG = True

	# Celery dev-only: run tasks inline without a broker/worker
	CELERY_TASK_ALWAYS_EAGER = True
	CELERY_BROKER_URL = "memory://"
	CELERY_RESULT_BACKEND = "cache+memory://"


class ProductionConfig(BaseConfig):
	DEBUG = False


def get_config(name: str | None):
	if (name or os.getenv("FLASK_ENV", "development")).lower().startswith("prod"):
		return ProductionConfig
	return DevelopmentConfig

