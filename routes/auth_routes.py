from flask import Blueprint, request, jsonify, session
from db import DB
from utils.auth_utils import hash_password, verify_password

auth_bp = Blueprint('auth', __name__)

# ==========================================
# STUDENT AUTHENTICATION API
# ==========================================

@auth_bp.route('/api/student/register', methods=['POST'])
def student_register():
    data = request.get_json() or request.form
    
    hall_ticket = data.get('hall_ticket_no', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    department_id = data.get('department_id')
    year = data.get('year')
    section = data.get('section', '').strip()
    password = data.get('password', '').strip()

    if not all([hall_ticket, first_name, last_name, email, department_id, year, section, password]):
        return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

    # Check for duplicate Hall Ticket or Email
    existing_ht = DB.query("SELECT * FROM students WHERE hall_ticket_no = %s", (hall_ticket,), one=True)
    if existing_ht:
        return jsonify({'success': False, 'message': 'Hall Ticket Number already registered.'}), 400

    existing_email = DB.query("SELECT * FROM students WHERE email = %s", (email,), one=True)
    if existing_email:
        return jsonify({'success': False, 'message': 'Email address already registered.'}), 400

    pass_hash = hash_password(password)

    student_id = DB.execute("""
        INSERT INTO students (hall_ticket_no, first_name, last_name, email, phone, password_hash, department_id, year, section, approval_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (hall_ticket, first_name, last_name, email, phone, pass_hash, department_id, year, section, 'Pending'))

    # Log Activity
    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Student Registration', f"{first_name} {last_name}", 'Student', f"Registration pending for Hall Ticket: {hall_ticket}"))

    return jsonify({
        'success': True,
        'message': 'Registration successful! Your account status is Pending admin approval.'
    })

@auth_bp.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.get_json() or request.form
    hall_ticket = data.get('hall_ticket_no', '').strip()
    password = data.get('password', '').strip()

    if not hall_ticket or not password:
        return jsonify({'success': False, 'message': 'Hall Ticket Number and Password are required.'}), 400

    student = DB.query("""
        SELECT s.*, d.code as dept_code, d.department_name 
        FROM students s 
        JOIN departments d ON s.department_id = d.department_id 
        WHERE s.hall_ticket_no = %s
    """, (hall_ticket,), one=True)

    if not student or not verify_password(password, student['password_hash']):
        return jsonify({'success': False, 'message': 'Invalid Hall Ticket Number or Password.'}), 401

    if student['approval_status'] == 'Pending':
        return jsonify({'success': False, 'message': 'Account Registration Pending! Please log in as Admin (admin / admin123) to Approve.'}), 403

    if student['approval_status'] == 'Rejected':
        return jsonify({'success': False, 'message': 'Your registration was rejected by Admin.'}), 403

    # Create session
    session.clear()
    session['user_id'] = student['student_id']
    session['user_role'] = 'student'
    session['hall_ticket_no'] = student['hall_ticket_no']
    session['name'] = f"{student['first_name']} {student['last_name']}"
    session['email'] = student['email']
    session['department_id'] = student['department_id']
    session['dept_code'] = student['dept_code']
    session['year'] = student['year']
    session['section'] = student['section']

    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'redirect': '/student-dashboard',
        'student': {
            'student_id': student['student_id'],
            'name': session['name'],
            'hall_ticket_no': student['hall_ticket_no'],
            'email': student['email'],
            'dept': student['dept_code'],
            'year': student['year'],
            'section': student['section']
        }
    })

@auth_bp.route('/api/student/session', methods=['GET'])
def student_session():
    if session.get('user_role') == 'student' and 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'student_id': session.get('user_id'),
            'name': session.get('name'),
            'email': session.get('email'),
            'hall_ticket_no': session.get('hall_ticket_no'),
            'department_id': session.get('department_id'),
            'dept_code': session.get('dept_code'),
            'year': session.get('year'),
            'section': session.get('section')
        })
    return jsonify({'logged_in': False})

@auth_bp.route('/api/student/logout', methods=['POST', 'GET'])
def student_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

# ==========================================
# FACULTY AUTHENTICATION API
# ==========================================

@auth_bp.route('/api/faculty/register', methods=['POST'])
def faculty_register():
    data = request.get_json() or request.form
    
    faculty_code = data.get('faculty_code', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    department_id = data.get('department_id')
    password = data.get('password', '').strip()

    if not all([faculty_code, first_name, last_name, email, department_id, password]):
        return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

    existing_fc = DB.query("SELECT * FROM faculty WHERE faculty_code = %s", (faculty_code,), one=True)
    if existing_fc:
        return jsonify({'success': False, 'message': 'Faculty ID already registered.'}), 400

    existing_email = DB.query("SELECT * FROM faculty WHERE email = %s", (email,), one=True)
    if existing_email:
        return jsonify({'success': False, 'message': 'Email address already registered.'}), 400

    pass_hash = hash_password(password)

    faculty_id = DB.execute("""
        INSERT INTO faculty (faculty_code, first_name, last_name, email, phone, password_hash, department_id, approval_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (faculty_code, first_name, last_name, email, phone, pass_hash, department_id, 'Pending'))

    DB.execute("INSERT INTO activity_logs (event_type, user_name, user_role, description) VALUES (%s, %s, %s, %s)",
               ('Faculty Registration', f"{first_name} {last_name}", 'Faculty', f"Registration pending for Faculty ID: {faculty_code}"))

    return jsonify({
        'success': True,
        'message': 'Faculty registration successful! Account pending Admin approval.'
    })

@auth_bp.route('/api/faculty/login', methods=['POST'])
def faculty_login():
    data = request.get_json() or request.form
    faculty_code = data.get('faculty_code', '').strip()
    password = data.get('password', '').strip()

    if not faculty_code or not password:
        return jsonify({'success': False, 'message': 'Faculty ID and Password are required.'}), 400

    fac = DB.query("""
        SELECT f.*, d.code as dept_code, d.department_name 
        FROM faculty f 
        JOIN departments d ON f.department_id = d.department_id 
        WHERE f.faculty_code = %s
    """, (faculty_code,), one=True)

    if not fac or not verify_password(password, fac['password_hash']):
        return jsonify({'success': False, 'message': 'Invalid Faculty ID or Password.'}), 401

    if fac['approval_status'] == 'Pending':
        return jsonify({'success': False, 'message': 'Faculty Account Registration Pending! Please log in as Admin (admin / admin123) to Approve.'}), 403

    if fac['approval_status'] == 'Rejected':
        return jsonify({'success': False, 'message': 'Your faculty registration was rejected by Admin.'}), 403

    session.clear()
    session['user_id'] = fac['faculty_id']
    session['user_role'] = 'faculty'
    session['faculty_code'] = fac['faculty_code']
    session['name'] = f"{fac['first_name']} {fac['last_name']}"
    session['email'] = fac['email']
    session['department_id'] = fac['department_id']
    session['dept_code'] = fac['dept_code']

    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'redirect': '/faculty-dashboard',
        'faculty': {
            'faculty_id': fac['faculty_id'],
            'faculty_code': fac['faculty_code'],
            'name': session['name'],
            'email': fac['email'],
            'dept': fac['dept_code']
        }
    })

