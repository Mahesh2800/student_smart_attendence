# Smart Attendance Management System

## 1. Working Solution

Attendly is a role-based college attendance system with three workflows:

- **Admin:** manages departments, sections, subjects, faculty, students, mappings, reports, and correction approvals.
- **Faculty:** views assigned sessions, marks attendance in bulk, reviews low-attendance students, exports reports, and requests corrections.
- **Student:** views personal attendance records, percentages, subject breakdowns, and calendar history.

The repository contains the complete Django REST backend and React frontend. Demo data can be created with the `seed_data --reset-demo` management command.

## 2. Approach

The solution uses a server-authoritative API. The frontend provides role-specific navigation and forms, while the backend enforces authentication, permissions, ownership, validation, and reporting rules. Attendance sessions retain their section so historical attendance remains associated with the section where it was recorded.

The main attendance flow is:

1. An admin creates the academic structure and subject-faculty-section mappings.
2. A session is created for a mapped faculty member, subject, section, date, and period.
3. Faculty loads one of their sessions and submits attendance for the entire section.
4. The backend validates every student, prevents invalid or duplicate records, and marks the session completed.
5. Percentages and reports are calculated from valid non-cancelled records.
6. A faculty member may request a correction, and an admin approves or rejects it.
7. Approved changes are recorded in the attendance change log.

## 3. Architecture

### Backend

- Django 5.2 and Django REST Framework expose JWT-authenticated APIs.
- Viewsets provide CRUD operations for departments, faculty, students, sections, subjects, mappings, sessions, records, and corrections.
- Custom report endpoints provide low-attendance lists, student percentages, class summaries, and CSV export.
- Permission classes and role-scoped querysets protect admin, faculty, and student data.
- Django model constraints protect uniqueness for mappings, sessions, and session-student attendance records.

### Frontend

- React 19 with Vite and React Router provides separate admin, faculty, and student workspaces.
- Axios services communicate with `/api/v1` and attach JWT access tokens.
- Faculty marking uses a session-aware URL and loads only students from the selected session section.
- Report and correction screens consume the backend validation responses.

### Data model

The core relationship is:

`Department -> ClassSection / Subject / Faculty -> SubjectFacultyMapping -> AttendanceSession -> AttendanceRecord`

Corrections reference an attendance record and retain the original status, requested status, approval state, and resolution metadata.

## 4. Assumptions and Trade-offs

- MySQL is the configured runtime database. The committed SQLite file is not the active database configuration.
- JWT tokens remain in frontend memory for this prototype. This avoids persistent browser token storage, but a refresh requires signing in again.
- Attendance percentages count Present and Late as attended. Absent and Excused are not attended.
- Cancelled sessions are excluded from attendance denominators and reports.
- Records before a student’s enrollment date are excluded from percentages.
- The current-section relationship preserves normal operation but does not provide complete transfer history. A future enrollment-history model would improve historical membership accuracy.
- Concurrent attendance edits use last-write-wins. Changes are logged, but optimistic versioning and row locks are outside the prototype scope.
- The admin department chart currently uses representative frontend data because a department aggregation endpoint has not been implemented.

## 5. Validation and Important Edge Cases

The implementation handles these cases on the server, not only in the UI:

- Future-dated sessions are rejected.
- A session must use a subject-faculty-section mapping.
- Subject, faculty, and section mappings must belong to the same department.
- Faculty can access and modify only their own sessions and records.
- Admin bulk marking uses the session faculty as the audit marker rather than an arbitrary faculty profile.
- Cancelled sessions cannot receive attendance.
- Students in a bulk request must belong to the session section.
- Duplicate student rows and duplicate session-student records are rejected.
- Attendance records cannot be moved to another session or student after creation.
- Faculty cannot transfer session ownership through an update.
- Correction reasons cannot be blank, correction status must differ from the current status, and duplicate pending corrections are rejected.
- Faculty corrections outside `CORRECTION_WINDOW_HOURS` are rejected.
- An admin cannot approve a correction after the underlying record has changed.
- Faculty reports and student percentages are scoped to the faculty member’s own sessions.
- Report thresholds must be finite numbers between 0 and 100.
- Class summaries require a valid section ID and validate date filters in `YYYY-MM-DD` format.
- CSV export uses structured CSV escaping for values containing commas or special characters.

## 6. Validation Results

The following checks were run successfully:

```powershell
Push-Location backend
python manage.py check
python manage.py makemigrations --check
python manage.py test attendance
Pop-Location

Push-Location frontend
npm run build
Pop-Location
```

