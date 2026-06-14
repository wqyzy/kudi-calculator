"""
库迪咖啡 · 在线协作财务计算器
Flask + SQLite 后端
"""

import os
import json
import uuid
import random
import string
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ========== Database ==========

def get_db_path():
    """获取可写的数据库路径"""
    # 优先使用环境变量
    env_path = os.environ.get('DATABASE_PATH')
    if env_path:
        return env_path

    # 尝试当前目录
    candidates = [
        os.path.join(os.getcwd(), 'data.db'),
        os.path.join('/tmp', 'kudi_calculator.db'),
        '/tmp/kudi_calculator.db',
    ]

    for path in candidates:
        try:
            # 测试是否可写
            if os.path.exists(path):
                # 文件已存在，测试可写
                with open(path, 'a') as f:
                    pass
            else:
                # 文件不存在，测试目录可写
                dir_path = os.path.dirname(path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                with open(path, 'w') as f:
                    f.write('')
                os.remove(path)
            return path
        except (IOError, OSError):
            continue

    # 终极 fallback
    return '/tmp/kudi_calculator.db'


DB_PATH = get_db_path()
print(f"[startup] DB_PATH = {DB_PATH}")


def get_conn():
    """获取数据库连接，自动建表"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
    return conn


def generate_code():
    """生成6位分享码"""
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    conn = get_conn()
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
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO projects (code, name, data) VALUES (?, ?, ?)",
            (code, name, '{}')
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[error] create failed: {e}")
        return render_template('index.html', error=f'创建项目失败: {e}')
    return redirect(url_for('view_project', code=code))


@app.route('/join', methods=['POST'])
def join():
    code = request.form.get('code', '').strip().upper()
    if not code:
        return render_template('index.html', error='请输入分享码')
    try:
        conn = get_conn()
        cur = conn.execute("SELECT 1 FROM projects WHERE code=?", (code,))
        exists = cur.fetchone() is not None
        conn.close()
        if exists:
            return redirect(url_for('view_project', code=code))
    except Exception as e:
        print(f"[error] join failed: {e}")
    return render_template('index.html', error=f'找不到分享码 "{code}"，请检查后重试')


@app.route('/view/<code>')
def view_project(code):
    code = code.upper()
    try:
        conn = get_conn()
        cur = conn.execute("SELECT * FROM projects WHERE code=?", (code,))
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        print(f"[error] view failed: {e}")
        return render_template('index.html', error=f'读取项目失败: {e}')

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
    try:
        conn = get_conn()
        cur = conn.execute("SELECT data FROM projects WHERE code=?", (code,))
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        print(f"[error] api_load: {e}")
        return jsonify({'error': str(e)}), 500

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

    try:
        conn = get_conn()
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
    except Exception as e:
        print(f"[error] api_save: {e}")
        return jsonify({'error': str(e)}), 500


# ========== Main ==========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
