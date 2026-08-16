import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from db import DB
from config import Config
from utils.auth_utils import login_required
from utils.file_utils import allowed_file, save_uploaded_file

faculty_bp = Blueprint('faculty', __name__)

def format_dt(val, fmt='%b %d, %I:%M %p'):
    if not val:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime(fmt)
    if isinstance(val, str):
        try:
            dt_obj = datetime.strptime(val.split('.')[0], '%Y-%m-%d %H:%M:%S')
            return dt_obj.strftime(fmt)
        except Exception:
            return val
    return str(val)

@faculty_bp.route('/api/faculty/assignments', methods=['GET'])
@login_required(role='faculty')
def get_faculty_assignments():
    faculty_id = session['user_id']
    
    assignments = DB.query("""
        SELECT a.*, d.code as dept_code,
               COUNT(s.submission_id) as total_submissions,
               SUM(CASE WHEN s.submission_status = 'Graded' THEN 1 ELSE 0 END) as graded_count
        FROM assignments a
        JOIN departments d ON a.department_id = d.department_id
        LEFT JOIN submissions s ON a.assignment_id = s.assignment_id
        WHERE a.faculty_id = %s
        GROUP BY a.assignment_id
        ORDER BY a.created_at DESC
    """, (faculty_id,))

    now = datetime.now()
    result = []
    for a in assignments:
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
            'dept_code': a['dept_code'],
            'year': a['year'],
            'section': a['section'],
            'maximum_marks': a['maximum_marks'],
            'deadline': deadline_str,
            'is_open': is_open,
            'total_submissions': a['total_submissions'] or 0,
            'graded_count': int(a['graded_count'] or 0)
        })

    return jsonify({'success': True, 'assignments': result})

