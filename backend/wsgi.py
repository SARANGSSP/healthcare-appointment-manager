"""
API process entrypoint.

Local:    python wsgi.py
Hosted:   gunicorn wsgi:app   (see render.yaml / Procfile)
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
