// API基础URL
const API_BASE_URL = `http://${window.location.hostname}:8080`;

// 检查登录状态
function checkLoginStatus() {
    const token = localStorage.getItem('token');
    if (!token) {
        // 如果没有登录token且不在登录页面，则重定向到登录页
        if (!window.location.pathname.includes('login.html') && 
            !window.location.pathname.includes('register.html')) {
            window.location.href = '/login.html';
        }
    }
}

// 在每个页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', checkLoginStatus);

// 处理登录表单提交
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // 调用登录函数
        const loginResult = await login(username, password);
        if (!loginResult) {
            return;
        }
    });
}

// 处理注册表单提交
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            alert('两次输入的密码不一致！');
            return;
        }

        // 调用注册函数
        const registerResult = await register(username, password);
        if (!registerResult) {
            return;
        }
    });
}

// 登出功能
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = '/login.html';
}

// 登录函数
async function login(username, password) {
    try {
        const response = await axios.post(`${API_BASE_URL}/user/login`, {
            username: username,
            password: password
        });
        
        if (response.data.status === 200) {
            // 保存用户信息和token
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('username', username);
            localStorage.setItem('userInfo', JSON.stringify(response.data.data));
            
            // 跳转到管理页面
            window.location.href = 'pages/a/admin.html';
            return true;
        } else {
            alert(response.data.msg || '登录失败');
            return false;
        }
    } catch (error) {
        console.error('登录错误:', error);
        alert('登录失败，请稍后重试');
        return false;
    }
}

// 注册函数
async function register(username, password) {
    try {
        const response = await axios.post(`${API_BASE_URL}/user/register`, {
            username: username,
            password: password
        });
        
        if (response.data.status === 200) {
            alert('注册成功！请登录');
            return true;
        } else {
            alert(response.data.msg || '注册失败');
            return false;
        }
    } catch (error) {
        console.error('注册错误:', error);
        alert('注册失败，请稍后重试');
        return false;
    }
}

// 登出函数
function logoutNew() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('username');
    localStorage.removeItem('userInfo');
    window.location.href = '../../login.html';
}

// 检查登录状态
function checkLogin() {
    if (!localStorage.getItem('isLoggedIn')) {
        window.location.href = '../login.html';
    }
}
