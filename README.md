# Smart Attendance Management System

Attendly is a role-aware attendance workspace for colleges. Administrators manage the academic structure and review corrections, faculty record attendance and monitor their assigned sections, and students view their own attendance history.

## Stack

- **Backend:** Django 5.2, Django REST Framework, SimpleJWT, django-filter, django-cors-headers, and MySQL.
- **Frontend:** React 19, Vite, React Router, Axios, and Recharts.
- **API base:** `/api/v1`.
- **Authorization:** JWT access tokens are attached by the frontend Axios interceptor. Access and refresh tokens are kept in memory for this demo, so a page refresh requires login again.

## Prerequisites

- Windows PowerShell, Python 3.11+ and `pip`
- Node.js 18+ and `npm`
- MySQL 8+ running locally or on a reachable server
- A MySQL database and user matching `backend/.env`

The backend currently uses MySQL from `backend/config/settings.py`. The committed `backend/db.sqlite3` file is not used by the application configuration.

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

The API is now available at `http://localhost:8000`. Keep this terminal running. If port 8000 is already occupied, start Django on another port, for example `python manage.py runserver 8001`, and update `frontend/.env` accordingly.

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

Open `http://localhost:5173/login` in a browser. The frontend development server must be running while using the application.

Demo credentials printed by the seed command:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `Admin@123` |
| Faculty | `faculty1` | `Faculty@123` |
| Student | `student1` | `Student@123` |

For a clean demo reset, run `python manage.py seed_data --reset-demo` from `backend`. This removes demo faculty and student attendance data before recreating the sample structure. Do not run it against data that must be preserved.

## End-to-end usage

1. **Sign in.** `POST /api/v1/auth/login/` returns JWT tokens and a role. The frontend routes the user to the matching workspace.
2. **Prepare academic data.** An admin creates departments, sections, subjects, faculty, students, and subject-faculty-section mappings. A mapping is required before a session can be created.
3. **Create or seed sessions.** Sessions contain the subject, faculty, section, date, period, and status. The seed command creates completed demo sessions; new sessions can be created through the sessions API or Django admin.
4. **Mark attendance as faculty.** Open **My sessions**, select a session, or use the session link from that page. The marking screen loads only students in that session section. Choose Present, Absent, Late, or Excused for each student and save once for the whole section.
5. **Review faculty reports.** The faculty dashboard shows today’s assigned sessions and students below the selected threshold. Faculty reports and CSV export are scoped to records from that faculty member’s sessions.
6. **Request a correction.** A faculty member submits an attendance record ID, a different status, and a reason from **Request correction**. Admin reviews the pending request and approves or rejects it. An approved request updates the record and creates a change-log entry.
7. **Review attendance as a student.** Students can view only their own records, attendance percentage, subject breakdown, and calendar history.

## Role-by-role application flow

### Admin flow

1. Sign in with the admin account and open **Departments**.
2. Create departments first because faculty, students, subjects, and sections reference them.
3. Open **Classes** and create each section with department, year, semester, and section name.
4. Create subjects with a department, code, semester, and credits.
5. Create faculty and student profiles. Each profile links to an existing Django user.
6. Create a subject mapping that connects one subject, one faculty member, and one section. The subject, faculty, and section must belong to the same department.
7. Create sessions through the sessions API or Django admin. A session needs a mapped subject, faculty, section, date, and period.
8. Use **Corrections** to review pending faculty requests. Approving changes the attendance record; rejecting preserves the original record.
9. Use **Reports** or the export endpoint for administrative reporting.

The admin frontend does not currently have a dedicated session-management page, so session creation is available through Django admin or the REST endpoint.

### Faculty flow

1. Sign in with a faculty account. The server scopes sessions and records to that faculty profile.
2. **Overview** shows today’s assigned sessions and the low-attendance watchlist.
3. **My sessions** lists recent and upcoming assigned sessions. Select a session to open the marking page.
4. **Mark attendance** loads only students in the selected session’s section. Set each status and save the whole section in one request.
5. Present and Late count toward attendance. Absent and Excused do not.
6. **Reports** accepts a threshold from 0 to 100 and returns only students represented in that faculty member’s sessions. CSV export is similarly scoped.
7. **Request correction** requires the attendance record ID, a different status, and a meaningful reason. Faculty corrections are restricted by `CORRECTION_WINDOW_HOURS`.

### Student flow

1. Sign in with a student account. Student endpoints are restricted to the authenticated student profile.
2. **Overview** shows the student’s attendance summary and low-attendance status.
3. **My attendance** shows attendance records and percentages.
4. **Calendar** presents attendance history by date.
5. A student cannot mark attendance, create corrections, view another student’s records, or access faculty/admin workspaces.

## Attendance lifecycle

```text
Department and academic records
	|
	v
Subject + Faculty + Section mapping
	|
	v
Attendance session (Scheduled)
	|
	v
Faculty bulk submission
	|
	v
Attendance records + change log
	|
	+--> Reports and percentages
	|
	+--> Faculty correction request --> Admin approval/rejection
```

Bulk marking changes a session to `Completed`. A `Cancelled` session cannot receive records. Existing records may be updated through bulk marking, and status changes create `AttendanceRecordChangeLog` entries.

## API request examples

All protected requests require:

```http
Authorization: Bearer <access-token>
```

Login:

```http
POST /api/v1/auth/login/
Content-Type: application/json

{"username": "faculty1", "password": "Faculty@123"}
```

Bulk attendance:

```http
POST /api/v1/attendance/sessions/12/mark-bulk/
Content-Type: application/json

{
  "records": [
    {"student_id": 21, "status": "Present"},
    {"student_id": 22, "status": "Absent"}
  ]
}
```

Correction request:

```http
POST /api/v1/attendance/corrections/
Content-Type: application/json

{"record": 81, "new_status": "Late", "reason": "The student arrived after roll call."}
```

Useful filters include `date_from` and `date_to` for sessions, `session` and `student` for records, and `threshold` for low-attendance reports. List responses are paginated and normally contain `count`, `next`, `previous`, and `results`.

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

## Troubleshooting

- **`manage.py` not found:** run Django commands from `backend`, or use `Push-Location backend` in PowerShell.
- **`package.json` not found:** run npm commands from `frontend`, or use `Push-Location frontend`.
- **Database connection errors:** confirm MySQL is running and that the values in `backend/.env` match an existing database and user.
- **CORS errors:** confirm `CORS_ALLOWED_ORIGINS` includes the frontend origin, normally `http://localhost:5173`.
- **401 responses:** log in again. Access tokens are memory-only and expire according to `SIMPLE_JWT` settings.
- **No faculty sessions:** verify that the faculty has a subject-faculty-section mapping and that the logged-in account is linked to the faculty profile.
- **No students while marking:** verify that students have the selected session section as their `current_section`.
- **Correction rejected:** check the record owner, correction window, current record status, reason length/content, and whether a pending correction already exists.

## AI usage report

Claude Code was used to inspect the existing attendance flow, identify faculty edge cases, implement focused backend and frontend fixes, add regression tests, and update this documentation. Changes were verified with Django diagnostics, ten attendance tests, and a successful Vite production build. No credentials or external private data were used. The detailed submission report is maintained locally and is intentionally excluded from the GitHub repository.
