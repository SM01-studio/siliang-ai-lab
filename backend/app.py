"""
Siliang AI LAB - Flask 主应用
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import secrets
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, User, Session, PasswordReset, App, UserAppPermission, seed_apps

app = Flask(__name__)

# CORS 配置 - 允许主门户和子网站访问
ALLOWED_ORIGINS = [
    'https://siliang.cfd',
    'https://writer.siliang.cfd',
    'http://localhost:8080',
    'http://localhost:5000',
    'http://127.0.0.1:8080'
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# 配置
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为 False

# 前端静态文件目录
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web')


# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'service': 'siliang-ai-lab'})


# ==================== 静态文件路由 ====================

@app.route('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(WEB_DIR, filename)


# ==================== 认证 API ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # 验证
    if not username or len(username) < 3:
        return jsonify({'error': '用户名至少3个字符'}), 400
    if not email or '@' not in email:
        return jsonify({'error': '请输入有效的邮箱地址'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400

    try:
        user_id = User.create(username, email, password)
        return jsonify({'message': '注册成功', 'user_id': user_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()

    email = data.get('email', '').strip()
    password = data.get('password', '')

    user = User.verify_password(email, password)

    if not user:
        return jsonify({'error': '邮箱或密码错误'}), 401

    if not user['is_active']:
        return jsonify({'error': '账户已被禁用'}), 403

    # 生成 token
    token = secrets.token_urlsafe(32)
    Session.create(user['id'], token)
    User.update_last_login(user['id'])

    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        Session.delete(token)
    return jsonify({'message': '已登出'})


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token:
        return jsonify({'error': '未登录'}), 401

    session = Session.get_by_token(token)
    if not session:
        return jsonify({'error': '会话已过期'}), 401

    return jsonify({
        'user': {
            'id': session['user_id'],
            'username': session['username'],
            'email': session['email'],
            'role': session['role']
        }
    })


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """请求密码重置"""
    data = request.get_json()
    email = data.get('email', '').strip()

    user = User.get_by_email(email)
    if not user:
        # 为了安全，不透露邮箱是否存在
        return jsonify({'message': '如果该邮箱已注册，您将收到重置邮件'})

    # 生成重置 token
    token = secrets.token_urlsafe(32)
    PasswordReset.create(user['id'], token)

    # TODO: 发送邮件（开发阶段先返回 token）
    # 实际部署时需要配置邮件服务
    return jsonify({
        'message': '如果该邮箱已注册，您将收到重置邮件',
        'dev_token': token  # 仅开发环境
    })


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    data = request.get_json()
    token = data.get('token', '')
    new_password = data.get('password', '')

    if len(new_password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400

    reset = PasswordReset.get_by_token(token)
    if not reset:
        return jsonify({'error': '重置链接无效或已过期'}), 400

    User.update_password(reset['user_id'], new_password)
    PasswordReset.mark_used(token)
    Session.delete_by_user(reset['user_id'])

    return jsonify({'message': '密码重置成功'})


# ==================== 应用 API ====================

@app.route('/api/apps', methods=['GET'])
def get_apps():
    """获取用户可访问的应用（管理员可访问所有，普通用户只能访问被分配的应用）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    is_admin = session and session['role'] == 'admin'
    user_id = session['user_id'] if session else None

    apps = App.get_for_user(user_id, is_admin)
    return jsonify({'apps': apps})


