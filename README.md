# Smart Attendance Management System

Attendly is a role-aware attendance workspace for colleges. Administrators manage the academic structure and review corrections, faculty record attendance and monitor their assigned sections, and students view their own attendance history.

## Stack

- **Backend:** Django 5.2, Django REST Framework, SimpleJWT, django-filter, django-cors-headers, and MySQL.
- **Frontend:** React 19, Vite, React Router, Axios, and Recharts.
- **API base:** `/api/v1`.
- **Authorization:** JWT access tokens are attached by the frontend Axios interceptor. Access and refresh tokens are kept in memory for this demo, so a page refresh requires login again.

## Setup

### Backend

The backend reads database and CORS settings from `backend/.env`.

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create the MySQL database and user named in `.env`, then run:

```powershell
python manage.py migrate
python manage.py seed_data --reset-demo
python manage.py runserver
```

`seed_data --reset-demo` creates five departments, class sections, subjects, ten faculty profiles, fifty students, mappings, and historical sessions with sample records.

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The frontend defaults to `http://localhost:5173` and calls `http://localhost:8000/api/v1`. Change `VITE_API_URL` in `frontend/.env` when the API is hosted elsewhere.

Demo credentials printed by the seed command:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `Admin@123` |
| Faculty | `faculty1` | `Faculty@123` |
| Student | `student1` | `Student@123` |

## End-to-end usage

1. **Sign in.** `POST /api/v1/auth/login/` returns JWT tokens and a role. The frontend routes the user to the matching workspace.
2. **Prepare academic data.** An admin creates departments, sections, subjects, faculty, students, and subject-faculty-section mappings. A mapping is required before a session can be created.
3. **Create or seed sessions.** Sessions contain the subject, faculty, section, date, period, and status. The seed command creates completed demo sessions; new sessions can be created through the sessions API or Django admin.
4. **Mark attendance as faculty.** Open **My sessions**, select a session, or use the session link from that page. The marking screen loads only students in that session section. Choose Present, Absent, Late, or Excused for each student and save once for the whole section.
5. **Review faculty reports.** The faculty dashboard shows today’s assigned sessions and students below the selected threshold. Faculty reports and CSV export are scoped to records from that faculty member’s sessions.
6. **Request a correction.** A faculty member submits an attendance record ID, a different status, and a reason from **Request correction**. Admin reviews the pending request and approves or rejects it. An approved request updates the record and creates a change-log entry.
7. **Review attendance as a student.** Students can view only their own records, attendance percentage, subject breakdown, and calendar history.

## Validation and edge cases

- A faculty member can access and mark only their own mapped sessions. Admins can manage all sessions.
- Future-dated sessions and sessions without a matching subject-faculty-section mapping are rejected.
- Cancelled sessions cannot be marked. Cancelled sessions are excluded from percentages and class summaries.
- Every student in a bulk submission must belong to the session section. Duplicate student rows are rejected, and one student can have only one record per session.
- Present and Late count as attended. Absent and Excused do not.
- Attendance is calculated only from records on or after the student enrollment date.
- Faculty can update an existing record through bulk marking; changes are written to `AttendanceRecordChangeLog`.
- Correction requests require a non-blank reason, a different status, and must be within `CORRECTION_WINDOW_HOURS` for faculty. The default window is 48 hours.
- A correction can be resolved only once. Only admins can approve or reject requests.
- Report thresholds must be numeric and between 0 and 100. Class summaries require a valid `section_id`; malformed or missing scope is rejected instead of returning unrelated data.
- Student, faculty, session, record, and correction querysets are role-scoped on the server, not only hidden in the UI.

## API surface

Authentication:

- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/refresh/`

Attendance routers under `/api/v1/attendance/`:

- `departments`, `faculty`, `students`, `sections`, `subjects`, `subject-mappings`
- `sessions`, `records`, and `corrections`

Custom endpoints:

- `POST sessions/{id}/mark-bulk/`
- `GET reports/low-attendance/?threshold=75`
- `GET reports/class-summary/?section_id=&date_from=&date_to=`
- `GET reports/student-percentage/{student_id}/`
- `GET reports/export-csv/?type=class-summary`
- `POST corrections/{id}/approve/`
- `POST corrections/{id}/reject/`

List endpoints are paginated at 20 items. Sessions, records, and students support django-filter parameters defined in `backend/attendance/filters.py`.

## Verification

Run these checks from the repository root:

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

The current attendance suite contains ten tests covering cancelled-session protection, report authentication and scope validation, percentage calculation, uniqueness, student record isolation, department mapping validation, faculty report scoping, correction-window enforcement, and date-filter validation. The frontend production build completes successfully; Vite currently reports only its existing bundle-size warning.

## Known limitations

- MySQL is required by the configured backend; `backend/db.sqlite3` is not the active development database.
- There is no bulk CSV import UI yet. A future import should validate every row, report row-level errors, and skip duplicate roll numbers or employee IDs.
- Concurrent edits use last-write-wins. Change logs exist, but row locking and version tokens are out of scope.
- Section membership is based on the student’s current section. A future enrollment-history model would provide exact historical membership after transfers.
- The admin department chart currently uses representative frontend data rather than a backend aggregation.

## AI usage report

Claude Code was used to inspect the existing attendance flow, identify faculty edge cases, implement focused backend and frontend fixes, add regression tests, and update this documentation. Changes were verified with Django diagnostics, ten attendance tests, and a successful Vite production build. No credentials or external private data were used. The detailed submission report is maintained locally and is intentionally excluded from the GitHub repository.
