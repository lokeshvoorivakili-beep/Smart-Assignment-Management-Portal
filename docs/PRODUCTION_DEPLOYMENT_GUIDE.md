# Smart Assignment Management Portal — Production Deployment Guide

This guide outlines how to deploy the **Smart Assignment Management Portal (SAMP)** to a production environment.

---

## 1. Running Production Server Locally (Windows / Linux)

Instead of the Flask development server (`python app.py`), use **Waitress** (the recommended WSGI production server for Windows) or **Gunicorn** (for Linux).

### Running with Waitress (Windows):
```powershell
# Run production WSGI server on port 5000
waitress-serve --port=5000 wsgi:app
```

Expected Output:
```text
INFO:waitress:Serving on http://0.0.0.0:5000
```

### Running with Gunicorn (Linux / macOS):
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 wsgi:app
```

---

## 2. Public Cloud Deployment Options

### Option A: Deployment on Render (Free Tier Available)

1. **Create a Git Repository**:
   ```powershell
   git init
   git add .
   git commit -m "Deploy Smart Assignment Management Portal"
   ```
2. **Push to GitHub / GitLab**.
3. **Connect to Render**:
   - Log into [Render Dashboard](https://render.com/).
   - Click **New +** -> **Web Service**.
   - Select your GitHub repository.
4. **Configure Build Settings**:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
5. **Environment Variables**:
   Add the following in Render's Environment panel:
   - `SECRET_KEY`: `your_random_production_secret_key`
   - `MYSQL_HOST`: `your_production_mysql_host`
   - `MYSQL_USER`: `your_production_mysql_user`
   - `MYSQL_PASSWORD`: `your_production_mysql_password`
   - `MYSQL_DB`: `smart_assignment_portal`
6. Click **Create Web Service**. Your public live URL will be generated (e.g., `https://smart-assignment-portal.onrender.com`).

---

### Option B: Deployment on PythonAnywhere

1. Open [PythonAnywhere](https://www.pythonanywhere.com/).
2. Upload your project zip or `git clone` into bash console.
3. Create a Virtual Environment and install requirements:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 samp-env
   pip install -r requirements.txt
   ```
4. Go to **Web** tab -> **Add a new web app** -> Select **Flask**.
5. Set WSGI file path to point to your `wsgi.py`.
6. Reload the Web App.

---

## 3. Production Security Checklist

- [x] Password Hashing: All user credentials stored as bcrypt hashes.
- [x] File Sanitization: Uploaded files renamed with secure UUID prefixes.
- [x] Session Security: Secret keys loaded strictly from `.env` environment variables.
- [ ] Enable HTTPS / SSL Certificates on domain name.
- [ ] Set `DEBUG = False` in production environment.
