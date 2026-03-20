/**
 * Siliang AI LAB - API Client
 */

// API 配置
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:5000/api'
    : 'https://api.siliang.cfd/api';

// Token 管理
const TokenManager = {
    get() {
        return localStorage.getItem('auth_token');
    },
    set(token) {
        localStorage.setItem('auth_token', token);
    },
    remove() {
        localStorage.removeItem('auth_token');
    }
};

// API 请求封装
async function api(endpoint, options = {}) {
    const token = TokenManager.get();

    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers
        }
    };

    if (options.body && typeof options.body === 'object') {
        config.body = JSON.stringify(options.body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || '请求失败');
    }

    return data;
}

// 认证 API
const AuthAPI = {
    async register(username, email, password) {
        return api('/auth/register', {
            method: 'POST',
            body: { username, email, password }
        });
    },

    async login(email, password) {
        const data = await api('/auth/login', {
            method: 'POST',
            body: { email, password }
        });
        if (data.token) {
            TokenManager.set(data.token);
        }
        return data;
    },

    async logout() {
        try {
            await api('/auth/logout', { method: 'POST' });
        } catch (e) {
            // 忽略登出错误
        }
        TokenManager.remove();
    },

    async getCurrentUser() {
        return api('/auth/me');
    },

    async forgotPassword(email) {
        return api('/auth/forgot-password', {
            method: 'POST',
            body: { email }
        });
    },

    async resetPassword(token, password) {
        return api('/auth/reset-password', {
            method: 'POST',
            body: { token, password }
        });
    }
};

// 应用 API
const AppsAPI = {
    async getAll() {
        return api('/apps');
    }
};

// 管理员 API
const AdminAPI = {
    async getUsers() {
        return api('/admin/users');
    },

    async createUser(username, email, password, role, expiresAt) {
        return api('/admin/users', {
            method: 'POST',
            body: { username, email, password, role, expires_at: expiresAt }
        });
    },

    async toggleUser(userId) {
        return api(`/admin/users/${userId}/toggle`, { method: 'POST' });
    },

    async deleteUser(userId) {
        return api(`/admin/users/${userId}`, { method: 'DELETE' });
    },

    // 权限管理
    async getUserPermissions(userId) {
        return api(`/admin/users/${userId}/permissions`);
    },

    async setUserPermissions(userId, appIds) {
        return api(`/admin/users/${userId}/permissions`, {
            method: 'POST',
            body: { app_ids: appIds }
        });
    },

    async getAllApps() {
        return api('/admin/apps');
    }
};

// Toast 通知
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// 检查登录状态
async function checkAuth() {
    const token = TokenManager.get();
    if (!token) return null;

    try {
        const { user } = await AuthAPI.getCurrentUser();
        return user;
    } catch (e) {
        TokenManager.remove();
        return null;
    }
}

// 路由保护
async function requireAuth() {
    const user = await checkAuth();
    if (!user) {
        window.location.href = '/index.html';
        return null;
    }
    return user;
}

// 管理员保护
async function requireAdmin() {
    const user = await requireAuth();
    if (!user) return null;

    if (user.role !== 'admin') {
        showToast('无权限访问', 'error');
        window.location.href = '/dashboard.html';
        return null;
    }
    return user;
}
