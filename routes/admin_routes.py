from flask import Blueprint, request, jsonify, session
from db import DB
from utils.auth_utils import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/dashboard-stats', methods=['GET'])
@login_required(role='admin')
def get_dashboard_stats():
    total_students = DB.query("SELECT COUNT(*) as cnt FROM students", one=True)['cnt']
    pending_students = DB.query("SELECT COUNT(*) as cnt FROM students WHERE approval_status = 'Pending'", one=True)['cnt']
    approved_students = DB.query("SELECT COUNT(*) as cnt FROM students WHERE approval_status = 'Approved'", one=True)['cnt']
    
    total_faculty = DB.query("SELECT COUNT(*) as cnt FROM faculty", one=True)['cnt']
    pending_faculty = DB.query("SELECT COUNT(*) as cnt FROM faculty WHERE approval_status = 'Pending'", one=True)['cnt']
    
    total_assignments = DB.query("SELECT COUNT(*) as cnt FROM assignments", one=True)['cnt']
    total_submissions = DB.query("SELECT COUNT(*) as cnt FROM submissions", one=True)['cnt']

    return jsonify({
        'success': True,
        'stats': {
            'total_students': total_students,
            'pending_students': pending_students,
            'approved_students': approved_students,
            'total_faculty': total_faculty,
            'pending_faculty': pending_faculty,
            'total_assignments': total_assignments,
            'total_submissions': total_submissions
        }
    })

@admin_bp.route('/api/admin/pending-registrations', methods=['GET'])
@login_required(role='admin')
def get_pending_registrations():
    students = DB.query("""
        SELECT s.student_id, s.hall_ticket_no, s.first_name, s.last_name, s.email, s.year, s.section, s.created_at,
               d.code as dept_code
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        WHERE s.approval_status = 'Pending'
        ORDER BY s.created_at DESC
    """)

    faculty = DB.query("""
        SELECT f.faculty_id, f.faculty_code, f.first_name, f.last_name, f.email, f.created_at,
               d.code as dept_code
        FROM faculty f
        JOIN departments d ON f.department_id = d.department_id
        WHERE f.approval_status = 'Pending'
        ORDER BY f.created_at DESC
    """)

    pending_list = []
    for s in students:
        created_str = s['created_at'].strftime('%b %d') if hasattr(s['created_at'], 'strftime') else str(s['created_at'])
        pending_list.append({
            'id': s['student_id'],
            'type': 'student',
            'identifier': s['hall_ticket_no'],
            'name': f"{s['first_name']} {s['last_name']}",
            'email': s['email'],
            'role_dept': f"Student · {s['dept_code']} · Y{s['year']}",
            'created_at': created_str
        })

    for f in faculty:
        created_str = f['created_at'].strftime('%b %d') if hasattr(f['created_at'], 'strftime') else str(f['created_at'])
        pending_list.append({
            'id': f['faculty_id'],
            'type': 'faculty',
            'identifier': f['faculty_code'],
            'name': f"{f['first_name']} {f['last_name']}",
            'email': f['email'],
            'role_dept': f"Faculty · {f['dept_code']}",
            'created_at': created_str
        })

    return jsonify({'success': True, 'pending': pending_list})

@admin_bp.route('/api/admin/students/<int:student_id>/approve', methods=['POST'])
@login_required(role='admin')
def approve_student(student_id):
    student = DB.query("SELECT * FROM students WHERE student_id = %s", (student_id,), one=True)
    if not student:
        return jsonify({'success': False, 'message': 'Student record not found.'}), 404

    DB.execute("UPDATE students SET approval_status = 'Approved' WHERE student_id = %s", (student_id,))
    
    # Notify Student
    DB.execute("""
        INSERT INTO notifications (user_role, user_id, title, message)
        VALUES ('Student', %s, 'Account Approved', 'Your student account registration has been approved! You can now log in.')
    """, (student_id,))

    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Approval', 'Admin', 'Admin', f"Approved student registration for Hall Ticket: {student['hall_ticket_no']}"))

    return jsonify({'success': True, 'message': f"Student {student['first_name']} {student['last_name']} approved successfully!"})

