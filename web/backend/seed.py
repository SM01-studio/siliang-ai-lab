"""
数据库初始化脚本
运行此脚本初始化数据库并插入初始数据
"""
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db


def seed_apps():
    """插入应用初始数据"""
    apps = [
        {
            'name': 'AI Writer',
            'description': '超级 AI 公众号文章自动化写作助手，支持从深度调研、大纲设计、内容撰写到多格式排版的全流程自动化。',
            'image_url': '/images/ai-writer.png',
            'url': 'https://siliang.cfd/',
            'sort_order': 1
        },
        {
            'name': 'ArchiAudit',
            'description': 'AI 住宅建筑平面图专项审核软件，智能识别并审核建筑图纸。',
            'image_url': '/images/archiaudit.png',
            'url': 'https://archiaudit.siliang.cfd/',  # 待部署
            'sort_order': 2
        }
    ]

    conn = get_db()
    cursor = conn.cursor()

    for app in apps:
        try:
            cursor.execute('''
                INSERT INTO apps (name, description, image_url, url, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (app['name'], app['description'], app['image_url'], app['url'], app['sort_order']))
        except Exception as e:
            print(f'插入应用 {app["name"]} 失败: {e}')

    conn.commit()
    conn.close()
    print('应用数据已插入')


def seed_admin():
    """创建默认管理员账户"""
    from database import User

    try:
        user_id = User.create('admin', 'admin@siliang.cfd', 'admin123', role='admin')
        print(f'管理员账户已创建: admin@siliang.cfd / admin123 (ID: {user_id})')
    except ValueError as e:
        print(f'管理员账户已存在或创建失败: {e}')


if __name__ == '__main__':
    print('初始化数据库...')
    init_db()
    print('插入初始数据...')
    seed_apps()
    seed_admin()
    print('完成!')
