from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "site.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with open(os.path.join(APP_DIR, "schema.sql"), "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()

# Startup-time init
if not os.path.exists(DB_PATH):
    open(DB_PATH, 'a').close()
with app.app_context():
    init_db()

def current_user():
    if 'user_id' in session:
        db = get_db()
        return db.execute("SELECT * FROM members WHERE id=?", (session['user_id'],)).fetchone()
    return None

def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("請先登入", "warning")
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    if current_user():
        return redirect(url_for('members'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        name = request.form['name'].strip()
        level = request.form['level']
        sponsor_id = request.form.get('sponsor_id')
        sponsor_id = int(sponsor_id) if sponsor_id else None
        if not username or not password or not name:
            flash("請完整填寫資料", "danger")
            return redirect(url_for('register'))
        if sponsor_id:
            exists = db.execute("SELECT 1 FROM members WHERE id=?", (sponsor_id,)).fetchone()
            if not exists:
                flash("推薦人ID不存在", "danger")
                return redirect(url_for('register'))
        try:
            db.execute(
                "INSERT INTO members (username,password_hash,name,level,sponsor_id) VALUES (?,?,?,?,?)",
                (username, generate_password_hash(password), name, level, sponsor_id)
            )
            db.commit()
            flash("註冊成功，請登入", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("帳號已存在，請改用其他帳號", "danger")
            return redirect(url_for('register'))
    members = db.execute("SELECT id,name,level FROM members ORDER BY id DESC LIMIT 50").fetchall()
    return render_template('register.html', members=members, me=current_user())

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM members WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash("登入成功","success")
            return redirect(url_for('members'))
        flash("帳號或密碼錯誤","danger")
    return render_template('login.html', me=current_user())

@app.route('/logout')
def logout():
    session.clear()
    flash("已登出","info")
    return redirect(url_for('login'))

@app.route('/members')
@login_required
def members():
    db = get_db()
    rows = db.execute("SELECT m.id, m.username, m.name, m.level, m.created_at, s.name AS sponsor_name FROM members m LEFT JOIN members s ON s.id = m.sponsor_id ORDER BY m.id DESC").fetchall()
    return render_template('members.html', rows=rows, me=current_user())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
