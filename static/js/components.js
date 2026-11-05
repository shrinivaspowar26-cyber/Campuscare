/**
 * Campus Care - Shared UI Components & Shell Renderer
 * Provides centralized sidebar, top navigation, status badges, and toast alerts
 * across all multi-page HTML views.
 */

const CampusCareUI = {
  // Initialize standard page shell
  async initPage(activePageKey, options = {}) {
    const user = await CampusCareAPI.getCurrentUser();

    // 1. Auth Guard
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath.includes("/login") || currentPath.includes("/register");

    if (!user && !isAuthPage) {
      window.location.href = "/login";
      return;
    }

    // Role-based route guard
    if (user && options.requiredRole && user.role !== options.requiredRole) {
      if (user.role === "student" && options.requiredRole === "admin") {
        alert("Access restricted to Facilities Administrators.");
        window.location.href = "/student-dashboard";
        return;
      }
    }

    // 2. Render Shared Sidebar
    const sidebarEl = document.getElementById("app-sidebar");
    if (sidebarEl && user) {
      this.renderSidebar(sidebarEl, user, activePageKey);
    }

    // 3. Render Shared Header
    const headerEl = document.getElementById("app-header");
    if (headerEl && user) {
      this.renderHeader(headerEl, user, options.pageTitle || "Dashboard");
    }

    // 4. Setup mobile drawer toggle
    this.setupMobileMenu();
  },

  // Render Sidebar
  renderSidebar(container, user, activeKey) {
    const isAdmin = user.role === "admin";

    const studentLinks = [
      { key: "student-dashboard", label: "Dashboard", href: "/student-dashboard", icon: "📊" },
      { key: "report-problem", label: "Report Problem", href: "/report-problem", icon: "➕" },
      { key: "my-reports", label: "My Reports", href: "/my-reports", icon: "📋" },
      { key: "profile", label: "Profile Settings", href: "/profile", icon: "👤" }
    ];

    const adminLinks = [
      { key: "admin-dashboard", label: "Admin Overview", href: "/admin-dashboard", icon: "📈" },
      { key: "admin-issues", label: "Issue Management", href: "/admin-issues", icon: "🛠️" },
      { key: "feedback", label: "Feedback & Reviews", href: "/feedback", icon: "⭐" },
      { key: "profile", label: "Profile Settings", href: "/profile", icon: "👤" }
    ];

    const links = isAdmin ? adminLinks : studentLinks;

    let navHtml = links.map(link => {
      const isActive = link.key === activeKey ? "active" : "";
      return `
        <a href="${link.href}" class="sidebar-link ${isActive}">
          <span class="sidebar-icon">${link.icon}</span>
          <span>${link.label}</span>
        </a>
      `;
    }).join("");

    const initials = user.name
      .split(" ")
      .map(n => n[0])
      .join("")
      .substring(0, 2)
      .toUpperCase();

    container.className = "app-sidebar";
    container.innerHTML = `
      <div class="sidebar-brand">
        <div class="brand-icon">CC</div>
        <div>
          <div class="brand-name">Campus Care</div>
          <div class="brand-tag">${isAdmin ? "Admin Portal" : "Student / Staff Portal"}</div>
        </div>
      </div>

      <nav class="sidebar-menu">
        <div class="menu-category-title">Navigation</div>
        ${navHtml}
      </nav>

      <div class="sidebar-footer">
        <div class="user-mini-profile">
          <div class="user-avatar-circle">${initials}</div>
          <div class="user-details-mini">
            <div class="user-name-mini" title="${user.name}">${user.name}</div>
            <div class="user-role-mini">${user.roleLabel || user.role}</div>
          </div>
        </div>
        <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
          <a href="/profile" style="font-size: 11.5px; color: #94A3B8;">Settings</a>
          <button id="sidebar-logout-btn" style="background: none; border: none; color: #F87171; font-size: 11.5px; cursor: pointer; padding: 2px 4px;">Log Out</button>
        </div>
      </div>
    `;

    // Event handlers
    const logoutBtn = container.querySelector("#sidebar-logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        await CampusCareAPI.logout();
        window.location.href = "/login";
      });
    }
  },

  // Render Header
  renderHeader(container, user, title) {
    container.className = "app-header";
    container.innerHTML = `
      <div class="header-left">
        <button class="mobile-menu-btn" id="mobile-toggle-btn" aria-label="Toggle Menu">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <h1 class="page-title">${title}</h1>
      </div>

      <div class="header-right">
        <span class="quick-role-badge">
          ${user.role === "admin" ? "🛡️ Facilities Admin" : "🎓 Student / Staff"}
        </span>
      </div>
    `;
  },

  // Setup mobile sidebar toggle
  setupMobileMenu() {
    const toggleBtn = document.getElementById("mobile-toggle-btn");
    const sidebar = document.getElementById("app-sidebar");
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("mobile-open");
      });

      // Close when clicking outside on mobile
      document.addEventListener("click", (e) => {
        if (sidebar.classList.contains("mobile-open") &&
            !sidebar.contains(e.target) &&
            !toggleBtn.contains(e.target)) {
          sidebar.classList.remove("mobile-open");
        }
      });
    }
  },

  // Render Status Badge
  renderStatusBadge(status) {
    const s = (status || "").toLowerCase().replace(/\s+/g, "");
    return `<span class="status-badge ${s}">${status}</span>`;
  },

  // Render Priority Indicator
  renderPriority(priority) {
    const p = (priority || "medium").toLowerCase();
    const label = p.charAt(0).toUpperCase() + p.slice(1);
    return `<span class="priority-indicator priority-${p}">● ${label}</span>`;
  },

  // Format ISO Date
  formatDate(isoString) {
    if (!isoString) return "N/A";
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  },

  // Format Date + Time
  formatDateTime(isoString) {
    if (!isoString) return "N/A";
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  },

  // Toast Notification System
  toast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${type === "success" ? "✓" : type === "error" ? "⚠️" : "ℹ️"}</span>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }
};

// Global export for multi-page scripts
if (typeof window !== "undefined") {
  window.CampusCareUI = CampusCareUI;
}
