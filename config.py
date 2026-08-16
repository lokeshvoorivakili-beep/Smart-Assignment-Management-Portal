import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'smart_assignment_portal_secret_key_default')
    
    # MySQL / MariaDB Connection Parameters
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'smart_assignment_portal')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    
    # SQLite Fallback Path
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'database', 'smart_assignment_portal.db')
    
    # Upload Settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 20 * 1024 * 1024)) # 20MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv('UPLOAD_FOLDER', 'uploads'))
    ASSIGNMENT_UPLOADS = os.path.join(UPLOAD_FOLDER, 'assignments')
    SUBMISSION_UPLOADS = os.path.join(UPLOAD_FOLDER, 'submissions')
    
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'rtf', 'png', 'jpg', 'jpeg', 'svg', 'gif', 'zip', 'rar', '7z', 'py', 'java', 'cpp', 'c', 'html', 'css', 'js'}
    SIMILARITY_THRESHOLD = 70.0 # Percentage threshold for similarity alerts
