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

## 2026-03-23 (周日) 首页 Chrome 性能优化

### 概述
首页 在 Chrome 浏览器中严重卡顿，Safari 正常。问题与之前 AI Writer 相同，原因是 Chrome 对 CSS `backdrop-filter: blur()` 渲染效率低。

### 问题排查

| 浏览器 | 症状 |
|--------|------|
| Chrome | 页面整体卡顿、滚动卡、粒子动画不流畅、卡片动画卡 |
| Safari | 完全正常 |

### 根本原因
- `backdrop-filter: blur()` 在 Chrome 中性能开销远大于 Safari
- 4 处 blur 效果（导航栏、Header、Auth Modal、Modal Overlay）

### 优化方案

#### 1. 移除所有 backdrop-filter
| 元素 | 修改 |
|------|------|
| `.landing-nav` | 移除 blur，背景透明度 0.8 → 0.95 |
| `.header` | 移除 blur，背景透明度 0.9 → 0.95 |
| `.auth-modal-overlay` | 移除 blur，背景透明度 0.8 → 0.85 |
| `.modal-overlay` | 移除 blur，背景透明度 0.8 → 0.85 |

#### 2. 优化粒子动画
- 限制最大粒子数：60 个
- 降低粒子密度：1/8000px² → 1/15000px²
- 添加页面可见性检测（切换标签页时暂停动画）
- Resize 事件节流：200ms

#### 3. 生产环境优化
**CSS/JS 压缩**：
| 文件 | 原始 | 压缩后 | 减少 |
|------|------|--------|------|
| style.css | 24KB | 21KB | 15% |
| api.js | 4.4KB | 3.7KB | 16% |

**Vercel 缓存配置** (vercel.json)：
- CSS/JS: 1 天缓存
- 图片: 7 天缓存

### 修改文件
- `css/style.css` - 移除 backdrop-filter
- `index.html` - 优化粒子动画
- `vercel.json` - 添加缓存配置
- `css/dist/style.min.css` - 压缩版 CSS（新增）
- `js/dist/api.min.js` - 压缩版 JS（新增）

### 经验总结
Chrome 对 CSS 滤镜渲染效率低，`backdrop-filter: blur()` 是性能杀手。解决方案：
1. 完全移除 backdrop-filter，改用更高透明度背景
2. 限制动画元素数量
3. 生产环境压缩静态资源

---

## 2026-03-23 (周日) ColorInsight 动态卡片集成

### 概述
将 ColorInsight AI 应用集成到 Dashboard，实现动态卡片加载，支持从数据库读取应用信息并显示。

### 主要改动

#### 1. 数据库配置
在 `apps` 表中添加 ColorInsight 应用记录：
| 字段 | 值 |
|------|-----|
| name | 色彩洞察 |
| description | 色彩策略 AI 助手 |
| url | https://colorinsight.siliang.cfd |
| module | dm |
| is_active | 1 |

#### 2. Dashboard 动态加载 (dashboard.html)
- 添加 DM 模块动态容器：`<div id="dynamic-apps-dm"></div>`
- 使用 `dynamic-apps-dm` 容器 ID 动态加载应用
- 卡片位置：位于 ArchiAudit 之前
- 添加 `cursor: pointer` 确保点击手势显示

#### 3. 权限分配
- 为测试用户分配 ColorInsight 访问权限

### 部署验证

| 组件 | 状态 |
|------|------|
| ColorInsight 前端 (Vercel) | ✅ colorinsight.siliang.cfd |
| ColorInsight 后端 (阿里云:5002) | ✅ api.siliang.cfd/api/colorinsight/ |
| Dashboard 动态卡片 | ✅ 显示正常 |
| 卡片点击跳转 | ✅ 跳转正常 |

### 修改文件
- `dashboard.html` - 添加 DM 模块动态容器
- 数据库 `apps` 表 - 添加 ColorInsight 记录

---

## 2026-03-22 (周六) AI Writer 动态加载与权限控制

### 概述
实现了 AI Writer 卡片从数据库动态加载，支持基于权限的应用访问控制，并修复了子应用认证问题。

### 主要改动

#### 1. 数据库扩展 (database.py)
新增 `apps` 表字段：
| 字段 | 类型 | 说明 |
|------|------|------|
| `module` | TEXT | 所属模块（office/210/kb/ut） |
| `video_url` | TEXT | 视频文件路径 |
| `icon_class` | TEXT | 图标样式类名 |
| `icon_svg` | TEXT | SVG 图标代码 |
| `card_subtitle` | TEXT | 卡片副标题（中文） |
| `card_subtitle_en` | TEXT | 卡片副标题（英文） |

