from flask import Flask, render_template


def register_routes(app: Flask) -> None:
	@app.get("/health")
	def health() -> tuple[dict, int]:
		return {"ok": True}, 200

	@app.get("/ui")
	def ui():
		try:
			return render_template("index.html")
		except Exception as exc:  # noqa: BLE001
			app.logger.error("Template render error: %s", exc)
			return {"error": "template_error"}, 500

