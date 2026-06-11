/* ═══════════════════════════════════════════════════════
   SecureHealth HMS – Main JavaScript
   ═══════════════════════════════════════════════════════ */

// ── Sidebar Toggle ─────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const wrapper = document.getElementById('mainWrapper');
  if (sidebar) {
    sidebar.classList.toggle('open');
    // Overlay for mobile
    let overlay = document.getElementById('sidebarOverlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'sidebarOverlay';
      overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:99;display:none;';
      overlay.onclick = toggleSidebar;
      document.body.appendChild(overlay);
    }
    overlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
  }
}

// ── Dark Mode ──────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const icon = document.getElementById('themeIcon');
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  if (icon) icon.className = isDark ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
  localStorage.setItem('shms-theme', isDark ? 'light' : 'dark');
}

// Apply saved theme on load
(function () {
  const saved = localStorage.getItem('shms-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.className = saved === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
  }
})();

// ── Auto-dismiss Flash Messages ────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.flash-alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});

// ── Session Timeout Warning ────────────────────────────
(function () {
  const WARNING_MS = 7 * 60 * 60 * 1000; // 7h (warn 1h before 8h session)
  let warningTimer = setTimeout(function () {
    const toast = document.createElement('div');
    toast.className = 'alert alert-warning flash-alert';
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;max-width:340px;box-shadow:0 4px 12px rgba(0,0,0,.15);';
    toast.innerHTML = '<i class="fa-solid fa-clock me-2"></i><strong>Session expiring soon.</strong> Your session will expire in 1 hour.';
    document.body.appendChild(toast);
    setTimeout(function () { toast.remove(); }, 8000);
  }, WARNING_MS);
})();

// ── Table Row Click → View ─────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.data-table tbody tr[data-href]').forEach(function (row) {
    row.style.cursor = 'pointer';
    row.addEventListener('click', function () {
      window.location.href = row.dataset.href;
    });
  });
});

// ── Confirm Dangerous Actions ──────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });
});
