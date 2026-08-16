import os
from flask import Blueprint, jsonify, send_from_directory
from db import DB
from config import Config

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/departments', methods=['GET'])
def get_public_departments():
    """Public API endpoint returning department dropdown list."""
    depts = DB.query("SELECT department_id, code, department_name FROM departments ORDER BY code ASC")
    return jsonify({'success': True, 'departments': depts})

@api_bp.route('/download/assignment/<filename>', methods=['GET'])
def download_assignment_file(filename):
    """Download instruction file attached to an assignment."""
    return send_from_directory(Config.ASSIGNMENT_UPLOADS, filename, as_attachment=True)

@api_bp.route('/download/submission/<filename>', methods=['GET'])
def download_submission_file(filename):
    """Download uploaded student submission file."""
    return send_from_directory(Config.SUBMISSION_UPLOADS, filename, as_attachment=True)