#### 2. Dashboard 动态加载 (dashboard.html)
- AI Writer 卡片改为从数据库动态加载
- 支持权限控制：普通用户只能看到被分配的应用
- 保持原有 UI 样式（悬浮图标、视频弹窗等）

#### 3. 子应用认证修复 (AI Writer)
- 修复 `writer.siliang.cfd` 可直接访问的问题
- 未登录用户自动跳转到主门户登录页
- 支持 `auth_token` 参数跨域认证

#### 4. 首页 UI 调整 (index.html)
- 右上角紫色标签改为 ArchiAudit
  - 图标：W → A
  - 标题：AI Writer → ArchiAudit
  - 副标题：AI智能文字创作助手 → 住宅平面审核和优化
- 文字位置微调（margin-left: 0.5rem）

#### 5. README 补充
- 添加首页和 Dashboard 截图预览
- 上传 page01.jpeg、page02.jpeg

### 部署验证

| 组件 | 状态 |
|------|------|
| siliang-ai-lab 前端 | ✅ 一致 |
| siliang-ai-lab 后端 | ✅ 一致 |
| AI Writer 前端 | ✅ 一致 |
| AI Writer 后端 | ✅ 一致 |

### 修改文件
- `backend/database.py` - 数据库扩展
- `dashboard.html` - 动态加载逻辑
- `index.html` - 首页 UI 调整
- `README.md` - 添加截图

---

## 2026-03-20 Dashboard UI 优化与视频功能

### 概述
对 Dashboard 页面进行了模块化卡片设计优化，添加了 AI Writer 视频弹窗功能，并修复了多个部署问题。

### 主要改动

#### 1. 视频弹窗功能
- 点击 AI Writer 卡片上方的圆形图标播放介绍视频
- HTML5 video 元素，带控制条
- 点击遮罩层或关闭按钮关闭弹窗

#### 2. 视频压缩
- 原始文件：127MB (CC-AI-Writer.mp4)
- 压缩后：13MB (CC-AI-Writer-compressed.mp4)
- 保持原始比例 1900×926 → 1478×720 (2.05:1)
- 压缩参数：FFmpeg 720p, H.264, CRF 26, AAC 128k

```bash
ffmpeg -i CC-AI-Writer.mp4 -vf "scale=-2:720" -c:v libx264 -crf 26 -preset slow -c:a aac -b:a 128k CC-AI-Writer-compressed.mp4
```

#### 3. 模块化卡片结构
- 创建 `.card-wrapper` 包装器分离点击区域
- `.float-icon` 圆形图标悬浮在卡片上方（z-index: 10）
- 卡片和图标可以分别设置不同的超链接/事件

#### 4. 模块图标样式
```css
.float-icon.icon-210 { background: linear-gradient(135deg, #06b6d4, #67e8f9); }
.float-icon.icon-kb { background: linear-gradient(135deg, #6D28D9, #8B5CF6); }
.float-icon.icon-ut { background: linear-gradient(135deg, #0891B2, #22D3EE); }
```

### 修复问题

#### 1. 登录验证恢复
- 移除临时模拟用户数据
- 恢复 `requireAuth()` 真实登录验证
- 管理员账号正确显示用户名

#### 2. web 目录 submodule 问题
- web 目录被误设为 submodule，导致文件无法部署
- 删除 web/.git 目录，将文件添加到主仓库
- `web/images/archiaudit.png` 等文件现在正常显示

#### 3. AI Writer 卡片跳转问题
- 原使用 `<a>` 标签，无法携带 token
- 改为 `onclick="openApp('https://writer.siliang.cfd')"`
- 现在可以携带 token 进行跨域认证

#### 4. 动态加载重复卡片
- loadApps 函数从 API 获取应用并动态添加
- AI Writer 会被重复添加
- 添加过滤：`apps.filter(app => app.name !== 'AI Writer')`

#### 5. 首页图片路径
- Card01.jpeg 路径修正为 `images/Card01.jpeg`

### 修改文件
- `dashboard.html` - 模块图标、卡片结构、视频弹窗、登录验证
- `index.html` - 图片路径修正
- `images/Card01.jpeg` - 色彩洞察卡片图片
- `card02.jpeg` - 设计语言转化卡片图片
- `CC-AI-Writer-compressed.mp4` - 压缩后的视频文件
- `web/` 目录 - 从 submodule 改为普通目录