# ==================== 管理员 API ====================

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    """获取所有用户（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    users = User.get_all()
    return jsonify({'users': users})


@app.route('/api/admin/users/<int:user_id>/toggle', methods=['POST'])
def admin_toggle_user(user_id):
    """启用/禁用用户（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    User.toggle_active(user_id)
    return jsonify({'message': '状态已更新'})


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    """删除用户（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    if user_id == session['user_id']:
        return jsonify({'error': '不能删除自己'}), 400

    User.delete(user_id)
    return jsonify({'message': '用户已删除'})


@app.route('/api/admin/users', methods=['POST'])
def admin_create_user():
    """创建用户（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')
    expires_at = data.get('expires_at')  # 格式: YYYY-MM-DD

    # 验证
    if not username or len(username) < 3:
        return jsonify({'error': '用户名至少3个字符'}), 400
    if not email or '@' not in email:
        return jsonify({'error': '请输入有效的邮箱地址'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400

    try:
        user_id = User.create(username, email, password, role, expires_at)
        return jsonify({'message': '用户创建成功', 'user_id': user_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/admin/users/<int:user_id>/permissions', methods=['GET'])
def admin_get_user_permissions(user_id):
    """获取用户的应用权限（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    permissions = UserAppPermission.get_user_permissions(user_id)
    return jsonify({'permissions': permissions})


@app.route('/api/admin/users/<int:user_id>/permissions', methods=['POST'])
def admin_set_user_permissions(user_id):
    """设置用户的应用权限（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    data = request.get_json()
    app_ids = data.get('app_ids', [])

    # 验证 app_ids 是有效的整数列表
    try:
        app_ids = [int(aid) for aid in app_ids]
    except (ValueError, TypeError):
        return jsonify({'error': '无效的应用ID'}), 400

    UserAppPermission.set_user_permissions(user_id, app_ids)
    return jsonify({'message': '权限已更新'})


@app.route('/api/admin/apps', methods=['GET'])
def admin_get_all_apps():
    """获取所有应用（管理员，包括未启用的）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    apps = App.get_all()
    return jsonify({'apps': apps})


@app.route('/api/admin/apps/<int:app_id>/toggle', methods=['POST'])
def admin_toggle_app(app_id):
    """启用/禁用应用（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    App.toggle_active(app_id)
    return jsonify({'message': '应用状态已更新'})


# ==================== 文件管理 API ====================

import requests

# 应用 API 地址配置
APP_API_URLS = {
    'ai-writer': 'http://127.0.0.1:5001/api/admin',
    'archiaudit': 'http://127.0.0.1:5003/api/admin',
    'colorinsight': 'http://127.0.0.1:5002/api/admin',
}


@app.route('/api/admin/files', methods=['GET'])
def admin_get_files():
    """管理员：获取各应用的文件列表"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    app_name = request.args.get('app', 'ai-writer')

    if app_name not in APP_API_URLS:
        return jsonify({'error': f'未知应用: {app_name}'}), 400

    try:
        # 调用对应应用的管理员 API
        api_url = f"{APP_API_URLS[app_name]}/sessions"
        response = requests.get(api_url, timeout=30)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'应用 API 错误: {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接应用: {str(e)}'}), 500


@app.route('/api/admin/files/<app_name>/<session_id>', methods=['DELETE'])
def admin_delete_file(app_name, session_id):
    """管理员：删除指定会话的文件"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    if app_name not in APP_API_URLS:
        return jsonify({'error': f'未知应用: {app_name}'}), 400

    try:
        api_url = f"{APP_API_URLS[app_name]}/sessions/{session_id}"
        response = requests.delete(api_url, timeout=30)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'删除失败: {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接应用: {str(e)}'}), 500


@app.route('/api/admin/files/<app_name>/<session_id>/download', methods=['GET'])
def admin_download_files(app_name, session_id):
    """管理员：下载会话文件（代理到子应用）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    if app_name not in APP_API_URLS:
        return jsonify({'error': f'未知应用: {app_name}'}), 400

    try:
        api_url = f"{APP_API_URLS[app_name]}/sessions/{session_id}/download"
        response = requests.get(api_url, timeout=60, stream=True)

        if response.status_code == 200:
            from io import BytesIO
            buf = BytesIO(response.content)
            from flask import send_file
            return send_file(buf, mimetype='application/zip', as_attachment=True,
                           download_name=f'{app_name}_{session_id}.zip')
        else:
            return jsonify({'error': f'下载失败: {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接应用: {str(e)}'}), 500


@app.route('/api/admin/files/batch-delete', methods=['POST'])
def admin_batch_delete_files():
    """管理员：批量删除文件"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = Session.get_by_token(token)

    if not session or session['role'] != 'admin':
        return jsonify({'error': '无权限'}), 403

    data = request.json
    app_name = data.get('app', 'ai-writer')
    session_ids = data.get('session_ids', [])

    if not session_ids:
        return jsonify({'error': '未提供要删除的会话ID'}), 400

    if app_name not in APP_API_URLS:
        return jsonify({'error': f'未知应用: {app_name}'}), 400

    try:
        api_url = f"{APP_API_URLS[app_name]}/sessions/batch-delete"
        response = requests.post(api_url, json={'session_ids': session_ids}, timeout=60)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'批量删除失败: {response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'无法连接应用: {str(e)}'}), 500


# ==================== 初始化 ====================

def create_admin():
    """创建默认管理员账户"""
    admin = User.get_by_email('admin@siliang.cfd')
    if not admin:
        User.create('admin', 'admin@siliang.cfd', 'admin123', role='admin')
        print('默认管理员账户已创建: admin@siliang.cfd / admin123')


if __name__ == '__main__':
    init_db()
    seed_apps()
    create_admin()
    print('🚀 Siliang AI LAB 启动中...')
    print('📍 访问地址: http://localhost:5000')
    app.run(debug=True, port=5000)
