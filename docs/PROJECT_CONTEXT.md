# Campus Care — Project Context

## Goal
Build a campus issue reporting system. Students and staff report problems. Admin reviews reports, assigns maintenance teams, and tracks resolution.

## Tech Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: SQLite
- Only use necessary frameworks.

## User Roles

### Student / Staff
- Register, log in, log out.
- View personal dashboard and reports.
- Report campus problems.
- Select category, location, and priority.
- Track report status and history.
- Submit feedback after resolution.
- Manage profile.

### Admin
- Log in and access admin dashboard.
- View all campus reports.
- Search, filter, and sort reports.
- View report details.
- Assign reports to maintenance teams.
- Update report status.
- View feedback, ratings, and satisfaction statistics.
- Manage profile.

No separate maintenance-team dashboard.

## Issue Workflow
Reported → Assigned → In Progress → Resolved → Closed

## Main Pages
1. Login
2. Student/Staff registration
3. Student/Staff dashboard
4. Report problem form
5. My reports and report details
6. Admin dashboard
7. Issue management and assignment
8. Feedback and reviews
9. Profile settings

## UI Direction
Use the provided AI Studio screenshots as visual references.

Aim for a clean, professional, responsive dashboard with:
- Sidebar navigation
- Summary cards
- Searchable and filterable tables
- Clear status and priority indicators
- Consistent spacing, typography, and colors

Functionality matters more than pixel-perfect matching.

## Core Rules
- Users see only their own reports.
- Admin can view and manage all reports.
- Admin assigns maintenance teams.
- Feedback is linked to eligible resolved/closed reports.
- Dashboard statistics must come from real database records.
- Data must persist after refresh and application restart.
