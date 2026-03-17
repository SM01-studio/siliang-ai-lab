"""
SQLite 数据库模型
"""
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'siliang.db')


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = get_db()
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')

    # 会话表（用于记住登录状态）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 密码重置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 应用表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            url TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户应用权限表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_app_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            app_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (app_id) REFERENCES apps (id),
            UNIQUE(user_id, app_id)
        )
    ''')

    conn.commit()

    # 迁移：添加 expires_at 字段（如果不存在）
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN expires_at TIMESTAMP")
        conn.commit()
    except:
        pass  # 字段已存在

    # 迁移：创建 user_app_permissions 表（如果不存在）
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_app_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                app_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (app_id) REFERENCES apps (id),
                UNIQUE(user_id, app_id)
            )
        ''')
        conn.commit()
    except:
        pass  # 表已存在

    conn.close()


class User:
    """用户模型"""

    @staticmethod
    def create(username, email, password, role='user', expires_at=None):
        """创建用户"""
        conn = get_db()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, role, expires_at) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, role, expires_at)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError as e:
            conn.close()
            if 'username' in str(e):
                raise ValueError('用户名已存在')
            elif 'email' in str(e):
                raise ValueError('邮箱已被注册')
            raise ValueError('注册失败')

    @staticmethod
    def get_by_id(user_id):
        """通过ID获取用户"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def get_by_email(email):
        """通过邮箱获取用户"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def get_by_username(username):
        """通过用户名获取用户"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def verify_password(email, password):
        """验证密码"""
        user = User.get_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    @staticmethod
    def update_password(user_id, new_password):
        """更新密码"""
        conn = get_db()
        cursor = conn.cursor()
        password_hash = generate_password_hash(new_password)
        cursor.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (password_hash, user_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_last_login(user_id):
        """更新最后登录时间"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (datetime.now(), user_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        """获取所有用户"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role, is_active, created_at, last_login, expires_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return [dict(user) for user in users]

    @staticmethod
    def delete(user_id):
        """删除用户"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def toggle_active(user_id):
        """切换用户激活状态"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET is_active = NOT is_active WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()


class Session:
    """会话模型"""

    @staticmethod
    def create(user_id, token, expires_hours=24):
        """创建会话"""
        conn = get_db()
        cursor = conn.cursor()
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        cursor.execute(
            'INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, token, expires_at)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_token(token):
        """通过token获取会话"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, u.username, u.email, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ? AND u.is_active = 1
        ''', (token, datetime.now()))
        session = cursor.fetchone()
        conn.close()
        return dict(session) if session else None

    @staticmethod
    def delete(token):
        """删除会话（登出）"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()
        conn.close()

    @staticmethod
    def delete_by_user(user_id):
        """删除用户所有会话"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()


class PasswordReset:
    """密码重置模型"""

    @staticmethod
    def create(user_id, token, expires_hours=1):
        """创建密码重置请求"""
        conn = get_db()
        cursor = conn.cursor()
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        cursor.execute(
            'INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, token, expires_at)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_token(token):
        """通过token获取重置请求"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pr.*, u.email
            FROM password_resets pr
            JOIN users u ON pr.user_id = u.id
            WHERE pr.token = ? AND pr.expires_at > ? AND pr.used = 0
        ''', (token, datetime.now()))
        reset = cursor.fetchone()
        conn.close()
        return dict(reset) if reset else None

    @staticmethod
    def mark_used(token):
        """标记为已使用"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE password_resets SET used = 1 WHERE token = ?', (token,))
        conn.commit()
        conn.close()


class App:
    """应用模型"""

    @staticmethod
    def get_all():
        """获取所有启用的应用"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM apps WHERE is_active = 1 ORDER BY sort_order')
        apps = cursor.fetchall()
        conn.close()
        return [dict(app) for app in apps]

    @staticmethod
    def get_by_id(app_id):
        """通过ID获取应用"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM apps WHERE id = ?', (app_id,))
        app = cursor.fetchone()
        conn.close()
        return dict(app) if app else None

    @staticmethod
    def get_for_user(user_id, is_admin=False):
        """获取用户可访问的应用（管理员可访问所有）"""
        conn = get_db()
        cursor = conn.cursor()

        if is_admin:
            # 管理员可以访问所有应用
            cursor.execute('SELECT * FROM apps WHERE is_active = 1 ORDER BY sort_order')
        else:
            # 普通用户只能访问被分配的应用
            cursor.execute('''
                SELECT a.* FROM apps a
                JOIN user_app_permissions uap ON a.id = uap.app_id
                WHERE uap.user_id = ? AND a.is_active = 1
                ORDER BY a.sort_order
            ''', (user_id,))

        apps = cursor.fetchall()
        conn.close()
        return [dict(app) for app in apps]


class UserAppPermission:
    """用户应用权限模型"""

    @staticmethod
    def get_user_permissions(user_id):
        """获取用户的所有应用权限"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT app_id FROM user_app_permissions WHERE user_id = ?',
            (user_id,)
        )
        permissions = cursor.fetchall()
        conn.close()
        return [p['app_id'] for p in permissions]

    @staticmethod
    def set_user_permissions(user_id, app_ids):
        """设置用户的应用权限（替换原有权限）"""
        conn = get_db()
        cursor = conn.cursor()

        # 删除原有权限
        cursor.execute('DELETE FROM user_app_permissions WHERE user_id = ?', (user_id,))

        # 添加新权限
        for app_id in app_ids:
            cursor.execute(
                'INSERT OR IGNORE INTO user_app_permissions (user_id, app_id) VALUES (?, ?)',
                (user_id, app_id)
            )

        conn.commit()
        conn.close()

    @staticmethod
    def add_permission(user_id, app_id):
        """添加单个权限"""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO user_app_permissions (user_id, app_id) VALUES (?, ?)',
                (user_id, app_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # 权限已存在
        conn.close()

    @staticmethod
    def remove_permission(user_id, app_id):
        """移除单个权限"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM user_app_permissions WHERE user_id = ? AND app_id = ?',
            (user_id, app_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_permissions():
        """获取所有用户的权限（用于管理页面）"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT uap.user_id, uap.app_id, a.name as app_name
            FROM user_app_permissions uap
            JOIN apps a ON uap.app_id = a.id
        ''')
        permissions = cursor.fetchall()
        conn.close()
        return [dict(p) for p in permissions]


# 初始化数据库
if __name__ == '__main__':
    init_db()
    seed_apps()
    print('数据库初始化完成')


def seed_apps():
    """添加示例应用数据"""
    conn = get_db()
    cursor = conn.cursor()

    # 检查是否已有应用
    cursor.execute('SELECT COUNT(*) FROM apps')
    count = cursor.fetchone()[0]

    if count == 0:
        # 添加示例应用
        sample_apps = [
            {
                'name': 'AI Writer',
                'description': '超级 AI 公众号文章自动化写作助手，支持从深度调研到排版的全流程自动化。',
                'image_url': '/images/ai-writer.png',
                'url': 'https://writer.siliang.cfd',
                'sort_order': 1
            },
            {
                'name': 'ArchiAudit',
                'description': 'AI 住宅建筑平面图专项审核软件，智能识别并审核建筑图纸。',
                'image_url': '/images/archiaudit.png',
                'url': 'https://archi.siliang.cfd',
                'sort_order': 2
            }
        ]

        for app in sample_apps:
            cursor.execute('''
                INSERT INTO apps (name, description, image_url, url, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (app['name'], app['description'], app['image_url'], app['url'], app['sort_order']))

        conn.commit()
        print(f'已添加 {len(sample_apps)} 个示例应用')

    conn.close()
