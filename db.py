import os
import socket
import sqlite3
import pymysql
import bcrypt
from datetime import datetime, timedelta
from config import Config

def is_mysql_available():
    """Fast socket test to check if MySQL/MariaDB server is running on port 3306."""
    try:
        sock = socket.create_connection((Config.MYSQL_HOST, Config.MYSQL_PORT), timeout=0.5)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def get_db():
    """
    Attempts to connect to MySQL/MariaDB if server is listening on port 3306.
    Otherwise, transparently falls back to local SQLite database.
    """
    if is_mysql_available():
        try:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                port=Config.MYSQL_PORT,
                connect_timeout=2,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
                cursor.execute(f"USE {Config.MYSQL_DB}")
            return conn, 'mysql'
        except Exception:
            pass

    # Fallback to SQLite database file
    os.makedirs(os.path.dirname(Config.SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'

class DB:
    @staticmethod
    def query(sql, params=(), one=False):
        conn, db_type = get_db()
        try:
            if db_type == 'mysql':
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    rv = cursor.fetchall()
                    return (rv[0] if rv else None) if one else rv
            else:
                sql_sqlite = sql.replace('%s', '?')
                cursor = conn.cursor()
                cursor.execute(sql_sqlite, params)
                rows = cursor.fetchall()
                result = [dict(r) for r in rows]
                return (result[0] if result else None) if one else result
        finally:
            conn.close()

    @staticmethod
    def execute(sql, params=()):
        conn, db_type = get_db()
        try:
            if db_type == 'mysql':
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    last_id = cursor.lastrowid
                    return last_id
            else:
                sql_sqlite = sql.replace('%s', '?')
                cursor = conn.cursor()
                cursor.execute(sql_sqlite, params)
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()

def init_db():
    """Initializes tables and seeds default data if tables do not exist."""
    conn, db_type = get_db()
    try:
        if db_type == 'mysql':
            with conn.cursor() as cursor:
                schema_path = os.path.join(Config.BASE_DIR, 'database', 'schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        sql_script = f.read()
                    for statement in sql_script.split(';'):
                        stmt = statement.strip()
                        if stmt:
                            cursor.execute(stmt)
        else:
            cursor = conn.cursor()
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                department_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS admin (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                hall_ticket_no TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL,
                approval_status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS faculty (
                faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_code TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                approval_status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_id INTEGER NOT NULL,
                department_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL,
                subject TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                instruction_file TEXT,
                deadline TIMESTAMP NOT NULL,
                maximum_marks INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
                FOREIGN KEY (department_id) REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS submissions (
                submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                uploaded_file TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                submitted_at TIMESTAMP NOT NULL,
                marks INTEGER DEFAULT NULL,
                feedback TEXT DEFAULT NULL,
                similarity_score REAL DEFAULT 0.0,
                submission_status TEXT DEFAULT 'Submitted',
                graded_at TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_role TEXT NOT NULL,
                user_id INTEGER DEFAULT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_name TEXT NOT NULL,
                user_role TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()
            
        seed_db()
    finally:
        conn.close()

def seed_db():
    """Seeds initial departments, admin account, test student, test faculty, and sample assignments."""
    depts = [
        ('CSE', 'Computer Science and Engineering'),
        ('ECE', 'Electronics and Communication Engineering'),
        ('EEE', 'Electrical and Electronics Engineering'),
        ('CIVIL', 'Civil Engineering'),
        ('MECH', 'Mechanical Engineering')
    ]
    for code, name in depts:
        existing = DB.query("SELECT * FROM departments WHERE code = %s", (code,), one=True)
        if not existing:
            DB.execute("INSERT INTO departments (code, department_name) VALUES (%s, %s)", (code, name))
            
    cse_dept = DB.query("SELECT department_id FROM departments WHERE code = %s", ('CSE',), one=True)
    cse_id = cse_dept['department_id'] if cse_dept else 1

    # Seed Default Admin: admin / admin123
    admin_user = DB.query("SELECT * FROM admin WHERE username = %s", ('admin',), one=True)
    if not admin_user:
        pass_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        DB.execute("INSERT INTO admin (username, password_hash, email) VALUES (%s, %s, %s)",
                   ('admin', pass_hash, 'admin@college.edu'))

    # Seed Test Student: 23CS001 / student123 (Approved)
    student = DB.query("SELECT * FROM students WHERE hall_ticket_no = %s", ('23CS001',), one=True)
    if not student:
        pass_hash = bcrypt.hashpw('student123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        DB.execute("""
            INSERT INTO students (hall_ticket_no, first_name, last_name, email, phone, password_hash, department_id, year, section, approval_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('23CS001', 'Test', 'Student', 'teststudent@gmail.com', '9876543210', pass_hash, cse_id, 3, 'A', 'Approved'))

    # Seed Test Student Asha (23CS002) for theme matching
    asha = DB.query("SELECT * FROM students WHERE hall_ticket_no = %s", ('23CS002',), one=True)
    if not asha:
        pass_hash = bcrypt.hashpw('student123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        DB.execute("""
            INSERT INTO students (hall_ticket_no, first_name, last_name, email, phone, password_hash, department_id, year, section, approval_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('23CS002', 'Asha', 'K.', 'asha@college.edu', '9876543211', pass_hash, cse_id, 2, 'A', 'Approved'))

    # Seed Test Faculty: F001 / faculty123 (Approved)
    fac = DB.query("SELECT * FROM faculty WHERE faculty_code = %s", ('F001',), one=True)
    if not fac:
        pass_hash = bcrypt.hashpw('faculty123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        fac_id = DB.execute("""
            INSERT INTO faculty (faculty_code, first_name, last_name, email, phone, password_hash, department_id, approval_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ('F001', 'Dr.', 'Mehta', 'mehta@college.edu', '9123456789', pass_hash, cse_id, 'Approved'))
    else:
        fac_id = fac['faculty_id']

    # Seed Initial Sample Assignments
    asgns = DB.query("SELECT COUNT(*) as count FROM assignments", one=True)
    if asgns and (asgns['count'] == 0 or asgns.get('count(*)', 0) == 0):
        dt_future1 = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        dt_future2 = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        dt_future3 = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        dt_past = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')

        DB.execute("""
            INSERT INTO assignments (faculty_id, department_id, year, section, subject, title, description, deadline, maximum_marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (fac_id, cse_id, 2, 'A', 'ADSAA', 'AVL Tree Implementation & Analysis',
              'Implement a self-balancing AVL tree in C++ with insert, delete, and search operations. Include rotation logic and height balancing. Provide a test driver.',
              dt_future1, 20))

        DB.execute("""
            INSERT INTO assignments (faculty_id, department_id, year, section, subject, title, description, deadline, maximum_marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (fac_id, cse_id, 2, 'A', 'Python', 'File Handling & Exception Management',
              'Write a Python program that reads a large CSV file, handles missing data with custom exceptions, logs errors to a separate file, and outputs a cleaned dataset.',
              dt_future2, 25))

        DB.execute("""
            INSERT INTO assignments (faculty_id, department_id, year, section, subject, title, description, deadline, maximum_marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (fac_id, cse_id, 2, 'A', 'AI', 'A* Search Algorithm — 8-Puzzle Problem',
              'Implement the A* search algorithm to solve the 8-puzzle problem. Use Manhattan distance heuristic. Compare performance with BFS.',
              dt_future3, 30))

        DB.execute("""
            INSERT INTO assignments (faculty_id, department_id, year, section, subject, title, description, deadline, maximum_marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (fac_id, cse_id, 2, 'A', 'Java', 'Multithreading — Producer Consumer Problem',
              'Implement the classic Producer-Consumer problem in Java using synchronized blocks and wait/notify. Demonstrate with concurrent producers.',
              dt_past, 20))

        DB.execute("""
            INSERT INTO assignments (faculty_id, department_id, year, section, subject, title, description, deadline, maximum_marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (fac_id, cse_id, 3, 'A', 'Python', 'Advanced Flask Web Portal Architecture',
              'Develop a secure, role-based web assignment portal with SQLite/MariaDB persistence, bcrypt authentication, and automated file validation.',
              dt_future2, 50))
