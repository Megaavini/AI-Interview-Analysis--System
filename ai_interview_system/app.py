# -------------------------------
# app.py - main Flask application
# -------------------------------
import base64
import json
import os
import re
import sqlite3
import time
import hashlib
from functools import wraps

import cv2
import numpy as np
from flask import (Flask, render_template, request, redirect, url_for, flash, session,
                   jsonify, send_from_directory, abort)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import config
import mailer
import emotion
import liveness
import interview_engine as engine

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_MB * 1024 * 1024 + 1024 * 1024
os.makedirs(config.UPLOAD_DIR, exist_ok=True)

DB_PATH = os.path.join(config.BASE_DIR, 'interview_system.db')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# live liveness trackers (one per running interview)
TRACKERS = {}


# ---------- Database helpers ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _add_column(cur, table, col, ddl):
    cols = [r[1] for r in cur.execute(f'PRAGMA table_info({table})')]
    if col not in cols:
        cur.execute(f'ALTER TABLE {table} ADD COLUMN {col} {ddl}')


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS mock_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            difficulty TEXT,
            score INTEGER,
            total INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # ---- new columns on users (safe for your existing database) ----
    _add_column(cur, 'users', 'full_name', 'TEXT')
    _add_column(cur, 'users', 'email', 'TEXT')
    _add_column(cur, 'users', 'phone', 'TEXT')
    _add_column(cur, 'users', 'resume_file', 'TEXT')
    _add_column(cur, 'users', 'role', "TEXT DEFAULT 'candidate'")   # candidate | hr | admin
    _add_column(cur, 'users', 'shortlisted', 'INTEGER DEFAULT 0')
    _add_column(cur, 'users', 'shortlist_job', 'TEXT')
    _add_column(cur, 'users', 'shortlisted_at', 'TIMESTAMP')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            questions TEXT,
            status TEXT DEFAULT 'in_progress',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            interview_marks REAL DEFAULT 0,
            interview_total REAL DEFAULT 0,
            personality_marks REAL DEFAULT 0,
            personality_json TEXT,
            overall_pct REAL DEFAULT 0,
            grade TEXT,
            total_frames INTEGER DEFAULT 0,
            face_frames INTEGER DEFAULT 0,
            spoof_frames INTEGER DEFAULT 0,
            multi_face_frames INTEGER DEFAULT 0,
            tab_switches INTEGER DEFAULT 0,
            feedback_rating INTEGER,
            feedback_text TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS interview_answers (
            interview_id INTEGER,
            idx INTEGER,
            answer TEXT,
            marks REAL DEFAULT 0,
            detail TEXT,
            PRIMARY KEY (interview_id, idx)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS emotion_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER,
            q_idx INTEGER,
            emotion TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            message TEXT,
            email_status TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # default admin (admin / admin123)
    cur.execute("SELECT id FROM users WHERE username='admin'")
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (username, password, is_admin, role) VALUES (?, ?, 1, 'admin')",
                    ('admin', generate_password_hash('admin123')))
    cur.execute("UPDATE users SET role='admin' WHERE is_admin=1 AND (role IS NULL OR role='candidate')")
    cur.execute("UPDATE users SET role='candidate' WHERE role IS NULL")
    conn.commit()
    conn.close()


init_db()


# ---------- Password helpers (old SHA-256 accounts keep working, then get upgraded) ----------
def verify_password(user, password):
    stored = user['password']
    if stored.startswith(('pbkdf2:', 'scrypt:')):
        return check_password_hash(stored, password)
    if stored == hashlib.sha256(password.encode()).hexdigest():
        conn = get_db()
        conn.execute('UPDATE users SET password=? WHERE id=?', (generate_password_hash(password), user['id']))
        conn.commit()
        conn.close()
        return True
    return False