@admin_bp.route('/api/admin/students/<int:student_id>/reject', methods=['POST'])
@login_required(role='admin')
def reject_student(student_id):
    student = DB.query("SELECT * FROM students WHERE student_id = %s", (student_id,), one=True)
    if not student:
        return jsonify({'success': False, 'message': 'Student record not found.'}), 404

    DB.execute("UPDATE students SET approval_status = 'Rejected' WHERE student_id = %s", (student_id,))

    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Rejection', 'Admin', 'Admin', f"Rejected student registration for Hall Ticket: {student['hall_ticket_no']}"))

    return jsonify({'success': True, 'message': f"Student {student['first_name']} {student['last_name']} rejected."})

@admin_bp.route('/api/admin/faculty/<int:faculty_id>/approve', methods=['POST'])
@login_required(role='admin')
def approve_faculty(faculty_id):
    fac = DB.query("SELECT * FROM faculty WHERE faculty_id = %s", (faculty_id,), one=True)
    if not fac:
        return jsonify({'success': False, 'message': 'Faculty record not found.'}), 404

    DB.execute("UPDATE faculty SET approval_status = 'Approved' WHERE faculty_id = %s", (faculty_id,))
    
    # Notify Faculty
    DB.execute("""
        INSERT INTO notifications (user_role, user_id, title, message)
        VALUES ('Faculty', %s, 'Account Approved', 'Your faculty account registration has been approved! You can now log in.')
    """, (faculty_id,))

    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Approval', 'Admin', 'Admin', f"Approved faculty registration for ID: {fac['faculty_code']}"))

    return jsonify({'success': True, 'message': f"Faculty {fac['first_name']} {fac['last_name']} approved successfully!"})

@admin_bp.route('/api/admin/faculty/<int:faculty_id>/reject', methods=['POST'])
@login_required(role='admin')
def reject_faculty(faculty_id):
    fac = DB.query("SELECT * FROM faculty WHERE faculty_id = %s", (faculty_id,), one=True)
    if not fac:
        return jsonify({'success': False, 'message': 'Faculty record not found.'}), 404

    DB.execute("UPDATE faculty SET approval_status = 'Rejected' WHERE faculty_id = %s", (faculty_id,))

    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Rejection', 'Admin', 'Admin', f"Rejected faculty registration for ID: {fac['faculty_code']}"))

    return jsonify({'success': True, 'message': f"Faculty {fac['first_name']} {fac['last_name']} rejected."})

@admin_bp.route('/api/admin/departments', methods=['GET'])
@login_required(role='admin')
def get_departments():
    depts = DB.query("""
        SELECT d.*, 
               COUNT(DISTINCT s.student_id) as student_count,
               COUNT(DISTINCT f.faculty_id) as faculty_count
        FROM departments d
        LEFT JOIN students s ON d.department_id = s.department_id
        LEFT JOIN faculty f ON d.department_id = f.department_id
        GROUP BY d.department_id
        ORDER BY d.code ASC
    """)
    return jsonify({'success': True, 'departments': depts})

@admin_bp.route('/api/admin/departments/add', methods=['POST'])
@login_required(role='admin')
def add_department():
    data = request.get_json() or request.form
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'message': 'Department code and name are required.'}), 400

    existing = DB.query("SELECT * FROM departments WHERE code = %s", (code,), one=True)
    if existing:
        return jsonify({'success': False, 'message': 'Department code already exists.'}), 400

    dept_id = DB.execute("INSERT INTO departments (code, department_name) VALUES (%s, %s)", (code, name))
    
    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Add Department', 'Admin', 'Admin', f"Added department {code} ({name})"))

    return jsonify({'success': True, 'message': 'Department added successfully!', 'department_id': dept_id})

@admin_bp.route('/api/admin/activity-logs', methods=['GET'])
@login_required(role='admin')
def get_activity_logs():
    logs = DB.query("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 20")
    result = []
    for l in logs:
        created_str = l['created_at'].strftime('%b %d, %I:%M %p') if hasattr(l['created_at'], 'strftime') else str(l['created_at'])
        result.append({
            'id': l['log_id'],
            'event_type': l['event_type'],
            'user_name': l['user_name'],
            'user_role': l['user_role'],
            'description': l['description'],
            'created_at': created_str
        })
    return jsonify({'success': True, 'logs': result})
