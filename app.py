from app import create_app


app = create_app()


if __name__ == "__main__":
	# For local development only. In production, use Gunicorn.
	app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