### Git 提交记录
```
1190edf fix: Filter out AI Writer from dynamic loading
364f4c8 fix: Restore AI Writer card with video popup
38cd77b fix: Add web directory files and fix AI Writer card link
571675d fix: Remove duplicate AI Writer card from module 4
de5c4ad fix: Restore login auth to show real user info
f6d0d7d fix: Correct Card01.jpeg path in index.html
b5b0fe0 fix: Add Card01.jpeg for 色彩洞察 card
43c56b6 feat: Add video popup and card UI improvements
```

### 待完成
- [ ] 为其他模块添加更多应用卡片
- [ ] CLD AI PPT助手 添加跳转链接

---

## 2026-03-19 首页与Dashboard UI调整

### 概述
对首页和Dashboard页面进行了多项UI优化和内容调整。

### 首页 (index.html) 修改

#### 1. 右侧悬浮拼贴区域
- AI Writer卡片图片替换为 `Card01.jpeg`
- 图片使用 `object-fit: cover` 填充卡片
- 蓝色标签卡片修改：
  - 图标：A → C
  - 标题：ArchiAudit → ColorInsight
  - 副标题：精装平面智能优化和审核 → 色彩洞察 AI 助手
  - 文字向右移动 16px

#### 2. 整体布局调整
- 左右模块同比例放大 9% (`transform: scale(1.09)`)
- 模块下移调整 (`padding-top: 7rem`)
- hero-badge 背景增强 (`rgba(124, 58, 237, 0.2)`)

#### 3. 导航栏
- "套餐 Pricing" → "团队会员 Group"

#### 4. 会员套餐区域
- 标题改为：Group / 团队会员 / 提供不同的会员权限
- 三个会员卡片重新设计：
  - 临时测试账号 (Test) - 紫色渐变按钮
  - 会员账号 - 个人功能版 (Personal) - 青色按钮
  - 会员账号 - 全功能版 (Full) - 浅青色渐变按钮
- 按钮点击提示：请邮件联系管理员 / Please contact admin via email
- 卡片底部对齐，三列布局

### Dashboard (dashboard.html) 修改

#### 1. 模块化布局
创建4个模块大标签（透明灰白色背景）：
1. 🏗️ 设计管理类 AI Agent (Design & Management AI Agent)
2. 🏠 210模块AI工具 (210 Module AI Tools)
3. 📚 知识库类AI Agent (Knowledge Base AI Agent)
4. 🛠️ AI 实用工具 (AI Utility Tools)

#### 2. 应用卡片样式
- 从服务器同步3:4固定比例卡片样式
- 添加白色框线 (`border: 2px solid rgba(255, 255, 255, 0.25)`)
- AI Writer卡片放置在第4个模块（AI 实用工具）内

#### 3. 本地预览支持
- 临时注释登录验证
- 添加模拟用户数据
- 添加模拟应用数据

### 修改文件
- `index.html` - 首页UI调整
- `dashboard.html` - Dashboard模块化布局

### 待完成
- [ ] 将修改部署到服务器
- [ ] 为其他3个模块添加应用卡片

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

## 2026-03-17 待解决问题：ArchiAudit 导致浏览器崩溃 ✅ 已修复

### 问题描述
在 Dashboard 页面点击 ArchiAudit 应用卡片时，会导致：
1. 页面闪烁、卡片跳跃
2. 白屏
3. 浏览器死机

### 原因分析
1. ArchiAudit 的 URL `https://archi.siliang.cfd` 尚未部署
2. 数据库中 `is_active = 1`（激活状态），用户可以看到并点击
3. 点击不存在的域名可能触发浏览器异常行为

### 修复过程
1. ✅ 已修改 `database.py` seed 函数，将 ArchiAudit 默认设为 `is_active = 0`
2. ✅ 已添加 `/api/admin/apps/<id>/toggle` API 端点
3. ✅ **已执行**：使用 PEM 密钥 SSH 连接服务器，更新生产数据库
   ```bash
   # 使用 Python 操作数据库（sqlite3 命令未安装）
   python3 -c "import sqlite3; ..."
   # 重启服务
   systemctl restart siliang-lab
   ```

### 验证结果
```
数据库状态:
(1, 'AI Writer', 1)      # 激活
(2, 'ArchiAudit', 0)     # 已禁用

API 返回: 只返回 AI Writer，ArchiAudit 不再显示
```

### 已修复的其他问题（今日）
1. ✅ `index.html` 重复声明 `const urlParams` 导致 JavaScript 错误，登录无效
2. ✅ 粒子效果恢复正常
3. ✅ 品牌更名为 "CLD-PDDM AI LAB"
4. ✅ ArchiAudit 导致浏览器崩溃问题