# ---------- Decorators ----------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def staff_required(f):
    """HR + admin."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') not in ('admin', 'hr'):
            flash('HR / Admin access required', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def admin_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated


@app.context_processor
def inject_globals():
    return {'is_staff': session.get('role') in ('admin', 'hr')}


# ---------- Resume helpers ----------
def save_resume(file, user_id):
    """Returns (filename or None, error or None)."""
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in config.ALLOWED_RESUME_EXT:
        return None, 'Resume must be a PDF, DOC or DOCX file'
    head = file.stream.read(8)
    file.stream.seek(0)
    sig_ok = {'pdf': head.startswith(b'%PDF'),
              'docx': head.startswith(b'PK'),
              'doc': head.startswith(b'\xd0\xcf\x11\xe0')}[ext]
    if not sig_ok:
        return None, f'That file is not a real {ext.upper()} document'
    name = secure_filename(f'{user_id}_{int(time.time())}.{ext}')
    file.save(os.path.join(config.UPLOAD_DIR, name))
    return name, None


def remove_resume(filename):
    if filename:
        p = os.path.join(config.UPLOAD_DIR, filename)
        if os.path.exists(p):
            os.remove(p)


# ---------- Public / auth routes ----------
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        if not username or not password:
            flash('Username and password required', 'danger')
            return redirect(url_for('register'))
        if not EMAIL_RE.match(email):
            flash('A valid e-mail address is required (shortlist mails are sent there)', 'danger')
            return redirect(url_for('register'))
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password, full_name, email, phone, role) "
                        "VALUES (?, ?, ?, ?, ?, 'candidate')",
                        (username, generate_password_hash(password), full_name, email, phone))
            uid = cur.lastrowid
            fname, err = save_resume(request.files.get('resume'), uid)
            if err:
                flash(err + ' - account created, you can upload the resume later from Profile.', 'warning')
            elif fname:
                cur.execute('UPDATE users SET resume_file=? WHERE id=?', (fname, uid))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists', 'danger')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and verify_password(user, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role'] or ('admin' if user['is_admin'] else 'candidate')
            session['is_admin'] = session['role'] == 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('admin') if session['role'] in ('admin', 'hr') else url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    notes = conn.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 5',
                         (session['user_id'],)).fetchall()
    ivs = conn.execute("SELECT * FROM interviews WHERE user_id=? AND status='done' ORDER BY id DESC LIMIT 3",
                       (session['user_id'],)).fetchall()
    conn.close()
    return render_template('dashboard.html', user=user, notes=notes, interviews=ivs)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        if not EMAIL_RE.match(email):
            flash('Enter a valid e-mail address', 'danger')
        else:
            fname, err = save_resume(request.files.get('resume'), user['id'])
            if err:
                flash(err, 'danger')
            else:
                if fname:
                    remove_resume(user['resume_file'])
                    conn.execute('UPDATE users SET resume_file=? WHERE id=?', (fname, user['id']))
                conn.execute('UPDATE users SET full_name=?, email=?, phone=? WHERE id=?',
                             (full_name, email, phone, user['id']))
                conn.commit()
                flash('Profile updated', 'success')
                conn.close()
                return redirect(url_for('profile'))
    conn.close()
    return render_template('profile.html', user=user)


def _resume_row(uid):
    """Owner or HR/admin only. Returns the stored file name."""
    if uid != session['user_id'] and session.get('role') not in ('admin', 'hr'):
        abort(403)
    conn = get_db()
    row = conn.execute('SELECT resume_file, full_name, username FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    if not row or not row['resume_file'] or not os.path.exists(os.path.join(config.UPLOAD_DIR, row['resume_file'])):
        abort(404)
    return row


@app.route('/resume/<int:uid>')
@login_required
def resume(uid):
    """Download."""
    row = _resume_row(uid)
    return send_from_directory(config.UPLOAD_DIR, row['resume_file'], as_attachment=True)


@app.route('/resume/<int:uid>/raw')
@login_required
def resume_raw(uid):
    """Same file, shown inline in the browser (used by the on-screen viewer)."""
    row = _resume_row(uid)
    ext = row['resume_file'].rsplit('.', 1)[-1].lower()
    mime = {'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword'}[ext]
    resp = send_from_directory(config.UPLOAD_DIR, row['resume_file'], mimetype=mime, as_attachment=False)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Cache-Control'] = 'private, no-store'
    return resp


@app.route('/resume/<int:uid>/view')
@login_required
def resume_view(uid):
    """On-screen resume viewer (PDF inline, DOCX rendered to HTML, DOC -> download)."""
    row = _resume_row(uid)
    ext = row['resume_file'].rsplit('.', 1)[-1].lower()
    return render_template('resume_view.html', uid=uid, ext=ext, name=row['full_name'] or row['username'])


QUESTIONS = {
    'python': {
        'easy': [
            {'q': 'What is the output of print(2**3)?', 'options': ['5', '6', '8', '9'], 'ans': 2},
            {'q': 'Which keyword is used for function definition in Python?', 'options': ['function', 'def', 'func', 'define'], 'ans': 1},
            {'q': 'What is the correct file extension for Python files?', 'options': ['.py', '.pyth', '.pt', '.p'], 'ans': 0},
            {'q': 'Which of these is a Python data type?', 'options': ['list', 'array', 'vector', 'matrix'], 'ans': 0},
            {'q': 'What is the output of len("hello")?', 'options': ['4', '5', '6', '3'], 'ans': 1},
        ],
        'medium': [
            {'q': 'What is the output of print(3 * "ab" + "c")?', 'options': ['abababc', 'abcabc', 'abab', 'error'], 'ans': 0},
            {'q': 'Which of the following is used to handle exceptions in Python?', 'options': ['try-except', 'try-catch', 'throw-catch', 'error-handle'], 'ans': 0},
            {'q': 'What is the correct way to create a list in Python?', 'options': ['list = []', 'list = ()', 'list = {}', 'list = < >'], 'ans': 0},
            {'q': 'What is the output of print(type([]))?', 'options': ['<class "list">', '<class "array">', '<class "tuple">', '<class "dict">'], 'ans': 0},
            {'q': 'Which of the following is NOT a Python looping construct?', 'options': ['for', 'while', 'do-while', 'None'], 'ans': 2},
        ],
        'hard': [
            {'q': 'What is the output of print(list(filter(lambda x: x%2==0, [1,2,3,4,5])))?', 'options': ['[2,4]', '[1,3,5]', '[2,4,6]', '[]'], 'ans': 0},
            {'q': 'Which of the following is used for multiple inheritance in Python?', 'options': ['class A(B, C)', 'class A extends B, C', 'class A inherits B, C', 'None'], 'ans': 0},
            {'q': 'What is the output of print(10 // 3)?', 'options': ['3', '3.33', '4', '3.0'], 'ans': 0},
            {'q': 'What is the correct way to open a file in Python for reading?', 'options': ['open("file.txt", "r")', 'open("file.txt", "read")', 'read("file.txt")', 'file_open("file.txt")'], 'ans': 0},
            {'q': 'What is the output of print(len("Hello World".split()))?', 'options': ['2', '3', '1', '4'], 'ans': 0},
        ]
    },
    'java': {
        'easy': [
            {'q': 'Which keyword is used to inherit a class in Java?', 'options': ['extends', 'implements', 'inherits', 'super'], 'ans': 0},
            {'q': 'What is the size of int in Java?', 'options': ['2 bytes', '4 bytes', '8 bytes', '1 byte'], 'ans': 1},
            {'q': 'Which method is the entry point of a Java program?', 'options': ['main()', 'start()', 'run()', 'init()'], 'ans': 0},
            {'q': 'What is Java?', 'options': ['OS', 'Database', 'Programming language', 'Framework'], 'ans': 2},
            {'q': 'Which of these is NOT a Java feature?', 'options': ['OOP', 'Platform independent', 'Pointer', 'Garbage collection'], 'ans': 2},
        ],
        'medium': [
            {'q': 'What is the output of System.out.println(10 + 20 + "30")?', 'options': ['102030', '3030', '1030', '30'], 'ans': 1},
            {'q': 'Which keyword is used to create an interface in Java?', 'options': ['interface', 'abstract', 'implements', 'extends'], 'ans': 0},
            {'q': 'What is the default value of a boolean variable in Java?', 'options': ['true', 'false', 'null', '0'], 'ans': 1},
            {'q': 'Which of the following is NOT a Java access modifier?', 'options': ['public', 'private', 'protected', 'internal'], 'ans': 3},
            {'q': 'What is the output of System.out.println(5/2)?', 'options': ['2', '2.5', '3', '2.0'], 'ans': 0},
        ],
        'hard': [
            {'q': 'What is the output of System.out.println(1 + 2 + "3" + 4)?', 'options': ['1234', '334', '334', '124'], 'ans': 1},
            {'q': 'Which of the following is used to create a thread in Java?', 'options': ['Thread class', 'Runnable interface', 'Both', 'None'], 'ans': 2},
            {'q': 'What is the output of System.out.println(10 % 3)?', 'options': ['3', '1', '2', '0'], 'ans': 1},
            {'q': 'Which collection class allows duplicate elements in Java?', 'options': ['ArrayList', 'HashSet', 'TreeSet', 'None'], 'ans': 0},
            {'q': 'What is the output of System.out.println(4 + 5 + "6")?', 'options': ['456', '96', '45', '15'], 'ans': 1},
        ]
    },
    'php': {
        'easy': [
            {'q': 'What does PHP stand for?', 'options': ['Personal Home Page', 'PHP: Hypertext Preprocessor', 'Pre Hypertext', 'Public Home Page'], 'ans': 1},
            {'q': 'Which symbol is used for variable in PHP?', 'options': ['$', '#', '@', '&'], 'ans': 0},
            {'q': 'What is the output of echo 2 + "2"; in PHP?', 'options': ['22', '4', '2', 'Error'], 'ans': 1},
            {'q': 'Which function is used to include a file in PHP?', 'options': ['include()', 'import()', 'require()', 'Both include and require'], 'ans': 3},
            {'q': 'PHP is a ________ language.', 'options': ['server-side', 'client-side', 'both', 'none'], 'ans': 0},
        ],
        'medium': [
            {'q': 'What is the output of echo 5 + "5 apples";?', 'options': ['10', '55', '5', 'Error'], 'ans': 0},
            {'q': 'Which of the following is used for array declaration in PHP?', 'options': ['array()', '[]', 'Both', 'None'], 'ans': 2},
            {'q': 'What is the output of echo strlen("Hello World");?', 'options': ['10', '11', '12', '9'], 'ans': 1},
            {'q': 'Which function is used to start a session in PHP?', 'options': ['session_start()', 'start_session()', 'session()', 'begin_session()'], 'ans': 0},
            {'q': 'What is the output of echo 10 % 3;?', 'options': ['3', '1', '2', '0'], 'ans': 1},
        ],
        'hard': [
            {'q': 'What is the output of echo 5 + "10" + "5";?', 'options': ['20', '5105', '15', 'Error'], 'ans': 0},
            {'q': 'Which of the following is used for connecting to MySQL in PHP?', 'options': ['mysqli_connect()', 'mysql_connect()', 'PDO', 'All of the above'], 'ans': 3},
            {'q': 'What is the output of echo "Hello" . 5 + 3 . "World";?', 'options': ['Hello8World', 'Hello53World', 'Error', 'HelloWorld8'], 'ans': 3},
            {'q': 'Which function is used to sort an array in PHP?', 'options': ['sort()', 'rsort()', 'asort()', 'All of the above'], 'ans': 3},
            {'q': 'What is the output of echo 2 ** 3;?', 'options': ['6', '8', '9', 'Error'], 'ans': 1},
        ]
    }
}

@app.route('/mocktest', methods=['GET', 'POST'])
@login_required
def mocktest():
    if request.method == 'POST':
        subject = request.form.get('subject')
        difficulty = request.form.get('difficulty')
        
        if subject not in QUESTIONS or difficulty not in QUESTIONS[subject]:
            flash('Invalid subject or difficulty level', 'danger')
            return redirect(url_for('mocktest'))
        
        # load questions
        qs = QUESTIONS[subject][difficulty]
        return render_template('take_test.html', subject=subject, difficulty=difficulty, questions=qs, enumerate=enumerate)
    
    return render_template('mocktest.html', subjects=QUESTIONS.keys())

@app.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    subject = request.form.get('subject')
    difficulty = request.form.get('difficulty')
    
    if subject not in QUESTIONS or difficulty not in QUESTIONS[subject]:
        flash('Invalid test parameters', 'danger')
        return redirect(url_for('mocktest'))
    
    qs = QUESTIONS[subject][difficulty]
    score = 0
    for i, q in enumerate(qs):
        selected = request.form.get(f'q{i}')
        if selected is not None and int(selected) == q['ans']:
            score += 1
    total = len(qs)
    
    # store result
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO mock_results (user_id, subject, difficulty, score, total) VALUES (?, ?, ?, ?, ?)",
                (session['user_id'], subject, difficulty, score, total))
    conn.commit()
    conn.close()
    
    flash(f'Test submitted! You scored {score}/{total}', 'success')
    return render_template('result.html', score=score, total=total, subject=subject, difficulty=difficulty)

@app.route('/history')
@login_required
def history():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT subject, difficulty, score, total, date FROM mock_results WHERE user_id = ? ORDER BY date DESC",
                (session['user_id'],))
    results = cur.fetchall()
    ivs = conn.execute("SELECT * FROM interviews WHERE user_id=? AND status IN ('done','feedback') ORDER BY id DESC",
                       (session['user_id'],)).fetchall()
    conn.close()
    return render_template('history.html', results=results, interviews=ivs)


# =====================================================================
#  AI INTERVIEW  (camera + DeepFace emotions + liveness + grading)
# =====================================================================
SUBJECTS = ['python', 'java', 'php', 'general']
FRAME_MAX_BYTES = 1_500_000


def _own_interview(conn, iid, allow_staff=False):
    iv = conn.execute('SELECT * FROM interviews WHERE id=?', (iid,)).fetchone()
    if not iv:
        abort(404)
    if iv['user_id'] != session['user_id'] and not (allow_staff and session.get('role') in ('admin', 'hr')):
        abort(403)
    return iv


@app.route('/attend')
@login_required
def attend():
    live_ok, live_err = liveness.model_status()
    emo_ok, emo_err = emotion.status()
    return render_template('attend.html', subjects=SUBJECTS, live_ok=live_ok, emo_ok=emo_ok)


@app.route('/interview/start', methods=['POST'])
@login_required
def interview_start():
    subject = request.form.get('subject', 'general')
    if subject not in SUBJECTS:
        subject = 'general'
    qs = engine.pick_questions(subject)
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO interviews (user_id, subject, questions) VALUES (?, ?, ?)',
                (session['user_id'], subject, json.dumps(qs)))
    iid = cur.lastrowid
    conn.commit()
    conn.close()
    TRACKERS[iid] = liveness.LivenessTracker()
    return redirect(url_for('interview_page', iid=iid))


@app.route('/interview/<int:iid>')
@login_required
def interview_page(iid):
    conn = get_db()
    iv = _own_interview(conn, iid)
    conn.close()
    if iv['status'] == 'feedback':
        return redirect(url_for('interview_feedback', iid=iid))
    if iv['status'] == 'done':
        return redirect(url_for('interview_result', iid=iid))
    qs = [{'type': q['type'], 'q': q['q'], 'o': q['o']} for q in json.loads(iv['questions'])]   # correct answers stay on the server
    return render_template('interview.html', iv=iv, questions=qs)


@app.route('/api/interview/<int:iid>/frame', methods=['POST'])
@login_required
def api_frame(iid):
    conn = get_db()
    iv = _own_interview(conn, iid)
    if iv['status'] != 'in_progress':
        conn.close()
        return jsonify({'error': 'finished'}), 400
    data = request.get_json(silent=True) or {}
    img = data.get('image', '')
    q_idx = int(data.get('q', 0))
    if ',' in img:
        img = img.split(',', 1)[1]
    try:
        raw = base64.b64decode(img)
        if len(raw) > FRAME_MAX_BYTES:
            raise ValueError('too big')
        frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError('bad image')
    except Exception:
        conn.close()
        return jsonify({'error': 'bad image'}), 400

    tracker = TRACKERS.setdefault(iid, liveness.LivenessTracker())
    live = tracker.check(frame)

    face_found = live['face_count'] > 0
    multi = live['face_count'] > 1
    spoof = live['is_fake']
    emo = None
    emo_scores = None
    if face_found and not spoof:
        emo, emo_scores = emotion.analyze(frame, live['box'])

    conn.execute('''UPDATE interviews SET total_frames = total_frames + 1,
                    face_frames = face_frames + ?, spoof_frames = spoof_frames + ?,
                    multi_face_frames = multi_face_frames + ? WHERE id=?''',
                 (1 if face_found else 0, 1 if spoof else 0, 1 if multi else 0, iid))
    if emo:
        conn.execute('INSERT INTO emotion_samples (interview_id, q_idx, emotion) VALUES (?, ?, ?)',
                     (iid, q_idx, emo))
    conn.commit()
    conn.close()

    warning = None
    if not face_found:
        warning = 'No face detected - please face the camera.'
    elif multi:
        warning = 'Multiple faces detected - only the candidate should be in view.'
    elif tracker.fake_streak >= config.SPOOF_STRIKES_WARN:
        warning = 'Spoofing suspected (photo / screen / mask). This has been recorded.'
    return jsonify({'face': face_found, 'faces': live['face_count'], 'liveness': live['label'],
                    'confidence': round(live['confidence'] * 100, 1), 'fake': spoof,
                    'emotion': emo, 'scores': emo_scores, 'box': live['box'],
                    'frame_w': int(frame.shape[1]), 'frame_h': int(frame.shape[0]),
                    'warning': warning,
                    'models': {'liveness': liveness.model_status()[0], 'liveness_err': liveness.model_status()[1],
                               'emotion': emotion.status()[0], 'emotion_err': emotion.last_error or emotion.status()[1]}})


@app.route('/api/interview/<int:iid>/answer', methods=['POST'])
@login_required
def api_answer(iid):
    """Saves one selected option (autosave while the candidate answers)."""
    conn = get_db()
    iv = _own_interview(conn, iid)
    if iv['status'] != 'in_progress':
        conn.close()
        return jsonify({'error': 'finished'}), 400
    data = request.get_json(silent=True) or {}
    try:
        idx = int(data.get('idx'))
        choice = data.get('choice')
        choice = None if choice in (None, '') else int(choice)
    except (TypeError, ValueError):
        conn.close()
        return jsonify({'error': 'bad data'}), 400
    conn.execute("""INSERT INTO interview_answers (interview_id, idx, answer) VALUES (?, ?, ?)
                    ON CONFLICT(interview_id, idx) DO UPDATE SET answer=excluded.answer""",
                 (iid, idx, '' if choice is None else str(choice)))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/interview/<int:iid>/event', methods=['POST'])
@login_required
def api_event(iid):
    conn = get_db()
    iv = _own_interview(conn, iid)
    if (request.get_json(silent=True) or {}).get('type') == 'tab' and iv['status'] == 'in_progress':
        conn.execute('UPDATE interviews SET tab_switches = tab_switches + 1 WHERE id=?', (iid,))
        conn.commit()
    conn.close()
    return jsonify({'ok': True})


def integrity_flags(iv):
    flags = []
    ff = max(iv['face_frames'], 1)
    if iv['spoof_frames'] and iv['spoof_frames'] / ff > 0.10:
        flags.append(f"possible face spoofing in {iv['spoof_frames']} frames")
    if iv['multi_face_frames'] and iv['multi_face_frames'] / max(iv['total_frames'], 1) > 0.10:
        flags.append('multiple people seen in camera')
    if iv['tab_switches'] >= 3:
        flags.append(f"left the interview tab {iv['tab_switches']} times")
    if iv['total_frames'] and iv['face_frames'] / iv['total_frames'] < 0.6:
        flags.append('face was missing from camera for a large part of the interview')
    return flags


@app.route('/api/interview/<int:iid>/finish', methods=['POST'])
@login_required
def api_finish(iid):
    conn = get_db()
    iv = _own_interview(conn, iid)
    if iv['status'] != 'in_progress':
        conn.close()
        return jsonify({'redirect': url_for('interview_feedback', iid=iid)})
    qs = json.loads(iv['questions'])
    # answers sent with the submit request win over autosaved ones
    saved = {r['idx']: r['answer'] for r in
             conn.execute('SELECT idx, answer FROM interview_answers WHERE interview_id=?', (iid,))}
    sent = (request.get_json(silent=True) or {}).get('answers')
    if isinstance(sent, list):
        for i, c in enumerate(sent[:len(qs)]):
            saved[i] = '' if c in (None, '') else str(c)
    total = 0.0
    for i, q in enumerate(qs):
        raw = saved.get(i, '')
        try:
            g = engine.grade_mcq(q, raw if raw != '' else None)
        except ValueError:
            g = engine.grade_mcq(q, None)
        total += g['marks']
        conn.execute("""INSERT INTO interview_answers (interview_id, idx, answer, marks, detail) VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(interview_id, idx) DO UPDATE SET answer=excluded.answer, marks=excluded.marks, detail=excluded.detail""",
                     (iid, i, raw, g['marks'], json.dumps(g)))
    counts = {}
    for r in conn.execute('SELECT emotion, COUNT(*) c FROM emotion_samples WHERE interview_id=? GROUP BY emotion', (iid,)):
        counts[r['emotion']] = r['c']
    iv = conn.execute('SELECT * FROM interviews WHERE id=?', (iid,)).fetchone()
    pers = emotion.personality_score(counts, iv['total_frames'], iv['face_frames'],
                                     iv['spoof_frames'], iv['multi_face_frames'], iv['tab_switches'])
    interview_total = len(qs) * engine.MARKS_PER_Q
    overall = round(total / interview_total * 50 + pers['total'], 1)       # 50 + 50 = 100
    conn.execute("""UPDATE interviews SET status='feedback', finished_at=CURRENT_TIMESTAMP,
                    interview_marks=?, interview_total=?, personality_marks=?, personality_json=?,
                    overall_pct=?, grade=? WHERE id=?""",
                 (round(total, 1), interview_total, pers['total'], json.dumps(pers), overall,
                  engine.grade_letter(overall), iid))
    conn.commit()
    conn.close()
    TRACKERS.pop(iid, None)
    return jsonify({'redirect': url_for('interview_feedback', iid=iid)})


@app.route('/interview/<int:iid>/feedback', methods=['GET', 'POST'])
@login_required
def interview_feedback(iid):
    conn = get_db()
    iv = _own_interview(conn, iid)
    if iv['status'] == 'in_progress':
        conn.close()
        return redirect(url_for('interview_page', iid=iid))
    if iv['status'] == 'done':
        conn.close()
        return redirect(url_for('interview_result', iid=iid))
    if request.method == 'POST':
        try:
            rating = max(1, min(5, int(request.form.get('rating', 0))))
        except ValueError:
            rating = 0
        if not rating:
            flash('Please choose a rating', 'warning')
        else:
            conn.execute("UPDATE interviews SET feedback_rating=?, feedback_text=?, status='done' WHERE id=?",
                         (rating, request.form.get('comments', '').strip()[:1500], iid))
            conn.commit()
            conn.close()
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('interview_result', iid=iid))
    conn.close()
    return render_template('interview_feedback.html', iv=iv)


@app.route('/interview/<int:iid>/result')
@login_required
def interview_result(iid):
    conn = get_db()
    iv = _own_interview(conn, iid, allow_staff=True)
    if iv['status'] != 'done':
        conn.close()
        if iv['user_id'] == session['user_id']:
            return redirect(url_for('interview_feedback' if iv['status'] == 'feedback' else 'interview_page', iid=iid))
        abort(404)
    user = conn.execute('SELECT * FROM users WHERE id=?', (iv['user_id'],)).fetchone()
    qs = json.loads(iv['questions'])
    rows = {r['idx']: r for r in conn.execute('SELECT * FROM interview_answers WHERE interview_id=?', (iid,))}
    answers = []
    for i, q in enumerate(qs):
        r = rows.get(i)
        d = json.loads(r['detail']) if r and r['detail'] else {}
        if 'o' in q:      # MCQ interview
            g = d or engine.grade_mcq(q, None)
            answers.append({'q': q['q'], 'type': q['type'], 'options': q['o'], 'explanation': q.get('e', ''), **g})
        else:             # interview taken with the earlier text-answer version
            answers.append({'q': q['q'], 'type': q['type'], 'options': None, 'explanation': q.get('model', ''),
                            'marks': (r['marks'] if r else 0), 'correct': (r['marks'] if r else 0) >= 7,
                            'choice': None, 'ans': None, 'comment': d.get('comment', ''),
                            'text_answer': (r['answer'] if r else '')})
    counts = {}
    for r in conn.execute('SELECT emotion, COUNT(*) c FROM emotion_samples WHERE interview_id=? GROUP BY emotion', (iid,)):
        counts[r['emotion']] = r['c']
    per_q = {}
    for r in conn.execute('SELECT q_idx, emotion, COUNT(*) c FROM emotion_samples WHERE interview_id=? GROUP BY q_idx, emotion', (iid,)):
        per_q.setdefault(r['q_idx'], {})[r['emotion']] = r['c']
    mock = conn.execute('SELECT AVG(score*100.0/total) a, COUNT(*) n FROM mock_results WHERE user_id=?',
                        (iv['user_id'],)).fetchone()
    conn.close()
    pers = json.loads(iv['personality_json']) if iv['personality_json'] else {}
    flags = integrity_flags(iv)
    strengths, improve = engine.build_feedback(
        iv['interview_marks'] / max(iv['interview_total'], 1) * 100, pers, answers, flags)
    return render_template('interview_result.html', iv=iv, user=user, answers=answers, pers=pers,
                           counts=counts, per_q=per_q, flags=flags, strengths=strengths, improve=improve,
                           mock_avg=mock['a'], mock_n=mock['n'],
                           interview_pct=round(iv['interview_marks'] / max(iv['interview_total'], 1) * 100, 1),
                           per_q_marks=engine.MARKS_PER_Q,
                           emotions=emotion.EMOTIONS)


# =====================================================================
#  HR / ADMIN
# =====================================================================
def candidate_rows(conn):
    rows = []
    for u in conn.execute("SELECT * FROM users WHERE COALESCE(role,'candidate')='candidate' ORDER BY id DESC"):
        mock = conn.execute('SELECT AVG(score*100.0/total) a, COUNT(*) n FROM mock_results WHERE user_id=?',
                            (u['id'],)).fetchone()
        iv = conn.execute("SELECT * FROM interviews WHERE user_id=? AND status='done' ORDER BY id DESC LIMIT 1",
                          (u['id'],)).fetchone()
        rows.append({'u': u, 'mock_avg': mock['a'], 'mock_n': mock['n'], 'iv': iv,
                     'flags': integrity_flags(iv) if iv else []})
    return rows


@app.route('/admin')
@login_required
@staff_required
def admin():
    conn = get_db()
    cands = candidate_rows(conn)
    all_results = conn.execute('''
        SELECT users.username, mock_results.subject, mock_results.difficulty, mock_results.score,
               mock_results.total, mock_results.date
        FROM mock_results JOIN users ON mock_results.user_id = users.id
        ORDER BY mock_results.date DESC''').fetchall()
    hr_users = conn.execute("SELECT id, username, email FROM users WHERE role='hr'").fetchall()
    mails = conn.execute('''SELECT n.*, u.username FROM notifications n LEFT JOIN users u ON u.id=n.user_id
                            ORDER BY n.id DESC LIMIT 30''').fetchall()
    conn.close()
    return render_template('admin.html', results=all_results, cands=cands, hr_users=hr_users, mails=mails,
                           smtp_ok=mailer.smtp_configured(), mail_from=config.MAIL_FROM)


def _shortlist_mail(user, job, message, marks_line):
    login_url = request.host_url.rstrip('/') + url_for('login')
    name = user['full_name'] or user['username']
    subject = f'Congratulations! You are shortlisted - {job}'
    text = (f'Dear {name},\n\nGood news! You have been shortlisted for the position: {job}.\n\n'
            f'{message}\n\n{marks_line}\n'
            f'Log in to your candidate account to view the details: {login_url}\n\n'
            f'Regards,\nHR Team')
    html = (f'<div style="font-family:Arial,sans-serif;max-width:560px">'
            f'<h2 style="color:#4f46e5">Congratulations, {name}! 🎉</h2>'
            f'<p>You have been <b>shortlisted</b> for the position: <b>{job}</b>.</p>'
            f'<p style="white-space:pre-line">{message}</p><p>{marks_line}</p>'
            f'<p><a href="{login_url}" style="background:#4f46e5;color:#fff;padding:10px 18px;'
            f'border-radius:8px;text-decoration:none">View in candidate login</a></p>'
            f'<p style="color:#666">Regards,<br>HR Team</p></div>')
    return subject, text, html


@app.route('/admin/shortlist', methods=['POST'])
@login_required
@staff_required
def admin_shortlist():
    ids = [int(i) for i in request.form.getlist('user_ids') if i.isdigit()]
    job = request.form.get('job_title', '').strip() or 'Open Position'
    message = request.form.get('message', '').strip() or 'Our HR team will contact you shortly with the next steps.'
    send = request.form.get('send_email') == 'on'
    if not ids:
        flash('Select at least one candidate', 'warning')
        return redirect(url_for('admin'))
    conn = get_db()
    ok_n = fail_n = 0
    for uid in ids:
        u = conn.execute("SELECT * FROM users WHERE id=? AND COALESCE(role,'candidate')='candidate'", (uid,)).fetchone()
        if not u:
            continue
        conn.execute("UPDATE users SET shortlisted=1, shortlist_job=?, shortlisted_at=CURRENT_TIMESTAMP WHERE id=?",
                     (job, uid))
        iv = conn.execute("SELECT * FROM interviews WHERE user_id=? AND status='done' ORDER BY id DESC LIMIT 1",
                          (uid,)).fetchone()
        marks_line = (f"Your interview result: {iv['overall_pct']}/100 (Grade {iv['grade']})." if iv else '')
        status = 'not emailed'
        if send:
            subject, text, html = _shortlist_mail(u, job, message, marks_line)
            ok, info = mailer.send_mail(u['email'], subject, text, html)
            status = 'sent' if ok else f'failed: {info}'
            ok_n += ok
            fail_n += (not ok)
        conn.execute('INSERT INTO notifications (user_id, title, message, email_status, created_by) VALUES (?,?,?,?,?)',
                     (uid, f'Shortlisted for {job}', message, status, session['username']))
    conn.commit()
    conn.close()
    flash(f'Shortlisted {len(ids)} candidate(s).' +
          (f' E-mails sent: {ok_n}, failed: {fail_n} (see E-mail log).' if send else ''),
          'success' if not fail_n else 'warning')
    return redirect(url_for('admin') + '#candidates')


@app.route('/admin/unshortlist/<int:uid>', methods=['POST'])
@login_required
@staff_required
def admin_unshortlist(uid):
    conn = get_db()
    conn.execute('UPDATE users SET shortlisted=0, shortlist_job=NULL, shortlisted_at=NULL WHERE id=?', (uid,))
    conn.commit()
    conn.close()
    flash('Removed from shortlist', 'info')
    return redirect(url_for('admin') + '#candidates')


@app.route('/admin/hr/create', methods=['POST'])
@login_required
@admin_only
def admin_create_hr():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    email = request.form.get('email', '').strip()
    if not username or len(password) < 6:
        flash('HR username and a password of 6+ characters are required', 'danger')
        return redirect(url_for('admin') + '#hr')
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, password, email, role, is_admin) VALUES (?,?,?,'hr',0)",
                     (username, generate_password_hash(password), email))
        conn.commit()
        flash(f'HR account "{username}" created', 'success')
    except sqlite3.IntegrityError:
        flash('Username already exists', 'danger')
    conn.close()
    return redirect(url_for('admin') + '#hr')


@app.route('/admin/test_email', methods=['POST'])
@login_required
@admin_only
def admin_test_email():
    to = request.form.get('to', '').strip()
    if not EMAIL_RE.match(to):
        flash('Enter a valid e-mail address', 'danger')
    else:
        ok, info = mailer.send_mail(to, 'Test e-mail - AI Interview System',
                                    'SMTP is working. This is a test message from the admin panel.')
        flash('Test e-mail sent to ' + to if ok else 'Test e-mail failed: ' + info, 'success' if ok else 'danger')
    return redirect(url_for('admin') + '#email')


# ---------- run ----------
if __name__ == '__main__':
    app.run(debug=True,use_reloader=False)
