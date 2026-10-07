async function login(email, password) {
    const data = await post('/auth/login', { email, password });
    if (data && data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('role', data.user.role);
        localStorage.setItem('userName', data.user.name);
        redirectByRole(data.user.role);
    } else {
        throw new Error(data?.error || 'Login failed');
    }
}

function logout() {
    localStorage.clear();
    window.location.href = '/login.html';
}

function redirectByRole(role) {
    const map = {
        super_admin: '/admin/dashboard.html',
        lmo: '/officer/dashboard.html',
        gatc: '/officer/dashboard.html',
        business_owner: '/owner/dashboard.html',
    };
    window.location.href = map[role] || '/login.html';
}

function requireRole(roles) {
    const role = localStorage.getItem('role');
    const allowed = Array.isArray(roles) ? roles : [roles];
    if (!localStorage.getItem('token') || !allowed.includes(role)) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

function getUserName() {
    return localStorage.getItem('userName') || 'User';
}
