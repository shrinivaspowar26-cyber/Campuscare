
/**
 * Campus Care - Frontend API Client
 * All methods call real Flask/SQLite endpoints.
 * mock-data.js is no longer used by this client.
 */

const CampusCareAPI = {

  // ---------------------------------------------------------------------------
  // Internal helper
  // ---------------------------------------------------------------------------

  async _fetch(url, options = {}) {
    const res = await fetch(url, options);
    let body;
    try { body = await res.json(); } catch { body = {}; }
    if (!res.ok) {
      throw new Error(body.error || `Request failed (${res.status})`);
    }
    return body;
  },

  // ---------------------------------------------------------------------------
  // Auth & Session
  // ---------------------------------------------------------------------------

  async getCurrentUser() {
    return this._fetch("/api/auth/current-user");
  },

  async login(email, password, role) {
    return this._fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role })
    });
  },

  async register(userData) {
    return this._fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    });
  },

  async logout() {
    await fetch("/logout");
    return true;
  },

  // ---------------------------------------------------------------------------
  // Reference data
  // ---------------------------------------------------------------------------

  async getCategories() {
    return this._fetch("/api/categories");
  },

  async getMaintenanceTeams() {
    return this._fetch("/api/maintenance-teams");
  },

  // ---------------------------------------------------------------------------
  // Reports
  // ---------------------------------------------------------------------------

  async getReports(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category && filters.category !== "All") params.set("category", filters.category);
    if (filters.status   && filters.status   !== "All") params.set("status",   filters.status);
    if (filters.priority && filters.priority !== "All") params.set("priority", filters.priority);
    if (filters.search   && filters.search.trim())      params.set("search",   filters.search.trim());
    const qs = params.toString();
    return this._fetch(`/api/reports${qs ? "?" + qs : ""}`);
  },

  async getReportById(id) {
    // id is the human-readable ticket ID (CC-YYYY-NNN)
    return this._fetch(`/api/reports/by-ticket/${encodeURIComponent(id)}`);
  },

  async createReport(reportData) {
    // reportData may carry a FormData (with image) or a plain object
    if (reportData instanceof FormData) {
      const res = await fetch("/api/reports", { method: "POST", body: reportData });
      let body;
      try { body = await res.json(); } catch { body = {}; }
      if (!res.ok) throw new Error(body.error || "Could not create report.");
      return body;
    }
    return this._fetch("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reportData)
    });
  },

  async updateReportStatus(id, newStatus, note = "") {
    // id here is the DB integer id (dbId) returned in report objects
    return this._fetch(`/api/reports/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus, note })
    });
  },

  async assignMaintenanceTeam(id, teamName, note = "") {
    return this._fetch(`/api/reports/${id}/assign`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team: teamName, note })
    });
  },

  async deleteReport(id) {
    return this._fetch(`/api/reports/${encodeURIComponent(id)}`, {
      method: "DELETE"
    });
  },

  // ---------------------------------------------------------------------------
  // Analytics  (computed from live report data)
  // ---------------------------------------------------------------------------

  async getAdminStats() {
    const [reports, feedback] = await Promise.all([
      this.getReports(),
      this.getAllFeedback()
    ]);

    const count = (status) => reports.filter(r => r.status === status).length;
    const resolved = count("Resolved");
    const closed   = count("Closed");

    const categoryCounts = {};
    reports.forEach(r => {
      categoryCounts[r.category] = (categoryCounts[r.category] || 0) + 1;
    });

    const ratings = feedback.map(f => f.rating).filter(Boolean);
    const avgRating = ratings.length
      ? (ratings.reduce((s, v) => s + v, 0) / ratings.length).toFixed(1)
      : "N/A";

    return {
      total:             reports.length,
      pendingAssignment: count("Reported"),
      assigned:          count("Assigned"),
      inProgress:        count("In Progress"),
      resolved,
      closed,
      resolvedOrClosed:  resolved + closed,
      avgRating,
      totalReviews:      ratings.length,
      categoryCounts
    };
  },

  async getStudentStats() {
    const reports = await this.getReports();
    return {
      total:           reports.length,
      inProgress:      reports.filter(r => r.status === "In Progress" || r.status === "Assigned").length,
      resolved:        reports.filter(r => r.status === "Resolved" || r.status === "Closed").length,
      awaitingFeedback: reports.filter(r =>
        (r.status === "Resolved" || r.status === "Closed") && !r.feedback
      ).length
    };
  },

  // ---------------------------------------------------------------------------
  // Feedback
  // ---------------------------------------------------------------------------

  async submitFeedback(id, feedbackData) {
    // id is the DB integer id (dbId)
    return this._fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reportId: id,
        rating:   feedbackData.rating,
        comments: feedbackData.comments || ""
      })
    });
  },

  async getAllFeedback(limit) {
    const qs = limit ? `?limit=${encodeURIComponent(limit)}` : "";
    return this._fetch(`/api/feedback${qs}`);
  },

  // ---------------------------------------------------------------------------
  // Profile
  // ---------------------------------------------------------------------------

  async updateProfile(userId, profileData) {
    // userId param kept for signature compatibility — server uses session
    return this._fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profileData)
    });
  },

  // Dev-only persona switcher — not available in production (real sessions are used).
  async switchPersona(email) {
    throw new Error("switchPersona is not available — use the login page to switch accounts.");
  }
};

// Global export for multi-page scripts
if (typeof window !== "undefined") {
  window.CampusCareAPI = CampusCareAPI;
}

