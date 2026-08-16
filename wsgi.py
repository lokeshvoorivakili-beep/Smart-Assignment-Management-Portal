"""
WSGI Entrypoint for Production Deployment (Gunicorn / Waitress / Nginx)
"""
from app import app

if __name__ == "__main__":
    app.run()
