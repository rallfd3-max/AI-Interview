// 登录认证相关的API
const API_BASE_URL = `http://${window.location.hostname}:8080/api`;

export async function login(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error('登录失败');
        }

        const data = await response.json();
        if (data.token) {
            // 存储token和用户信息
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify({
                username: data.username,
                // 其他用户信息...
            }));
            return data;
        } else {
            throw new Error('登录响应中没有token');
        }
    } catch (error) {
        console.error('登录请求失败:', error);
        throw error;
    }
}

export async function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

export function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}
