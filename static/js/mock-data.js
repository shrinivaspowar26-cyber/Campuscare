/**
 * Campus Care - Centralized Mock Data & In-Tab State Store
 *
 * NOTE FOR COLLEGE PROJECT / CS EVALUATION:
 * - This layer provides initial sample records across all 9 campus categories.
 * - State changes persist across HTML page navigations in the same tab using window.name.
 * - When the page is fully refreshed (F5 / Reload), it detects reload via Navigation Timing API
 *   and automatically resets back to clean sample data (purely in-memory and in-tab string persistence).
 * - When integrating Python Flask + SQLite later, this file's schema maps directly to
 *   the SQL database tables: users, issues, categories, issue_history, and feedback.
 */

// 1. The 9 Centralized Issue Categories (Preconfigured)
const CAMPUS_CATEGORIES = [
  "Electrical",
  "Plumbing",
  "Furniture",
  "Cleaning & Sanitation",
  "Wi-Fi & Network",
  "Infrastructure & Civil",
  "Classroom/Lab Equipment",
  "Washroom",
  "Other"
];

// 2. Specialized Maintenance Teams
const MAINTENANCE_TEAMS = [
  "Campus Electrical Dept",
  "Plumbing & Water Services",
  "Campus IT & Network Operations",
  "Civil Works & Carpentry",
  "Sanitation & Housekeeping Facilities"
];

// 3. Initial Demo Users
const INITIAL_USERS = [
  {
    id: "usr_student_01",
    name: "Demo Student",
    email: "student@campus.edu",
    password: "",
    role: "student",
    roleLabel: "Student",
    identifier: "CS2023-042",
    department: "Computer Science & Engineering",
    phone: "+1 (555) 000-0001"
  },
  {
    id: "usr_staff_01",
    name: "Demo Staff",
    email: "staff@campus.edu",
    password: "",
    role: "student", // Staff shares the Student/Staff portal role
    roleLabel: "Faculty Staff",
    identifier: "EMP-9021",
    department: "Department of Physics",
    phone: "+1 (555) 000-0002"
  },
  {
    id: "usr_admin_01",
    name: "Demo Admin",
    email: "admin@campus.edu",
    password: "",
    role: "admin",
    roleLabel: "Facilities Administrator",
    identifier: "ADM-001",
    department: "Estate & Facilities Office",
    phone: "+1 (555) 000-0003"
  }
];