@auth_bp.route('/api/faculty/session', methods=['GET'])
def faculty_session():
    if session.get('user_role') == 'faculty' and 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'faculty_id': session.get('user_id'),
            'name': session.get('name'),
            'email': session.get('email'),
            'faculty_code': session.get('faculty_code'),
            'department_id': session.get('department_id'),
            'dept_code': session.get('dept_code')
        })
    return jsonify({'logged_in': False})

@auth_bp.route('/api/faculty/logout', methods=['POST', 'GET'])
def faculty_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

# ==========================================
# ADMIN AUTHENTICATION API
# ==========================================

@auth_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and Password are required.'}), 400

    admin = DB.query("SELECT * FROM admin WHERE username = %s", (username,), one=True)
    if not admin or not verify_password(password, admin['password_hash']):
        return jsonify({'success': False, 'message': 'Invalid Admin Username or Password.'}), 401

    session.clear()
    session['user_id'] = admin['admin_id']
    session['user_role'] = 'admin'
    session['name'] = 'System Administrator'
    session['username'] = admin['username']

    return jsonify({
        'success': True,
        'message': 'Admin login successful!',
        'redirect': '/admin-dashboard'
    })

@auth_bp.route('/api/admin/logout', methods=['POST', 'GET'])
def admin_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})
