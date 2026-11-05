# Campus Care — Implementation Plan

## Phase 1: Finalize UI
- Finalize pages and navigation.
- Define forms, tables, buttons, and user actions.
- Use AI Studio screenshots as references.

## Phase 2: Build Frontend
- Create HTML templates.
- Add shared CSS and responsive layouts.
- Add JavaScript interactions.
- Use temporary sample data during UI development.
- Keep sample data separate from production logic.

## Phase 3: Design Database
- Create SQLite schema.
- Define users, categories, maintenance teams, issues, issue history, and feedback.
- Add relationships and constraints.
- Prepare initialization and sample-data scripts.

## Phase 4: Build Flask Foundation
- Set up Flask application.
- Configure SQLite access.
- Implement registration, login, logout, and sessions.
- Add role-based access control.
- Hash passwords securely.

## Phase 5: Implement Issue Reporting
- Create reports.
- Validate report details.
- Generate unique report IDs.
- Show users their own reports.
- Display report details and history.

## Phase 6: Implement Admin Operations
- Display all campus reports.
- Add search, filters, and sorting.
- Assign maintenance teams.
- Update issue statuses.
- Record assignments and status changes in issue history.

## Phase 7: Implement Feedback
- Allow eligible reporters to submit ratings and comments.
- Display submitted reviews.
- Calculate average ratings and rating distribution from database records.

## Phase 8: Integrate Dashboards
- Connect dashboard statistics to SQLite.
- Remove temporary sample data from completed features.
- Verify that user and admin views stay consistent.

## Phase 9: Test
- Test registration, login, and logout.
- Test report submission and persistence.
- Test admin assignment and status changes.
- Test access permissions.
- Test feedback submission.
- Test filters, validation, and error handling.
- Verify the complete issue workflow.

## Phase 10: Finalize
- Fix bugs.
- Improve responsive layout.
- Write README and setup instructions.
- Prepare screenshots and project demonstration.

## Rules
- Complete one phase at a time.
- Test each feature before moving forward.
- Update `PROGRESS.md` after meaningful changes.
- Do not skip unfinished dependencies.
- Do not add unnecessary technologies.
- Adjust this plan only when implementation requires it.