// 4. Initial Seed Issue Reports
const INITIAL_REPORTS = [
  {
    id: "CC-2026-101",
    title: "Ceiling projector flickering and HDMI port loose",
    category: "Classroom/Lab Equipment",
    location: {
      building: "Engineering Block B",
      floor: "3rd Floor",
      roomArea: "Seminar Lab 304"
    },
    priority: "high",
    status: "Reported",
    assignedTeam: null,
    reportedBy: {
      id: "usr_student_01",
      name: "Alex Johnson",
      email: "student@campus.edu"
    },
    createdAt: "2026-10-28T01:15:00Z",
    updatedAt: "2026-10-28T01:15:00Z",
    description: "During morning lectures, the overhead digital projector shuts off unexpectedly after 15 minutes of projection. The HDMI wall-plate port is also wobbly and losing audio sync.",
    history: [
      {
        timestamp: "2026-10-28T01:15:00Z",
        status: "Reported",
        note: "Issue ticket logged by Alex Johnson.",
        updatedBy: "Alex Johnson (Student)"
      }
    ],
    feedback: null
  },
  {
    id: "CC-2026-102",
    title: "Continuous flush valve leakage causing water accumulation",
    category: "Washroom",
    location: {
      building: "Science Complex",
      floor: "Ground Floor",
      roomArea: "West Wing Restroom (Cubicle 2)"
    },
    priority: "urgent",
    status: "Assigned",
    assignedTeam: "Plumbing & Water Services",
    reportedBy: {
      id: "usr_student_01",
      name: "Alex Johnson",
      email: "student@campus.edu"
    },
    createdAt: "2026-10-27T14:30:00Z",
    updatedAt: "2026-10-27T16:00:00Z",
    description: "The dual flush valve is running continuously without auto-cutoff, leading to clean water flooding into the outer hallway.",
    history: [
      {
        timestamp: "2026-10-27T14:30:00Z",
        status: "Reported",
        note: "Issue submitted by student.",
        updatedBy: "Alex Johnson"
      },
      {
        timestamp: "2026-10-27T16:00:00Z",
        status: "Assigned",
        note: "Assigned to Plumbing & Water Services for emergency washer replacement.",
        updatedBy: "Robert Davis (Admin)"
      }
    ],
    feedback: null
  },
  {
    id: "CC-2026-103",
    title: "Access point AP-L2 dropping connection intermittently",
    category: "Wi-Fi & Network",
    location: {
      building: "Central Library",
      floor: "2nd Floor",
      roomArea: "Silent Study Hall North"
    },
    priority: "medium",
    status: "In Progress",
    assignedTeam: "Campus IT & Network Operations",
    reportedBy: {
      id: "usr_staff_01",
      name: "Prof. Sarah Miller",
      email: "staff@campus.edu"
    },
    createdAt: "2026-10-26T09:45:00Z",
    updatedAt: "2026-10-27T11:20:00Z",
    description: "Wi-Fi access point SSID 'Campus_Secure' authenticates students but provides no IP throughput or drops packets every 5 minutes. Needs PoE switch port check.",
    history: [
      {
        timestamp: "2026-10-26T09:45:00Z",
        status: "Reported",
        note: "Incident logged by faculty.",
        updatedBy: "Prof. Sarah Miller"
      },
      {
        timestamp: "2026-10-26T11:00:00Z",
        status: "Assigned",
        note: "Ticket dispatched to IT Operations.",
        updatedBy: "Robert Davis (Admin)"
      },
      {
        timestamp: "2026-10-27T11:20:00Z",
        status: "In Progress",
        note: "IT technician is testing switch VLAN configurations and replacing patch cable.",
        updatedBy: "Campus IT Team"
      }
    ],
    feedback: null
  },
  {
    id: "CC-2026-104",
    title: "Three broken lecture hall writing desks with exposed screws",
    category: "Furniture",
    location: {
      building: "Academic Block A",
      floor: "1st Floor",
      roomArea: "Lecture Theatre 102 (Rows 4 & 5)"
    },
    priority: "medium",
    status: "Resolved",
    assignedTeam: "Civil Works & Carpentry",
    reportedBy: {
      id: "usr_student_01",
      name: "Alex Johnson",
      email: "student@campus.edu"
    },
    createdAt: "2026-10-24T10:00:00Z",
    updatedAt: "2026-10-25T15:30:00Z",
    description: "Two folding writing tablet arms have detached from the seating frames and have sharp exposed screw threads.",
    history: [
      {
        timestamp: "2026-10-24T10:00:00Z",
        status: "Reported",
        note: "Reported by Alex Johnson.",
        updatedBy: "Alex Johnson"
      },
      {
        timestamp: "2026-10-24T11:15:00Z",
        status: "Assigned",
        note: "Assigned to Carpentry Team.",
        updatedBy: "Robert Davis (Admin)"
      },
      {
        timestamp: "2026-10-25T08:30:00Z",
        status: "In Progress",
        note: "Carpentry team replaced fasteners and re-anchored desk tablets.",
        updatedBy: "Carpentry Team"
      },
      {
        timestamp: "2026-10-25T15:30:00Z",
        status: "Resolved",
        note: "Repairs completed and safety verified. Ready for student verification.",
        updatedBy: "Robert Davis (Admin)"
      }
    ],
    feedback: null // Ready for student feedback!
  },
  {
    id: "CC-2026-105",
    title: "Main corridor exhaust fans stopped spinning",
    category: "Electrical",
    location: {
      building: "Chemistry Annex",
      floor: "2nd Floor",
      roomArea: "Organic Synthesis Corridor"
    },
    priority: "high",
    status: "Closed",
    assignedTeam: "Campus Electrical Dept",
    reportedBy: {
      id: "usr_student_01",
      name: "Alex Johnson",
      email: "student@campus.edu"
    },
    createdAt: "2026-10-21T08:15:00Z",
    updatedAt: "2026-10-23T16:00:00Z",
    description: "Ventilation exhaust fans in the chemistry annex hallway tripped the main distribution sub-board breaker.",
    history: [
      {
        timestamp: "2026-10-21T08:15:00Z",
        status: "Reported",
        note: "Submitted ticket.",
        updatedBy: "Alex Johnson"
      },
      {
        timestamp: "2026-10-21T09:00:00Z",
        status: "Assigned",
        note: "Dispatched to Electrical Department.",
        updatedBy: "Robert Davis"
      },
      {
        timestamp: "2026-10-22T10:00:00Z",
        status: "In Progress",
        note: "Motor capacitor replaced on unit #2.",
        updatedBy: "Electrical Dept"
      },
      {
        timestamp: "2026-10-22T17:00:00Z",
        status: "Resolved",
        note: "All 3 exhaust fans tested and operational.",
        updatedBy: "Robert Davis"
      },
      {
        timestamp: "2026-10-23T16:00:00Z",
        status: "Closed",
        note: "Ticket closed following positive student satisfaction review.",
        updatedBy: "System"
      }
    ],
    feedback: {
      rating: 5,
      comments: "Prompt response from the electrical maintenance team. Air quality in the corridor is back to normal.",
      submittedAt: "2026-10-23T15:45:00Z"
    }
  }
];

