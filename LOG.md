# Siliang AI LAB 开发日志

## 项目概述

**Siliang AI LAB** 是一个 AI 应用主门户系统，提供：
- 用户登录/注册功能
- 用户管理（管理员 + 普通用户）
- 应用仪表板（管理多个 AI Web 应用）

**技术栈**：
- 前端：HTML5 + CSS3 + Vanilla JavaScript
- 后端：Python + Flask
- 数据库：SQLite

**项目位置**：`/Users/www.macpe.cn/siliang-ai-lab/`

---

## 2026-03-12 项目启动

### 背景
基于已成功上线的 **AI Article Writer** 项目，扩展为多应用管理平台。

### 已完成
- [x] 创建项目目录结构
  ```
  siliang-ai-lab/
  ├── web/           # 前端文件
  │   ├── css/
  │   ├── js/
  │   └── images/
  ├── backend/       # Flask 后端
  ├── data/          # SQLite 数据库
  └── LOG.md         # 开发日志
  ```

### 待开发功能
- [ ] 用户认证系统（登录/注册）
- [ ] 用户管理后台（管理员功能）
- [ ] 应用仪表板（展示应用缩略图）
- [ ] 集成现有 AI Article Writer

### 关联项目
- **AI Article Writer**: https://siliang.cfd/
- **API 服务**: https://api.siliang.cfd/
- **GitHub**: https://github.com/macpe-pro/ai-article-writer

---

## 2026-03-13 需求确认

### 用户认证需求
| 功能 | 决定 | 备注 |
|------|------|------|
| 注册方式 | 邮箱 + 用户名 | 手机号后续可选 |
| 密码找回 | ✅ 需要 | 邮箱验证 |
| 第三方登录 | ❌ 暂不需要 | 后续可选 |
| 应用管理 | VS Code Claude 管理 | 简化配置文件/数据库管理 |

### UI 风格设计
**风格定位**：Beauty/Spa + Vibrant & Block-based + Glassmorphism

**配色方案**（来自 ui-ux-pro-max）：
| 用途 | 颜色 | Hex |
|------|------|-----|
| 主色 Primary | 粉红色 | #EC4899 |
| 次色 Secondary | 浅粉色 | #F9A8D4 |
| 强调色 CTA | 紫色 | #8B5CF6 |
| 背景色 Background | 极浅粉色 | #FDF2F8 |
| 文字色 Text | 深紫红 | #831843 |
| 边框色 Border | 粉色 | #FBCFE8 |

**视觉效果**：
- Glassmorphism（毛玻璃效果）
- Vibrant（鲜艳活泼）
- Block-based（块状布局）

### 应用列表（待展示）
| 应用名称 | 描述 | 图片 |
|----------|------|------|
| AI Writer | 超级 AI 公众号文章自动化写作助手 | `web/images/ai-writer.png` |
| ArchiAudit | AI 住宅建筑平面图专项审核软件 | `web/images/archiaudit.png` |

---

## 2026-03-13 应用权限管理系统

### 需求
- 除管理员外，普通用户默认**无任何应用权限**
- 管理员需要手动为每个用户分配可用的应用
- 管理面板中每个用户旁显示应用复选框，勾选即分配权限

### 实现

#### 1. 数据库层 (`database.py`)
- 新增 `user_app_permissions` 表，存储用户-应用权限关联
- 新增 `UserAppPermission` 模型类：
  - `get_user_permissions(user_id)` - 获取用户权限列表
  - `set_user_permissions(user_id, app_ids)` - 设置用户权限（替换）
  - `add_permission(user_id, app_id)` - 添加单个权限
  - `remove_permission(user_id, app_id)` - 移除单个权限
- 修改 `App.get_for_user(user_id, is_admin)` - 根据权限过滤应用

#### 2. 后端 API (`app.py`)
- 修改 `/api/apps` - 普通用户只返回被分配的应用，管理员返回所有
- 新增 `GET /api/admin/users/<id>/permissions` - 获取用户权限
- 新增 `POST /api/admin/users/<id>/permissions` - 设置用户权限
- 新增 `GET /api/admin/apps` - 获取所有应用列表

#### 3. 前端 API (`api.js`)
- `AdminAPI.getUserPermissions(userId)` - 获取用户权限
- `AdminAPI.setUserPermissions(userId, appIds)` - 设置用户权限
- `AdminAPI.getAllApps()` - 获取所有应用

