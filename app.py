"""
库迪咖啡 · 在线协作财务计算器
Flask + SQLite 后端
"""

import os
import json
import uuid
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            code TEXT PRIMARY KEY,
            name TEXT DEFAULT '',
            data TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def generate_code():
    """生成6位分享码"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    # 去掉易混淆的字符
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    conn = get_db()
    for _ in range(100):
        code = ''.join(random.choices(chars, k=6))
        cur = conn.execute("SELECT 1 FROM projects WHERE code=?", (code,))
        if not cur.fetchone():
            conn.close()
            return code
    conn.close()
    return str(uuid.uuid4())[:6].upper()


# ========== Routes ==========

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create', methods=['POST'])
def create():
    name = request.form.get('name', '').strip() or '未命名项目'
    code = generate_code()
    conn = get_db()
    conn.execute(
        "INSERT INTO projects (code, name, data) VALUES (?, ?, ?)",
        (code, name, '{}')
    )
    conn.commit()
    conn.close()
    return redirect(url_for('view_project', code=code))


@app.route('/join', methods=['POST'])
def join():
    code = request.form.get('code', '').strip().upper()
    conn = get_db()
    cur = conn.execute("SELECT 1 FROM projects WHERE code=?", (code,))
    if cur.fetchone():
        conn.close()
        return redirect(url_for('view_project', code=code))
    conn.close()
    return render_template('index.html', error=f'找不到分享码 "{code}"，请检查后重试')


@app.route('/view/<code>')
def view_project(code):
    code = code.upper()
    conn = get_db()
    cur = conn.execute("SELECT * FROM projects WHERE code=?", (code,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return render_template('index.html', error=f'项目不存在: {code}')
    try:
        data = json.loads(row['data']) if row['data'] else {}
    except:
        data = {}
    return render_template('calculator.html', code=code, name=row['name'], data=data)


# ========== API ==========

@app.route('/api/load/<code>')
def api_load(code):
    code = code.upper()
    conn = get_db()
    cur = conn.execute("SELECT data FROM projects WHERE code=?", (code,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'not found'}), 404
    try:
        data = json.loads(row['data']) if row['data'] else {}
    except:
        data = {}
    return jsonify({'code': code, 'data': data})


@app.route('/api/save/<code>', methods=['POST'])
def api_save(code):
    code = code.upper()
    data = request.get_json(force=True)
    if data is None:
        return jsonify({'error': 'invalid data'}), 400
    conn = get_db()
    cur = conn.execute("SELECT 1 FROM projects WHERE code=?", (code,))
    if not cur.fetchone():
        conn.close()
        return jsonify({'error': 'not found'}), 404
    conn.execute(
        "UPDATE projects SET data = ?, updated_at = datetime('now') WHERE code = ?",
        (json.dumps(data, ensure_ascii=False), code)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'code': code})


# ========== Main ==========

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