// ============================================================================
// State Management Engine (window.name with Navigation Timing Reload-Reset)
// ============================================================================

const STORE_KEY = "CAMPUS_CARE_MOCK_STORE_V1";

class MockDataStore {
  constructor() {
    this.data = this.initializeStore();
  }

  isPageReload() {
    try {
      const navEntries = performance.getEntriesByType("navigation");
      if (navEntries && navEntries.length > 0) {
        return navEntries[0].type === "reload";
      }
      // Fallback for older browsers
      return window.performance && window.performance.navigation && window.performance.navigation.type === 1;
    } catch (e) {
      return false;
    }
  }

  getDefaultData() {
    return {
      currentUser: JSON.parse(JSON.stringify(INITIAL_USERS[0])), // Default logged-in as demo student
      users: JSON.parse(JSON.stringify(INITIAL_USERS)),
      reports: JSON.parse(JSON.stringify(INITIAL_REPORTS)),
      categories: [...CAMPUS_CATEGORIES],
      maintenanceTeams: [...MAINTENANCE_TEAMS]
    };
  }

  initializeStore() {
    const isReload = this.isPageReload();

    // If it is a full browser refresh (F5), reset back to sample data
    if (isReload) {
      const defaultState = this.getDefaultData();
      this.saveToWindowName(defaultState);
      return defaultState;
    }

    // Otherwise, check if window.name already contains data from previous page navigation
    try {
      if (window.name && window.name.startsWith(STORE_KEY + ":")) {
        const jsonStr = window.name.substring(STORE_KEY.length + 1);
        const parsed = JSON.parse(jsonStr);
        if (parsed && parsed.reports && parsed.currentUser) {
          return parsed;
        }
      }
    } catch (err) {
      console.warn("Could not parse window.name state, resetting to initial seed:", err);
    }

    // Default initialization
    const freshState = this.getDefaultData();
    this.saveToWindowName(freshState);
    return freshState;
  }

  saveToWindowName(state) {
    try {
      window.name = STORE_KEY + ":" + JSON.stringify(state);
    } catch (err) {
      console.error("Failed to serialize store into window.name:", err);
    }
  }

  commit() {
    this.saveToWindowName(this.data);
  }

  reset() {
    this.data = this.getDefaultData();
    this.commit();
  }
}

// Global singleton instance for the current tab
window.MockDataStore = MockDataStore;
window.__campusCareStore = new MockDataStore();