The backend suite contains **10 passing tests** covering authentication, permissions, percentage calculations, uniqueness, cancelled-session protection, report scope validation, department mapping validation, faculty report scoping, correction-window enforcement, and date-filter validation.

The frontend production build succeeds. Vite reports a non-blocking bundle-size warning because the generated JavaScript chunk is larger than 500 kB.

## 7. Repository and Commit

Repository: <https://github.com/Mahesh2800/student_smart_attendence>

The implementation and subsequent backend fixes were pushed to the `main` branch. The latest fix commit is:

`6b5a729 fix backend validation and report scoping issues`

## 8. Mandatory AI Usage Report

### AI TOOL USED

GitHub Copilot.

### WHAT I ASKED AI TO DO

1. **Improve the end-to-end workflow and edge-case handling.**

   Improved prompt:

   > Review the existing Django and React smart-attendance project locally. Trace the complete admin, faculty, and student attendance flows. Identify missing faculty functionality, API/frontend mismatches, permission leaks, invalid state transitions, report-scope bugs, and validation edge cases. Make the smallest compatible fixes, add focused regression tests, update the README with setup, end-to-end usage, validations, reports, limitations, and verification commands, then run the relevant backend and frontend checks.

2. **Publish the completed project to GitHub.**

   Improved prompt:

   > Inspect the current repository state and preserve all existing work. Initialize Git only if needed, configure `https://github.com/Mahesh2800/student_smart_attendence.git` as `origin`, exclude local secrets, virtual environments, dependencies, and build output, commit the complete source with the message `student and facutly end to end flow updated`, push the `main` branch, and verify the remote commit and clean working tree.

3. **Review and fix backend models, serializers, and views.**

   Improved prompt:

   > Perform a security and correctness review of `backend/attendance/models.py`, `serializers.py`, and `views.py` as one API contract. Find concrete issues involving model validation bypasses, cross-department mappings, faculty/student data scoping, session ownership, correction lifecycle, stale updates, report parameters, audit attribution, CSV escaping, transactions, and unauthorized access. Fix only confirmed issues, add regression tests for every important fix, run Django checks/tests and the frontend build, update documentation, and commit/push with a descriptive `fix ...` message.

### PROMPT THAT WAS MOST USEFUL

The most useful prompt was the backend contract review:

> Perform a security and correctness review of `backend/attendance/models.py`, `serializers.py`, and `views.py` as one API contract. Find concrete issues involving model validation bypasses, cross-department mappings, faculty/student data scoping, session ownership, correction lifecycle, stale updates, report parameters, audit attribution, CSV escaping, transactions, and unauthorized access. Fix only confirmed issues, add regression tests for every important fix, run Django checks/tests and the frontend build, update documentation, and commit/push with a descriptive `fix ...` message.

It was useful because it connected model rules, serializer behavior, view permissions, reports, and tests instead of treating each file independently.

### CODE GENERATED BY AI: What part?

AI generated and revised focused portions of:

- Model validation for subject, faculty, and section department consistency.
- Serializer validation for session ownership, record immutability, correction windows, duplicate pending corrections, and stale correction protection.
- View logic for faculty report scoping, audit attribution, date filters, CSV escaping, cancelled-session protection, and report parameter validation.
- Regression tests for the edge cases listed above.
- README and this submission documentation.

### CODE I MODIFIED: What part?

The existing project structure and feature design were retained. The implementation was modified within the existing backend models, serializers, views, tests, frontend faculty marking components, README, and repository configuration. No new framework or unrelated architecture was introduced.

### AI OUTPUT THAT WAS WRONG

The first backend test and frontend build commands were run from the repository root instead of their respective `backend` and `frontend` directories. They reported missing `manage.py` and `package.json`, which initially looked like project failures but were only working-directory errors. One combined patch was also rejected by the editing tool because of conflicting context; it did not modify the code.

### HOW I IDENTIFIED THE PROBLEM

I compared the command working directory with the repository layout, then reran the commands using `Push-Location backend` and `Push-Location frontend`. The corrected commands passed. For the patch issue, the tool reported that no files were changed, so the edits were split into smaller file-scoped patches and validated after each slice.

### HOW I FIXED IT

I corrected the command paths, validated the application through Django’s test runner and Vite build, and applied the code changes in smaller patches. The final result passed Django system checks, migration checks, all 10 attendance tests, and the frontend production build. The corrected implementation was committed and pushed to the GitHub repository.