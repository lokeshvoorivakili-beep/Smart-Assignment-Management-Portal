import os
from flask import Flask, render_template, session, redirect, url_for, jsonify
from config import Config
from db import init_db

# Initialize database tables and seed data
init_db()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(Config)

# Ensure upload directories exist
os.makedirs(Config.ASSIGNMENT_UPLOADS, exist_ok=True)
os.makedirs(Config.SUBMISSION_UPLOADS, exist_ok=True)

# Register Blueprints
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.faculty_routes import faculty_bp
from routes.admin_routes import admin_bp
from routes.api_routes import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(faculty_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

# ==========================================
# PAGE ROUTING (HTML Views)
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student-dashboard')
def student_dashboard_page():
    if session.get('user_role') != 'student':
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/faculty-dashboard')
def faculty_dashboard_page():
    if session.get('user_role') != 'faculty':
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/admin-dashboard')
def admin_dashboard_page():
    if session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    return render_template('index.html')

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Resource or endpoint not found.'}), 404

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'success': False, 'message': 'File size exceeds maximum 20MB upload limit.'}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'An unexpected server error occurred.'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("  Smart Assignment Management Portal Starting...")
    print("  Local URL: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