#### 4. 管理面板 (`admin.html`)
- 用户表格新增「应用权限」列
- 管理员显示 "管理员拥有所有权限"
- 普通用户显示应用复选框，勾选/取消自动保存
- 添加提示："💡 管理员默认拥有所有应用权限，普通用户需要手动分配应用权限"

#### 5. 用户仪表板 (`dashboard.html`)
- 无权限时显示提示："暂无可用应用，请联系管理员分配应用权限"

### 权限规则

| 用户类型 | 默认权限 | 说明 |
|---------|---------|------|
| 管理员 | 所有应用 | 无需手动分配 |
| 普通用户 | 无 | 必须由管理员勾选分配 |

### 修改文件
- `backend/database.py` - 权限表和模型
- `backend/app.py` - 权限 API 端点
- `web/js/api.js` - 前端 API 方法
- `web/admin.html` - 管理面板权限复选框
- `web/dashboard.html` - 无权限提示

### 示例应用数据
已添加 2 个示例应用：
- AI Writer - 公众号文章自动化写作助手
- ArchiAudit - 住宅建筑平面图审核软件

---

## 2026-03-16 生产环境部署

### 架构调整

将原有单一应用架构调整为**统一门户 + 多应用**架构：

```
siliang.cfd (Vercel)          → 主门户（登录/注册/应用列表）
writer.siliang.cfd (Vercel)   → AI Writer 应用
api.siliang.cfd (阿里云)       → 统一 API 入口
    ├── 端口 5000              → Siliang AI LAB 主后端
    └── 端口 5001              → AI Writer 后端
```

### 部署内容

#### 1. 后端部署（阿里云）
- 上传 Siliang AI LAB 后端到 `/www/siliang-ai-lab/backend/`
- 上传 AI Writer 后端到 `/www/siliang-ai-lab/writer/`
- 配置 Python 虚拟环境和依赖
- 配置 Systemd 服务：
  - `siliang-lab.service` - 主后端（端口 5000）
  - `siliang-writer.service` - AI Writer（端口 5001）

#### 2. Nginx 配置
- 统一 API 入口 `api.siliang.cfd`
- 路由规则：
  - `/api/auth/*` → 端口 5000（认证）
  - `/api/apps/*` → 端口 5000（应用列表）
  - `/api/admin/*` → 端口 5000（管理）
  - `/api/writer/*` → 端口 5001（AI Writer）
- 删除旧的 `ai-article-api` Nginx 配置

#### 3. 前端部署（Vercel）
- 创建 GitHub 仓库：https://github.com/SM01-studio/siliang-ai-lab
- 配置 Vercel 项目，绑定域名 `siliang.cfd`
- AI Writer 移至子域名 `writer.siliang.cfd`

#### 4. DNS 配置（Porkbun）
| 类型 | 主机 | 值 |
|------|------|-----|
| A | @ | 216.198.79.1 (Vercel) |
| A | api | 47.79.0.228 |
| CNAME | writer | cname.vercel-dns.com |

### 访问地址

| 服务 | URL |
|------|-----|
| 主门户 | https://siliang.cfd |
| AI Writer | https://writer.siliang.cfd |
| LAB API | https://api.siliang.cfd/api/health |
| Writer API | https://api.siliang.cfd/api/writer/health |

### 测试账号
- 管理员：`admin@siliang.cfd` / `admin123`

### 修改文件
- `deploy/requirements.txt` - 统一依赖
- `deploy/nginx.conf` - Nginx 配置
- `deploy/siliang-lab.service` - 主后端服务
- `deploy/siliang-writer.service` - Writer 服务
- `backend/app.py` - 添加健康检查端点
- `web/js/api.js` - 更新生产环境 API 地址
- `web/vercel.json` - Vercel 配置

---

## 2026-03-16 部署问题修复

### 问题1: AI Writer 搜索超时
**现象**：Phase 1 搜索超过 5 分钟，显示"AI助手暂时不可用"

**原因**：
1. 缺少 `.env` 文件（GLM_API_KEY 等 API 密钥）
2. 缺少 `references` 参考文档目录
3. 缺少任务处理器服务 (`siliang-task-processor.service`)

**修复**：
- 从旧位置复制 `.env` 文件到 `/www/siliang-ai-lab/writer/.env`
- 上传 `references` 目录并创建软链接
- 创建并启动 `siliang-task-processor.service`

### 问题2: Phase 2 大纲生成 400 错误
**现象**：`/api/writer/outline/generate` 返回 400 错误

