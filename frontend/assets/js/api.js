const BASE = 'http://localhost:5000/api';

async function apiCall(endpoint, method = 'GET', body = null, isForm = false) {
    const token = localStorage.getItem('token');
    const headers = {};
    if (!isForm) headers['Content-Type'] = 'application/json';
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const options = { method, headers };
    if (body) options.body = isForm ? body : JSON.stringify(body);

    const res = await fetch(BASE + endpoint, options);
    if (res.status === 401) {
        localStorage.clear();
        window.location.href = '/login.html';
        return null;
    }
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) return res.json();
    return res;
}

const get = (path) => apiCall(path);
const post = (path, body) => apiCall(path, 'POST', body);
const patch = (path, body) => apiCall(path, 'PATCH', body);
const postForm = (path, formData) => apiCall(path, 'POST', formData, true);

async function downloadFile(path, filename) {
    const token = localStorage.getItem('token');
    const res = await fetch(BASE + path, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}
