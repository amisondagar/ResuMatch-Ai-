/**
 * static/js/main.js — Global JavaScript
 * ResumeMatch.ai
 *
 * Handles: dark/light mode, sidebar toggle, flash dismissal,
 *          dropdowns, score circle animations, tooltips, loading states
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Theme Toggle ─────────────────────────────────────────────────────
  const root       = document.documentElement;
  const savedTheme = localStorage.getItem('theme') || 'dark';

  root.setAttribute('data-theme', savedTheme);
  updateAllThemeIcons(savedTheme);

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('#themeToggle, .theme-toggle-btn');
    if (btn) {
      e.preventDefault();
      const current = root.getAttribute('data-theme');
      const next    = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      updateAllThemeIcons(next);
    }
  });

  function updateAllThemeIcons(theme) {
    document.querySelectorAll('#themeToggle, .theme-toggle-btn').forEach(btn => {
      btn.innerHTML = theme === 'dark'
        ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
        : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
      btn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    });
  }

  // ── Sidebar Toggle (mobile) ───────────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar       = document.querySelector('.sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // ── Flash Message Auto-dismiss ────────────────────────────────────────
  const flashes = document.querySelectorAll('.alert');
  flashes.forEach((alert, i) => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => dismissAlert(alert));
    }
    // Auto-dismiss after 5 seconds
    setTimeout(() => dismissAlert(alert), 5000 + i * 500);
  });

  function dismissAlert(el) {
    el.style.transition = 'all 0.3s ease';
    el.style.opacity  = '0';
    el.style.transform = 'translateX(20px)';
    setTimeout(() => el.remove(), 300);
  }

  // ── Dropdown Menus ────────────────────────────────────────────────────
  document.querySelectorAll('[data-dropdown]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const target = document.getElementById(trigger.dataset.dropdown);
      if (target) target.classList.toggle('show');
      // Close others
      document.querySelectorAll('.dropdown-menu.show').forEach(m => {
        if (m !== target) m.classList.remove('show');
      });
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu.show')
            .forEach(m => m.classList.remove('show'));
  });

  // ── Animate Score Bars ────────────────────────────────────────────────
  const scoreBars = document.querySelectorAll('.score-bar-fill');
  if (scoreBars.length > 0) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el  = entry.target;
          const val = el.dataset.value || 0;
          el.style.width = val + '%';
          obs.unobserve(el);
        }
      });
    }, { threshold: 0.1 });

    scoreBars.forEach(bar => {
      bar.style.width = '0%';  // Start at 0
      obs.observe(bar);
    });
  }

  // ── Animate Score Circles ─────────────────────────────────────────────
  document.querySelectorAll('.score-circle').forEach(circle => {
    const value   = parseInt(circle.dataset.score || 0);
    const circle_  = circle.querySelector('circle.progress');
    const valueEl = circle.querySelector('.score-circle-value');

    if (!circle_ || !valueEl) return;

    const radius = parseFloat(circle_.getAttribute('r') || 52);
    const circumference = 2 * Math.PI * radius;
    circle_.style.strokeDasharray  = circumference;
    circle_.style.strokeDashoffset = circumference;

    // Animate
    setTimeout(() => {
      const offset = circumference - (value / 100) * circumference;
      circle_.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
      circle_.style.strokeDashoffset = offset;

      // Count up number
      let current = 0;
      const step = value / 60;
      const timer = setInterval(() => {
        current = Math.min(current + step, value);
        valueEl.textContent = Math.round(current) + '%';
        if (current >= value) clearInterval(timer);
      }, 16);
    }, 300);
  });

  // ── Bookmark Toggle ───────────────────────────────────────────────────
  document.querySelectorAll('.bookmark-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const candidateId = btn.dataset.candidateId;
      const url = `/resume/${candidateId}/bookmark`;

      try {
        const res = await fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const data = await res.json();
        const icon = btn.querySelector('.bookmark-icon');
        if (icon) {
          icon.textContent = data.bookmarked ? '🔖 Bookmarked' : '☆ Bookmark';
          btn.classList.toggle('bookmarked', data.bookmarked);
          btn.setAttribute('title', data.bookmarked ? 'Remove Bookmark' : 'Bookmark');
        }
        showToast(data.bookmarked ? 'Bookmarked!' : 'Bookmark removed', 'success');
      } catch (err) {
        console.error('Bookmark error:', err);
      }
    });
  });

  // ── Status Update (Select dropdown & Action buttons) ───────────────────
  document.querySelectorAll('.action-btn-status').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const candId    = btn.dataset.candId;
      const newStatus = btn.dataset.status;

      try {
        const res = await fetch(`/resume/${candId}/status`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: `status=${newStatus}`
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`Candidate status updated to ${newStatus.toUpperCase()}!`, 'success');
          const card = document.getElementById(`cand-card-${candId}`) || btn.closest('.glass-card');
          const badge = card?.querySelector('.status-badge');
          if (badge) {
            badge.textContent = `Status: ${newStatus.charAt(0).toUpperCase() + newStatus.slice(1)}`;
            badge.className = `badge status-badge badge-${statusColor(newStatus)}`;
          }
        }
      } catch (err) {
        console.error('Status update error:', err);
      }
    });
  });

  document.querySelectorAll('.status-select').forEach(sel => {
    sel.addEventListener('change', async () => {
      const scoreId  = sel.dataset.scoreId;
      const newStatus = sel.value;

      try {
        const res = await fetch(`/analysis/status/${scoreId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: `status=${newStatus}`
        });
        const data = await res.json();
        if (data.ok) {
          showToast(`Status updated to ${newStatus}`, 'success');
          const badge = sel.closest('tr')?.querySelector('.status-badge');
          if (badge) {
            badge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
            badge.className = `badge badge-${statusColor(newStatus)} status-badge`;
          }
        }
      } catch (err) {
        console.error('Status update error:', err);
      }
    });
  });

  function statusColor(s) {
    return { shortlisted: 'success', rejected: 'danger', pending: 'warning', interview: 'info' }[s.toLowerCase()] || 'muted';
  }

  // ── Confirm Delete ────────────────────────────────────────────────────
  document.querySelectorAll('.confirm-delete').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
        e.preventDefault();
      }
    });
  });

  // ── Mark Notifications Read ───────────────────────────────────────────
  const notifBtn = document.getElementById('notifToggle');
  if (notifBtn) {
    notifBtn.addEventListener('click', async () => {
      const badge = notifBtn.querySelector('.notif-badge');
      if (badge) {
        await fetch('/dashboard/notifications/mark-read', { method: 'POST' });
        badge.style.display = 'none';
      }
    });
  }

  // ── Global Toast Notification ─────────────────────────────────────────
  window.showToast = function(message, type = 'info') {
    const container = document.getElementById('flashContainer') ||
                      createFlashContainer();
    const toast = document.createElement('div');
    const icons = { success: '✅', danger: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.className = `alert alert-${type}`;
    toast.innerHTML = `<span>${icons[type] || ''} ${message}</span>
                       <button class="alert-close" onclick="this.closest('.alert').remove()">×</button>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.transition = 'all 0.3s ease';
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  };

  function createFlashContainer() {
    const c = document.createElement('div');
    c.id = 'flashContainer';
    c.className = 'flash-container';
    document.body.appendChild(c);
    return c;
  }

  // ── Loading State on Forms ────────────────────────────────────────────
  document.querySelectorAll('form.loading-form').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('[type="submit"]');
      if (btn) {
        btn.disabled = true;
        const orig = btn.innerHTML;
        btn.innerHTML = '<span class="spinner spinner-sm"></span> Processing...';
        // Re-enable after 30s as fallback
        setTimeout(() => { btn.disabled = false; btn.innerHTML = orig; }, 30000);
      }
    });
  });

  // ── Active Nav Highlight ──────────────────────────────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') {
      item.classList.add('active');
    } else if (href === '/' && path === '/') {
      item.classList.add('active');
    }
  });

  // ── Screenshot & Key Shortcuts Enablement ─────────────────────────────
  document.addEventListener('contextmenu', (e) => {
    // Unconditionally allow context menu & right-click
    return true;
  }, true);

  document.addEventListener('keydown', (e) => {
    // Allow PrintScreen, Win+Shift+S, F12, Ctrl+P without blocking
    if (e.key === 'PrintScreen' || e.keyCode === 44) {
      return true;
    }
  }, true);

});
