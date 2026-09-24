from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import AttendanceCorrectionRequest, AttendanceRecord, AttendanceSession, ClassSection, Department, Faculty, Student, Subject, SubjectFacultyMapping
from .views import _percentage

User = get_user_model()


class AttendanceBehaviorTests(TestCase):
	def setUp(self):
		self.department = Department.objects.create(name='Engineering', code='ENG')
		self.section = ClassSection.objects.create(department=self.department, year=1, semester=1, section_name='A')
		self.subject = Subject.objects.create(name='Algorithms', code='CS101', department=self.department, semester=1)
		faculty_user = User.objects.create_user('faculty', password='pass')
		self.faculty = Faculty.objects.create(user=faculty_user, employee_id='EMP1', department=self.department)
		student_user = User.objects.create_user('student', password='pass')
		self.student = Student.objects.create(user=student_user, roll_no='R1', department=self.department, current_section=self.section, admission_year=2026, enrollment_date=timezone.localdate() - timedelta(days=30))
		SubjectFacultyMapping.objects.create(subject=self.subject, faculty=self.faculty, section=self.section)
		self.session = AttendanceSession.objects.create(subject=self.subject, faculty=self.faculty, section=self.section, date=timezone.localdate() - timedelta(days=1), period_number=1, status=AttendanceSession.Status.COMPLETED)

	def test_percentage_excludes_cancelled_sessions(self):
		AttendanceRecord.objects.create(session=self.session, student=self.student, status='Present', marked_by=self.faculty)
		cancelled = AttendanceSession.objects.create(subject=self.subject, faculty=self.faculty, section=self.section, date=timezone.localdate() - timedelta(days=2), period_number=1, status=AttendanceSession.Status.CANCELLED)
		AttendanceRecord.objects.create(session=cancelled, student=self.student, status='Absent', marked_by=self.faculty)
		self.assertEqual(_percentage(list(self.student.attendance_records.select_related('session'))), 100)

	def test_unique_attendance_submission_is_rejected(self):
		AttendanceRecord.objects.create(session=self.session, student=self.student, status='Present', marked_by=self.faculty)
		with self.assertRaises(Exception):
			AttendanceRecord.objects.create(session=self.session, student=self.student, status='Absent', marked_by=self.faculty)

	def test_student_record_queryset_is_scoped(self):
		client = APIClient()
		client.force_authenticate(self.student.user)
		response = client.get('/api/v1/attendance/records/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['count'], 0)

	def test_reports_require_authentication(self):
		response = APIClient().get('/api/v1/attendance/reports/low-attendance/')
		self.assertEqual(response.status_code, 401)

	def test_faculty_cannot_mark_cancelled_session(self):
		cancelled = AttendanceSession.objects.create(subject=self.subject, faculty=self.faculty, section=self.section, date=timezone.localdate() - timedelta(days=2), period_number=1, status=AttendanceSession.Status.CANCELLED)
		client = APIClient()
		client.force_authenticate(self.faculty.user)
		response = client.post(f'/api/v1/attendance/sessions/{cancelled.id}/mark-bulk/', {'records': [{'student_id': self.student.id, 'status': 'Present'}]}, format='json')
		self.assertEqual(response.status_code, 400)
		self.assertFalse(AttendanceRecord.objects.filter(session=cancelled).exists())

	def test_report_filters_reject_invalid_scope(self):
		client = APIClient()
		client.force_authenticate(self.faculty.user)
		self.assertEqual(client.get('/api/v1/attendance/reports/low-attendance/?threshold=101').status_code, 400)
		self.assertEqual(client.get('/api/v1/attendance/reports/class-summary/').status_code, 400)

	def test_mapping_rejects_cross_department_relationships(self):
		other_department = Department.objects.create(name='Science', code='SCI')
		other_section = ClassSection.objects.create(department=other_department, year=1, semester=1, section_name='A')
		mapping = SubjectFacultyMapping(subject=self.subject, faculty=self.faculty, section=other_section)
		with self.assertRaises(Exception):
			mapping.full_clean()

	def test_faculty_reports_use_only_their_records(self):
		other_user = User.objects.create_user('faculty2', password='pass')
		other_faculty = Faculty.objects.create(user=other_user, employee_id='EMP2', department=self.department)
		SubjectFacultyMapping.objects.create(subject=self.subject, faculty=other_faculty, section=self.section)
		other_session = AttendanceSession.objects.create(subject=self.subject, faculty=other_faculty, section=self.section, date=timezone.localdate() - timedelta(days=2), period_number=1, status=AttendanceSession.Status.COMPLETED)
		AttendanceRecord.objects.create(session=self.session, student=self.student, status='Present', marked_by=self.faculty)
		AttendanceRecord.objects.create(session=other_session, student=self.student, status='Absent', marked_by=other_faculty)
		client = APIClient()
		client.force_authenticate(self.faculty.user)
		response = client.get(f'/api/v1/attendance/reports/student-percentage/{self.student.id}/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['overall'], 100)

	def test_faculty_correction_window_is_enforced(self):
		old_session = AttendanceSession.objects.create(subject=self.subject, faculty=self.faculty, section=self.section, date=timezone.localdate() - timedelta(days=10), period_number=1, status=AttendanceSession.Status.COMPLETED)
		record = AttendanceRecord.objects.create(session=old_session, student=self.student, status='Present', marked_by=self.faculty)
		client = APIClient()
		client.force_authenticate(self.faculty.user)
		response = client.post('/api/v1/attendance/corrections/', {'record': record.id, 'new_status': 'Absent', 'reason': 'Correcting an old entry'}, format='json')
		self.assertEqual(response.status_code, 400)
		self.assertFalse(AttendanceCorrectionRequest.objects.filter(record=record).exists())

	def test_class_summary_validates_date_filters(self):
		client = APIClient()
		client.force_authenticate(self.faculty.user)
		response = client.get(f'/api/v1/attendance/reports/class-summary/?section_id={self.section.id}&date_from=not-a-date')
		self.assertEqual(response.status_code, 400)