### SSH 连接
- 使用 PEM 密钥连接：`ssh -i Aliali.pem root@47.79.0.228`

---

## 2026-03-18 首页 UI 重新设计

### 概述
将首页右侧模块重新设计为"错落式悬浮拼贴（Staggered Collage）"布局，提升视觉层次感和现代感。

### 主要改动

#### 1. 右侧模块 - 错落式悬浮拼贴布局
- **容器**：50% 宽度，min-height: 600px，使用绝对定位
- **图片A (AI Writer)**：左侧，z-index: 1（底层）
  - 尺寸：220px × 320px
  - 位置：left: 0, top: 0
- **图片B (ArchiAudit)**：右侧向下偏移，z-index: 2
  - 尺寸：200px × 290px
  - 位置：left: calc(220px + 1.5rem), top: 120px
- **悬浮卡片1 (AI Writer 标签)**：右上角，z-index: 4
  - 紫色渐变背景 `linear-gradient(135deg, #7c3aed, #a78bfa)`
  - 白色文字，简洁图标 "W"
  - 副标题："AI智能文字创作助手"
- **悬浮卡片2 (ArchiAudit 标签)**：左下角，z-index: 3
  - 青色渐变背景 `linear-gradient(135deg, #06b6d4, #67e8f9)`
  - 白色文字，简洁图标 "A"
  - 副标题："精装平面智能优化和审核"

#### 2. 左侧模块 - 居中对齐
- 宽度：flex: 0 0 55%
- 内容居中：text-align: center, align-items: center
- 标题 "CLD-PDDM AI LAB" 强制单行显示（white-space: nowrap）

#### 3. 整体布局调整
- 左右模块间距：gap: 12rem
- 整体水平偏移：margin-left: -25%（让 gap 中线对齐浏览器中线）
- 整体垂直位置：padding-top: 6rem（模块下移）

#### 4. 其他优化
- "登录后即可访问所有应用" 提示定位在图片2下方
- 图片和卡片添加悬停动画效果
- 响应式布局支持（平板尺寸缩放）

### 样式特点
- 大圆角：图片 24px，卡片 16px
- 柔和投影：多层阴影营造层次感
- 悬停效果：translateY + scale + 增强阴影

### 修改文件
- `web/index.html` - 布局重构和样式更新

---

## 2026-03-20 Dashboard UI 优化与视频功能

### AI Writer Chrome 性能优化
**问题**：Chrome 浏览器 CPU 占用 60-70%，Safari 正常

**修复**：
- 减少 backdrop-filter blur（20px → 10px）
- 移除 aurora 动画 blur 效果
- 删除粒子动画系统（initParticles 函数）
- CSS/JS 压缩（min.css, min.js）
- Vercel 缓存配置（Cache-Control headers）

**修改文件**：`CC_AI_WRITER/ai-article-writer/web/`

### Dashboard 模块化卡片设计

#### 1. 卡片结构优化
- 创建 `.card-wrapper` 包装器分离点击区域
- `.float-icon` 圆形图标悬浮在卡片上方（z-index: 10）
- 卡片和图标可以分别设置不同的超链接

#### 2. 模块图标样式
```css
.float-icon.icon-210 { background: linear-gradient(135deg, #06b6d4, #67e8f9); }
.float-icon.icon-kb { background: linear-gradient(135deg, #6D28D9, #8B5CF6); }
.float-icon.icon-ut { background: linear-gradient(135deg, #0891B2, #22D3EE); }
```

#### 3. 新增卡片
- CLD AI PPT助手（添加到 AI 实用工具模块）

### AI Writer 视频弹窗功能

#### 1. 视频模态框
- 点击 AI Writer 卡片上方的圆形图标播放视频
- HTML5 video 元素，带控制条
- 点击遮罩层或关闭按钮关闭

#### 2. 视频压缩
- 原始文件：127MB (CC-AI-Writer.mp4)
- 压缩后：12MB (CC-AI-Writer-compressed.mp4)
- 压缩参数：FFmpeg 720p, H.264, CRF 26, AAC 128k

```bash
ffmpeg -i CC-AI-Writer.mp4 -vf "scale=-2:720" -c:v libx264 -crf 26 -preset slow -c:a aac -b:a 128k CC-AI-Writer-compressed.mp4
```

### 修改文件
- `dashboard.html` - 模块图标、卡片结构、视频弹窗
- `CC-AI-Writer-compressed.mp4` - 压缩后的视频文件

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
