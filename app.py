from app import create_app
from app.tasks.gmail import sync_user_gmail

app = create_app()
with app.app_context():
	sync_user_gmail(user_id=3, max_results=2)


if __name__ == "__main__":
	# For local development only. In production, use Gunicorn.
	app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

