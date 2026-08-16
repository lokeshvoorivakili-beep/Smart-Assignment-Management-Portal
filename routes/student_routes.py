import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session, send_from_directory
from db import DB
from config import Config
from utils.auth_utils import login_required
from utils.file_utils import allowed_file, save_uploaded_file
from utils.similarity import compute_submission_similarity

student_bp = Blueprint('student', __name__)

def format_dt(val, fmt='%b %d, %I:%M %p'):
    if not val:
        return None
    if hasattr(val, 'strftime'):
        return val.strftime(fmt)
    if isinstance(val, str):
        try:
            dt_obj = datetime.strptime(val.split('.')[0], '%Y-%m-%d %H:%M:%S')
            return dt_obj.strftime(fmt)
        except Exception:
            return val
    return str(val)

@student_bp.route('/api/student/assignments', methods=['GET'])
@login_required(role='student')
def get_student_assignments():
    student_id = session['user_id']
    dept_id = session['department_id']
    year = session['year']
    section = session['section']

    # Retrieve assignments matching student's dept, year, section
    assignments = DB.query("""
        SELECT a.*, 
               f.first_name as faculty_first, f.last_name as faculty_last, f.faculty_code,
               d.code as dept_code,
               s.submission_id, s.submitted_at, s.marks, s.feedback, s.submission_status, s.similarity_score
        FROM assignments a
        JOIN faculty f ON a.faculty_id = f.faculty_id
        JOIN departments d ON a.department_id = d.department_id
        LEFT JOIN submissions s ON (a.assignment_id = s.assignment_id AND s.student_id = %s)
        WHERE a.department_id = %s AND a.year = %s AND a.section = %s
        ORDER BY a.deadline ASC
    """, (student_id, dept_id, year, section))

    now = datetime.now()
    result = []
    for a in assignments:
        # Check deadline
        deadline_dt = a['deadline']
        if isinstance(deadline_dt, str):
            try:
                deadline_dt = datetime.strptime(deadline_dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                deadline_dt = datetime.strptime(deadline_dt.split('.')[0], '%Y-%m-%d %H:%M:%S')

        is_open = now <= deadline_dt
        deadline_str = deadline_dt.strftime('%b %d, %I:%M %p')

        result.append({
            'assignment_id': a['assignment_id'],
            'subject': a['subject'],
            'title': a['title'],
            'description': a['description'],
            'faculty_name': f"{a['faculty_first']} {a['faculty_last']}",
            'dept_code': a['dept_code'],
            'year': a['year'],
            'section': a['section'],
            'maximum_marks': a['maximum_marks'],
            'deadline': deadline_str,
            'deadline_iso': deadline_dt.isoformat(),
            'is_open': is_open,
            'has_instruction_file': bool(a['instruction_file']),
            'instruction_file': a['instruction_file'],
            'submission': {
                'submitted': bool(a['submission_id']),
                'submission_id': a['submission_id'],
                'submitted_at': format_dt(a['submitted_at']),
                'status': a['submission_status'],
                'marks': a['marks'],
                'feedback': a['feedback']
            } if a['submission_id'] else None
        })

    return jsonify({'success': True, 'assignments': result})

@student_bp.route('/api/student/assignments/<int:assignment_id>', methods=['GET'])
@login_required(role='student')
def get_assignment_detail(assignment_id):
    student_id = session['user_id']
    assignment = DB.query("""
        SELECT a.*, 
               f.first_name as faculty_first, f.last_name as faculty_last,
               d.code as dept_code,
               s.submission_id, s.uploaded_file, s.original_filename, s.submitted_at, s.marks, s.feedback, s.submission_status
        FROM assignments a
        JOIN faculty f ON a.faculty_id = f.faculty_id
        JOIN departments d ON a.department_id = d.department_id
        LEFT JOIN submissions s ON (a.assignment_id = s.assignment_id AND s.student_id = %s)
        WHERE a.assignment_id = %s
    """, (student_id, assignment_id), one=True)

    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404

    now = datetime.now()
    deadline_dt = assignment['deadline']
    if isinstance(deadline_dt, str):
        try:
            deadline_dt = datetime.strptime(deadline_dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            deadline_dt = datetime.strptime(deadline_dt.split('.')[0], '%Y-%m-%d %H:%M:%S')

    is_open = now <= deadline_dt

    return jsonify({
        'success': True,
        'assignment': {
            'assignment_id': assignment['assignment_id'],
            'subject': assignment['subject'],
            'title': assignment['title'],
            'description': assignment['description'],
            'faculty_name': f"{assignment['faculty_first']} {assignment['faculty_last']}",
            'dept_code': assignment['dept_code'],
            'year': assignment['year'],
            'section': assignment['section'],
            'maximum_marks': assignment['maximum_marks'],
            'deadline': deadline_dt.strftime('%b %d, %I:%M %p'),
            'is_open': is_open,
            'instruction_file': assignment['instruction_file'],
            'submission': {
                'submission_id': assignment['submission_id'],
                'filename': assignment['original_filename'],
                'uploaded_file': assignment['uploaded_file'],
                'submitted_at': format_dt(assignment['submitted_at']),
                'status': assignment['submission_status'],
                'marks': assignment['marks'],
                'feedback': assignment['feedback']
            } if assignment['submission_id'] else None
        }
    })

@student_bp.route('/api/student/submit', methods=['POST'])
@login_required(role='student')
def submit_assignment():
    student_id = session['user_id']
    assignment_id = request.form.get('assignment_id')
    
    if not assignment_id:
        return jsonify({'success': False, 'message': 'Assignment ID is required.'}), 400

    assignment = DB.query("SELECT * FROM assignments WHERE assignment_id = %s", (assignment_id,), one=True)
    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404

    # Backend Deadline Check
    now = datetime.now()
    deadline_dt = assignment['deadline']
    if isinstance(deadline_dt, str):
        try:
            deadline_dt = datetime.strptime(deadline_dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            deadline_dt = datetime.strptime(deadline_dt.split('.')[0], '%Y-%m-%d %H:%M:%S')

    if now > deadline_dt:
        return jsonify({'success': False, 'message': 'Submission deadline has passed.'}), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No submission file uploaded.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Allowed formats: PDF, DOCX, TXT, PY, CPP, JAVA, ZIP.'}), 400

    # Save uploaded file securely
    unique_filename, original_filename = save_uploaded_file(file, Config.SUBMISSION_UPLOADS)
    saved_file_path = os.path.join(Config.SUBMISSION_UPLOADS, unique_filename)

    # Compute similarity score against existing submissions for the same assignment
    other_submissions = DB.query("""
        SELECT uploaded_file FROM submissions 
        WHERE assignment_id = %s AND student_id != %s
    """, (assignment_id, student_id))
    
    existing_paths = [os.path.join(Config.SUBMISSION_UPLOADS, s['uploaded_file']) for s in other_submissions]
    similarity_score = compute_submission_similarity(saved_file_path, existing_paths)

    submitted_at_str = now.strftime('%Y-%m-%d %H:%M:%S')

    # Check if student already submitted (Re-submission before deadline)
    existing_sub = DB.query("SELECT * FROM submissions WHERE assignment_id = %s AND student_id = %s",
                            (assignment_id, student_id), one=True)

    if existing_sub:
        # Update existing submission record
        DB.execute("""
            UPDATE submissions 
            SET uploaded_file = %s, original_filename = %s, submitted_at = %s, similarity_score = %s, submission_status = 'Submitted'
            WHERE submission_id = %s
        """, (unique_filename, original_filename, submitted_at_str, similarity_score, existing_sub['submission_id']))
        sub_id = existing_sub['submission_id']
        message = 'Assignment re-submitted successfully!'
    else:
        # Create new submission record
        sub_id = DB.execute("""
            INSERT INTO submissions (assignment_id, student_id, uploaded_file, original_filename, submitted_at, similarity_score, submission_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Submitted')
        """, (assignment_id, student_id, unique_filename, original_filename, submitted_at_str, similarity_score))
        message = 'Assignment submitted successfully!'

    # Log notification if high similarity detected
    if similarity_score >= Config.SIMILARITY_THRESHOLD:
        student_name = session.get('name', 'Student')
        DB.execute("""
            INSERT INTO notifications (user_role, user_id, title, message)
            VALUES (%s, %s, %s, %s)
        """, ('Faculty', assignment['faculty_id'], 'High Similarity Alert',
              f"Submission for '{assignment['title']}' by {student_name} has high similarity of {similarity_score}%."))

    # Log activity
    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Submission', session.get('name'), 'Student', f"Submitted assignment '{assignment['title']}' (Similarity: {similarity_score}%)"))

    return jsonify({
        'success': True,
        'message': message,
        'similarity_score': similarity_score,
        'submission_id': sub_id
    })

@student_bp.route('/api/student/grades', methods=['GET'])
@login_required(role='student')
def get_student_grades():
    student_id = session['user_id']
    
    graded_items = DB.query("""
        SELECT s.*, a.title as assignment_title, a.subject, a.maximum_marks,
               f.first_name as faculty_first, f.last_name as faculty_last
        FROM submissions s
        JOIN assignments a ON s.assignment_id = a.assignment_id
        JOIN faculty f ON a.faculty_id = f.faculty_id
        WHERE s.student_id = %s AND s.submission_status = 'Graded'
        ORDER BY s.graded_at DESC
    """, (student_id,))

    result = []
    for item in graded_items:
        result.append({
            'submission_id': item['submission_id'],
            'assignment_title': item['assignment_title'],
            'subject': item['subject'],
            'maximum_marks': item['maximum_marks'],
            'marks': item['marks'],
            'feedback': item['feedback'],
            'faculty_name': f"{item['faculty_first']} {item['faculty_last']}",
            'uploaded_file': item['uploaded_file'],
            'original_filename': item['original_filename'],
            'graded_at': format_dt(item['graded_at'], '%b %d, %Y') or 'Recently'
        })

    return jsonify({'success': True, 'grades': result})

@student_bp.route('/api/student/notifications', methods=['GET'])
@login_required(role='student')
def get_student_notifications():
    student_id = session['user_id']
    notifs = DB.query("""
        SELECT * FROM notifications 
        WHERE user_role = 'Student' AND (user_id IS NULL OR user_id = %s)
        ORDER BY created_at DESC LIMIT 10
    """, (student_id,))
    
    result = []
    for n in notifs:
        created_str = n['created_at'].strftime('%b %d, %I:%M %p') if isinstance(n['created_at'], datetime) else str(n['created_at'])
        result.append({
            'id': n['notification_id'],
            'title': n['title'],
            'message': n['message'],
            'is_read': bool(n['is_read']),
            'time': created_str
        })
        
    return jsonify({'success': True, 'notifications': result})
