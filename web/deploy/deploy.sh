#!/bin/bash
# Siliang AI LAB - 部署脚本
# 使用方法: ./deploy.sh

set -e

# 配置
SERVER="47.79.0.228"
USER="root"
REMOTE_DIR="/www/siliang-ai-lab"

echo "🚀 Siliang AI LAB 部署脚本"
echo "============================"

# 1. 创建远程目录结构
echo "📁 创建远程目录结构..."
ssh $USER@$SERVER "mkdir -p $REMOTE_DIR/{backend,writer,web,data,venv}"

# 2. 上传后端代码
echo "📤 上传 Siliang AI LAB 后端..."
rsync -avz --exclude '__pycache__' --exclude '*.pyc' \
    ../backend/ $USER@$SERVER:$REMOTE_DIR/backend/

# 3. 上传 AI Writer 后端
echo "📤 上传 AI Writer 后端..."
rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude 'output' \
    ../../CC_AI_WRITER/ai-article-writer/web/ $USER@$SERVER:$REMOTE_DIR/writer/

# 4. 上传前端
echo "📤 上传前端文件..."
rsync -avz ../web/ $USER@$SERVER:$REMOTE_DIR/web/

# 5. 上传部署配置
echo "📤 上传部署配置..."
scp requirements.txt $USER@$SERVER:$REMOTE_DIR/
scp nginx.conf $USER@$SERVER:/tmp/siliang-nginx.conf
scp siliang-lab.service $USER@$SERVER:/tmp/
scp siliang-writer.service $USER@$SERVER:/tmp/

# 6. 远程安装依赖
echo "📦 安装 Python 依赖..."
ssh $USER@$SERVER << 'EOF'
cd /www/siliang-ai-lab

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 安装依赖
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
venv/bin/pip install gunicorn gevent
EOF

# 7. 配置 Systemd 服务
echo "⚙️ 配置 Systemd 服务..."
ssh $USER@$SERVER << 'EOF'
# 复制服务文件
cp /tmp/siliang-lab.service /etc/systemd/system/
cp /tmp/siliang-writer.service /etc/systemd/system/

# 重新加载 systemd
systemctl daemon-reload

# 启用服务
systemctl enable siliang-lab
systemctl enable siliang-writer
EOF

# 8. 配置 Nginx
echo "🌐 配置 Nginx..."
ssh $USER@$SERVER << 'EOF'
# 备份旧配置
if [ -f /etc/nginx/sites-available/siliang-api ]; then
    cp /etc/nginx/sites-available/siliang-api /etc/nginx/sites-available/siliang-api.bak
fi

# 复制新配置
cp /tmp/siliang-nginx.conf /etc/nginx/sites-available/siliang-api

# 创建软链接
ln -sf /etc/nginx/sites-available/siliang-api /etc/nginx/sites-enabled/

# 测试 Nginx 配置
nginx -t
EOF

# 9. 重启服务
echo "🔄 重启服务..."
ssh $USER@$SERVER << 'EOF'
# 重启后端服务
systemctl restart siliang-lab
systemctl restart siliang-writer

# 重启 Nginx
systemctl reload nginx

# 检查状态
sleep 2
systemctl status siliang-lab --no-pager
systemctl status siliang-writer --no-pager
EOF

echo ""
echo "✅ 部署完成!"
echo "============================"
echo "API 地址: https://api.siliang.cfd"
echo "健康检查: https://api.siliang.cfd/health"
