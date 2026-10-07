function statusBadge(status) {
    const map = {
        verified: '<span class="badge bg-success">✅ Verified</span>',
        expiring_soon: '<span class="badge bg-warning text-dark">⚠️ Expiring Soon</span>',
        expired: '<span class="badge bg-danger">🔴 Expired</span>',
        failed: '<span class="badge bg-danger">❌ Failed</span>',
        registered: '<span class="badge bg-secondary">Registered</span>',
        pending_verification: '<span class="badge bg-warning text-dark">⏳ Pending</span>',
        revoked: '<span class="badge bg-dark">Revoked</span>',
        submitted: '<span class="badge bg-info">Submitted</span>',
        under_review: '<span class="badge bg-info">Under Review</span>',
        docs_approved: '<span class="badge bg-primary">Docs Approved</span>',
        docs_rejected: '<span class="badge bg-danger">Docs Rejected</span>',
        inspection_scheduled: '<span class="badge bg-warning text-dark">Scheduled</span>',
        inspection_done: '<span class="badge bg-primary">Inspected</span>',
        rejected: '<span class="badge bg-danger">Rejected</span>',
    };
    return map[status] || `<span class="badge bg-light text-dark">${status}</span>`;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function daysUntil(dateStr) {
    if (!dateStr) return null;
    const diff = new Date(dateStr) - new Date();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function showAlert(containerId, message, type = 'info') {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
}

function showLoading(elId) {
    const el = document.getElementById(elId);
    if (el) el.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
}

const INSTRUMENT_TYPES = [
    'Non-Automatic Weighing Scale', 'Platform Scale', 'Fuel Dispenser',
    'Water Meter', 'Energy Meter', 'Gas Meter', 'Clinical Thermometer',
    'Taxi Meter', 'Moisture Meter',
];

const PERMISSIBLE_ERRORS = {
    'Non-Automatic Weighing Scale': 0.5, 'Platform Scale': 0.5, 'Fuel Dispenser': 0.3,
    'Water Meter': 2.0, 'Energy Meter': 1.0, 'Gas Meter': 1.5,
    'Clinical Thermometer': 0.2, 'Taxi Meter': 0.5, 'Moisture Meter': 1.0,
};

function renderSidebar(role, active) {
    const menus = {
        business_owner: [
            { href: '/owner/dashboard.html', label: 'Dashboard', key: 'dashboard' },
            { href: '/owner/instruments.html', label: 'Instruments', key: 'instruments' },
            { href: '/owner/applications.html', label: 'Applications', key: 'applications' },
            { href: '/owner/certificates.html', label: 'Certificates', key: 'certificates' },
        ],
        officer: [
            { href: '/officer/dashboard.html', label: 'Dashboard', key: 'dashboard' },
            { href: '/officer/application-review.html', label: 'Review', key: 'review' },
            { href: '/officer/calendar.html', label: 'Calendar', key: 'calendar' },
        ],
        admin: [
            { href: '/admin/dashboard.html', label: 'Dashboard', key: 'dashboard' },
            { href: '/admin/instruments.html', label: 'Instruments', key: 'instruments' },
            { href: '/admin/users.html', label: 'Users', key: 'users' },
            { href: '/admin/reports.html', label: 'Reports', key: 'reports' },
        ],
    };
    const items = menus[role] || [];
    return items.map(m =>
        `<a href="${m.href}" class="sidebar-link ${active === m.key ? 'active' : ''}">${m.label}</a>`
    ).join('');
}

function initLayout(sidebarRole, activePage) {
    const sidebar = document.getElementById('sidebar-nav');
    if (sidebar) sidebar.innerHTML = renderSidebar(sidebarRole, activePage);
    const userEl = document.getElementById('user-name');
    if (userEl) userEl.textContent = getUserName();
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
}
