# Siliang AI LAB

AI 应用管理平台 - 用户登录、应用仪表板、管理员面板

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r ../requirements.txt
```

### 2. 初始化数据库

```bash
python seed.py
```

### 3. 启动服务

```bash
python app.py
```

访问 http://localhost:5000

## 默认账户

- **邮箱**: admin@siliang.cfd
- **密码**: admin123

## 目录结构

```
siliang-ai-lab/
├── web/                 # 前端
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── index.html       # 登录/注册
│   ├── dashboard.html   # 仪表板
│   └── admin.html       # 管理面板
├── backend/             # 后端
│   ├── app.py           # Flask 主程序
│   ├── database.py      # 数据库模型
│   └── seed.py          # 初始化脚本
├── data/                # SQLite 数据库
└── LOG.md               # 开发日志
```

## 功能

- [x] 用户注册/登录
- [x] 密码找回
- [x] 应用仪表板
- [x] 管理员用户管理
- [x] Glassmorphism UI

## 部署

生产环境部署到：
- 前端: Vercel (https://lab.siliang.cfd)
- 后端: 阿里云服务器 (https://api.siliang.cfd)