**原因**：`generate_outline` 函数只检查内存中的 `sessions` 字典，不从共享文件加载

**修复**：修改 `api_server.py`，在 session 不存在时尝试从共享文件加载

### 新增服务
| 服务名 | 端口 | 说明 |
|--------|------|------|
| siliang-task-processor | - | AI Writer 任务处理器 |

### 修改文件
- `deploy/siliang-task-processor.service` - 新增任务处理器服务
- `api_server.py` - 修复 Phase 2 session 加载

---

## 2026-03-17 部署验证与调试

### 验证工作

#### 1. 前端访问验证
- ✅ 主门户 https://siliang.cfd 正常访问
- ✅ AI Writer https://writer.siliang.cfd 正常访问
- ✅ API 健康检查正常

#### 2. 管理员登录修复
**问题**：管理员账户无法登录，提示"邮箱或密码错误"

**原因**：数据库未正确初始化，缺少管理员用户

**修复**：在服务器上手动创建管理员用户
```python
from database import Database
db = Database()
db.create_user('admin@siliang.cfd', 'admin123', 'Admin', is_admin=True)
```

#### 3. Gemini 图片生成 API 验证
- ✅ Gemini API 连接正常
- ✅ 图片生成功能可用

### 待解决问题

#### AI Writer Phase 2 大纲生成 400 错误
**现象**：
- Phase 1 搜索仍存在超时问题
- Phase 2 `/api/writer/outline/generate` 返回 400 错误

**Nginx 日志**：
```
POST /api/writer/outline/generate HTTP/2.0" 400 44
```

**可能原因**：
1. Session 数据未正确保存/加载
2. 任务处理器与 API 服务器之间的共享文件同步问题

**状态**：待进一步调试

---

## 2026-03-17 Session 数据同步问题修复

### 问题分析
在测试过程中发现多个 Phase 之间数据不同步的问题：

1. **Phase 1 → Phase 2**: 字数设置 (length) 未正确传递
2. **Phase 2 → Phase 3**: 大纲字数未影响初稿生成
3. **Phase 2 → Phase 4**: 配图数量和风格未正确传递
4. **Phase 3 → Phase 4**: 初稿字数显示不更新

### 根本原因
- `create_session` 只保存到内存， 未保存到共享文件
- 多个 gunicorn worker 之间内存不共享
- 各端点获取 session 时未从共享文件同步最新数据

### 修复方案

#### 1. 新增 `get_synced_session()` 函数
```python
def get_synced_session(session_id: str) -> dict:
    """获取同步后的 session - 始终从共享文件合并最新数据"""
    shared_session = shared_get_session(session_id)

    if session_id in sessions:
        mem_session = sessions[session_id]
        if shared_session:
            # 合并共享文件中的最新数据
            for key in ['outline', 'confirmed_outline', 'research_data', 'draft', 'images', 'length', 'audience', 'topic']:
                if key in shared_session and shared_session[key] is not None:
                    mem_session[key] = shared_session[key]
        session = mem_session
    else:
        if shared_session:
            session = shared_session
            sessions[session_id] = session
        else:
            session = None
    return session
```

#### 2. 修复 `create_session`
- 添加 `shared_create_session(session_id, topic, length, audience)` 调用

#### 3. 修复 `generate_draft`
- 使用 `get_synced_session()` 获取 session
- 从 `outline.word_count` 读取目标字数
- 动态计算每章节字数

#### 4. 修复其他端点
- `generate_outline`
- `generate_images`
- `outline_feedback`
- `layout_feedback`
- `complete_export`

### Dashboard 性能优化
- 图片压缩: ai-writer.png (979KB → 196KB), archiaudit.png (1.3MB → 240KB)
- 粒子动画优化: 添加页面可见性检测, 限制最大粒子数
- 删除 2MB 无用图片

### 修改文件
- `api_server.py` - Session 同步修复
- `glm_service.py` - 字数动态计算
- `dashboard.html` - 性能优化
- `images/` - 图片压缩

---

## 服务器信息

| 项目 | 值 |
|------|-----|
| 服务器 IP | 47.79.0.228 |
| 用户名 | root |
| 前端域名 | https://siliang.cfd/ |
| API 域名 | https://api.siliang.cfd/ |

---

## 备注
- 前端部署：Vercel
- 后端部署：阿里云服务器 + Nginx + Systemd
- SSL：Let's Encrypt via Certbot
