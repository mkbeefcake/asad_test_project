asad_test_project (Flask backend)

Minimal Flask backend with:
- OAuth 2.0 Gmail login and token storage
- Postgres + SQLAlchemy + Alembic (Flask-Migrate)
- Celery tasks (dev eager mode; no broker required on Windows)
- Gmail sync task/endpoint
- LLM integrations (OpenAI, Anthropic)
- Dockerfile + VS Code debug configs

Quickstart (Windows PowerShell)

1) Create venv and install deps
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Set environment variables (see ENV_EXAMPLE.txt)
```
$env:FLASK_ENV="development"
$env:SECRET_KEY="change-me"
$env:DATABASE_URL="postgresql://postgres:rootroot@localhost/asad_db"
$env:GOOGLE_CLIENT_ID="..."
$env:GOOGLE_CLIENT_SECRET="..."
$env:GOOGLE_REDIRECT_URI="http://127.0.0.1:5000/oauth2/callback"
# Optional LLMs
$env:OPENAI_API_KEY="..."
$env:ANTHROPIC_API_KEY="..."
```

3) Initialize DB (Postgres)
```
$env:FLASK_APP="app:create_app"
flask db upgrade
```

4) Run the app
```
python app.py
# Opens at http://127.0.0.1:5000
```

OAuth (Gmail)
- Add your account as a Test user in Google OAuth consent screen while in Testing mode.
- Visit: http://127.0.0.1:5000/oauth2/login
- Callback stores tokens in DB and returns { ok: true, user_id }.

Gmail Sync
```
Invoke-RestMethod -Method Post http://127.0.0.1:5000/gmail/sync/1
```

Celery (dev eager mode)
- Tasks run synchronously in-process (no Redis required on Windows).
```
python -c "from app.tasks.example import add; print(add.delay(2,3).get())"
```

LLM Routes
```
Invoke-RestMethod -Method Post http://127.0.0.1:5000/llm/anthropic -ContentType 'application/json' -Body '{"prompt":"Say hello"}'
Invoke-RestMethod -Method Post http://127.0.0.1:5000/llm/openai -ContentType 'application/json' -Body '{"prompt":"Say hello"}'
```

Docker (optional)
```
docker build -t asad-app .
docker run -e PORT=8080 -p 8080:8080 --env-file ENV_EXAMPLE.txt asad-app
```