@faculty_bp.route('/api/faculty/assignments/create', methods=['POST'])
@login_required(role='faculty')
def create_assignment():
    faculty_id = session['user_id']
    data = request.form if request.form else (request.get_json() or {})

    department_id = data.get('department_id')
    year = data.get('year')
    section = data.get('section', '').strip()
    subject = data.get('subject', '').strip()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    deadline = data.get('deadline', '').strip()
    maximum_marks = data.get('maximum_marks')

    if not all([department_id, year, section, subject, title, description, deadline, maximum_marks]):
        return jsonify({'success': False, 'message': 'All required assignment fields must be provided.'}), 400

    # Process optional instruction attachment
    instruction_file = None
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        if allowed_file(file.filename):
            unique_filename, _ = save_uploaded_file(file, Config.ASSIGNMENT_UPLOADS)
            instruction_file = unique_filename

    # Standardize deadline format (YYYY-MM-DD HH:MM:SS)
    deadline_clean = deadline.replace('T', ' ').strip()
    if len(deadline_clean) == 16:
        deadline_clean += ':00'
    elif len(deadline_clean) > 19:
        deadline_clean = deadline_clean[:19]

    # Validate deadline date format and ensure it is in the future
    try:
        deadline_dt = datetime.strptime(deadline_clean, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid deadline date format. Please select a valid date and time.'}), 400

    if deadline_dt <= datetime.now():
        return jsonify({'success': False, 'message': 'Deadline date must be in the future. Please select a future date and time.'}), 400

    deadline_formatted = deadline_dt.strftime('%Y-%m-%d %H:%M:%S')

    assignment_id = DB.execute("""
        INSERT INTO assignments (faculty_id, department_id, year, section, subject, title, description, instruction_file, deadline, maximum_marks)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (faculty_id, department_id, year, section, subject, title, description, instruction_file, deadline_formatted, maximum_marks))

    # Create Notification for matching students
    DB.execute("""
        INSERT INTO notifications (user_role, user_id, title, message)
        VALUES ('Student', NULL, %s, %s)
    """, (f"New Assignment: {subject}", f"New assignment '{title}' posted by {session.get('name')}. Due by {deadline_formatted}."))

    # Log Activity
    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Create Assignment', session.get('name'), 'Faculty', f"Created assignment '{title}' for Subject: {subject}"))

    return jsonify({
        'success': True,
        'message': 'Assignment created and published successfully!',
        'assignment_id': assignment_id
    })

@faculty_bp.route('/api/faculty/assignments/<int:assignment_id>/update', methods=['POST'])
@login_required(role='faculty')
def update_assignment(assignment_id):
    faculty_id = session['user_id']
    assignment = DB.query("SELECT * FROM assignments WHERE assignment_id = %s", (assignment_id,), one=True)
    
    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404
        
    if assignment['faculty_id'] != faculty_id:
        return jsonify({'success': False, 'message': 'Unauthorized to modify this assignment.'}), 403

    data = request.form if request.form else (request.get_json() or {})

    department_id = data.get('department_id', assignment['department_id'])
    year = data.get('year', assignment['year'])
    section = data.get('section', assignment['section'])
    subject = data.get('subject', assignment['subject'])
    title = data.get('title', assignment['title'])
    description = data.get('description', assignment['description'])
    deadline = data.get('deadline', str(assignment['deadline']))
    maximum_marks = data.get('maximum_marks', assignment['maximum_marks'])

    # Handle replacement instruction file if uploaded
    instruction_file = assignment['instruction_file']
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        if allowed_file(file.filename):
            unique_filename, _ = save_uploaded_file(file, Config.ASSIGNMENT_UPLOADS)
            instruction_file = unique_filename

    # Standardize deadline format
    deadline_clean = str(deadline).replace('T', ' ').strip()
    if len(deadline_clean) == 16:
        deadline_clean += ':00'
    elif len(deadline_clean) > 19:
        deadline_clean = deadline_clean[:19]

    try:
        deadline_dt = datetime.strptime(deadline_clean, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid deadline date format.'}), 400

    deadline_formatted = deadline_dt.strftime('%Y-%m-%d %H:%M:%S')

    DB.execute("""
        UPDATE assignments 
        SET department_id = %s, year = %s, section = %s, subject = %s, title = %s,
            description = %s, instruction_file = %s, deadline = %s, maximum_marks = %s
        WHERE assignment_id = %s
    """, (department_id, year, section, subject, title, description, instruction_file, deadline_formatted, maximum_marks, assignment_id))

    # Notify students of updated assignment instructions
    DB.execute("""
        INSERT INTO notifications (user_role, user_id, title, message)
        VALUES ('Student', NULL, %s, %s)
    """, (f"Updated Assignment: {subject}", f"Assignment '{title}' instructions/deadline updated by {session.get('name')}."))

    # Log Activity
    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Update Assignment', session.get('name'), 'Faculty', f"Replaced/Updated assignment '{title}'"))

    return jsonify({
        'success': True,
        'message': 'Assignment updated and instruction file replaced successfully!'
    })

@faculty_bp.route('/api/faculty/assignments/<int:assignment_id>/submissions', methods=['GET'])
@login_required(role='faculty')
def get_assignment_submissions(assignment_id):
    assignment = DB.query("""
        SELECT a.*, d.code as dept_code 
        FROM assignments a
        JOIN departments d ON a.department_id = d.department_id
        WHERE a.assignment_id = %s
    """, (assignment_id,), one=True)

    if not assignment:
        return jsonify({'success': False, 'message': 'Assignment not found.'}), 404

    submissions = DB.query("""
        SELECT s.*, st.hall_ticket_no, st.first_name, st.last_name, st.email
        FROM submissions s
        JOIN students st ON s.student_id = st.student_id
        WHERE s.assignment_id = %s
        ORDER BY s.submitted_at DESC
    """, (assignment_id,))

    sub_list = []
    for s in submissions:
        sub_list.append({
            'submission_id': s['submission_id'],
            'student_name': f"{s['first_name']} {s['last_name']}",
            'hall_ticket_no': s['hall_ticket_no'],
            'email': s['email'],
            'original_filename': s['original_filename'],
            'uploaded_file': s['uploaded_file'],
            'submitted_at': format_dt(s['submitted_at']),
            'marks': s['marks'],
            'feedback': s['feedback'],
            'similarity_score': s['similarity_score'],
            'status': s['submission_status'],
            'is_graded': s['submission_status'] == 'Graded'
        })

    return jsonify({
        'success': True,
        'assignment': {
            'title': assignment['title'],
            'subject': assignment['subject'],
            'dept_code': assignment['dept_code'],
            'year': assignment['year'],
            'section': assignment['section'],
            'maximum_marks': assignment['maximum_marks']
        },
        'submissions': sub_list
    })

@faculty_bp.route('/api/faculty/submissions/<int:submission_id>/grade', methods=['POST'])
@login_required(role='faculty')
def grade_submission(submission_id):
    data = request.get_json() or request.form
    marks = data.get('marks')
    feedback = data.get('feedback', '').strip()

    if marks is None or marks == '':
        return jsonify({'success': False, 'message': 'Marks obtained field is required.'}), 400

    sub = DB.query("""
        SELECT s.*, a.title as assignment_title, a.maximum_marks, s.student_id
        FROM submissions s
        JOIN assignments a ON s.assignment_id = a.assignment_id
        WHERE s.submission_id = %s
    """, (submission_id,), one=True)

    if not sub:
        return jsonify({'success': False, 'message': 'Submission not found.'}), 404

    marks_val = float(marks)
    if marks_val < 0 or marks_val > sub['maximum_marks']:
        return jsonify({'success': False, 'message': f'Marks must be between 0 and {sub["maximum_marks"]}.'}), 400

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    DB.execute("""
        UPDATE submissions 
        SET marks = %s, feedback = %s, submission_status = 'Graded', graded_at = %s
        WHERE submission_id = %s
    """, (marks_val, feedback, now_str, submission_id))

    # Notify student
    DB.execute("""
        INSERT INTO notifications (user_role, user_id, title, message)
        VALUES ('Student', %s, %s, %s)
    """, (sub['student_id'], 'Assignment Graded',
          f"Your submission for '{sub['assignment_title']}' has been graded: {marks_val}/{sub['maximum_marks']} marks."))

    # Log Activity
    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Evaluation', session.get('name'), 'Faculty', f"Graded submission for '{sub['assignment_title']}' ({marks_val}/{sub['maximum_marks']})"))

    return jsonify({
        'success': True,
        'message': 'Submission graded successfully!'
    })

@faculty_bp.route('/api/faculty/similarity-alerts', methods=['GET'])
@login_required(role='faculty')
def get_similarity_alerts():
    faculty_id = session['user_id']
    
    alerts = DB.query("""
        SELECT s.*, a.title as assignment_title, a.subject,
               st.first_name, st.last_name, st.hall_ticket_no
        FROM submissions s
        JOIN assignments a ON s.assignment_id = a.assignment_id
        JOIN students st ON s.student_id = st.student_id
        WHERE a.faculty_id = %s AND s.similarity_score >= %s
        ORDER BY s.similarity_score DESC
    """, (faculty_id, Config.SIMILARITY_THRESHOLD))

    result = []
    for alert in alerts:
        result.append({
            'submission_id': alert['submission_id'],
            'assignment_title': alert['assignment_title'],
            'subject': alert['subject'],
            'student_name': f"{alert['first_name']} {alert['last_name']}",
            'hall_ticket_no': alert['hall_ticket_no'],
            'similarity_score': alert['similarity_score'],
            'submitted_at': format_dt(alert['submitted_at'])
        })

    return jsonify({'success': True, 'alerts': result})
