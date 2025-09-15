from flask import Flask, render_template, request
from .blueprints.oauth import bp as oauth_bp
from .tasks.gmail import sync_user_gmail
from .services.llm import safe_openai_complete, safe_anthropic_complete, safe_groq_complete


def register_routes(app: Flask) -> None:
	@app.get("/health")
	def health() -> tuple[dict, int]:
		return {"ok": True}, 200

	# Register OAuth blueprint
	app.register_blueprint(oauth_bp)

	@app.post("/gmail/sync/<int:user_id>")
	def gmail_sync(user_id: int):
		try:
			res = sync_user_gmail.delay(user_id)
			# Eager mode returns result immediately; otherwise return task id
			if hasattr(res, "get"):
				try:
					data = res.get(timeout=30)
					return data, 200
				except Exception:  # noqa: BLE001
					return {"task_id": getattr(res, "id", None)}, 202
			return {"task_id": getattr(res, "id", None)}, 202
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Gmail sync trigger failed: %s", exc)
			return {"error": "sync_failed"}, 500

	@app.get("/ui")
	def ui():
		try:
			return render_template("index.html")
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Template render error: %s", exc)
			return {"error": "template_error"}, 500

	@app.post("/llm/openai")
	def llm_openai():
		try:
			payload = request.get_json(silent=True) or {}
			prompt = (payload.get("prompt") or "Say hello briefly.").strip()
			model = (payload.get("model") or "gpt-4o-mini").strip()
			text = safe_openai_complete(prompt, model=model)
			return {"text": text}, 200
		except Exception as exc:  # noqa: BLE001
			app.logger.error("OpenAI route error: %s", exc)
			return {"error": "openai_failed"}, 500

	@app.post("/llm/anthropic")
	def llm_anthropic():
		try:
			payload = request.get_json(silent=True) or {}
			prompt = (payload.get("prompt") or "Say hello briefly.").strip()
			model = (payload.get("model") or "claude-3-5-sonnet-20240620").strip()
			text = safe_anthropic_complete(prompt, model=model)
			return {"text": text}, 200
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Anthropic route error: %s", exc)
			return {"error": "anthropic_failed"}, 500

	@app.post("/llm/groq")
	def llm_groq():
		try:
			payload = request.get_json(silent=True) or {}
			prompt = (payload.get("prompt") or "Say hello briefly.").strip()
			text = safe_groq_complete(prompt)
			return {"text": text}, 200
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Groq route error: %s", exc)
			return {"error": "groq_failed"}, 500
