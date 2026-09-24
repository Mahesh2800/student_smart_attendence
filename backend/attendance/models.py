from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Department(models.Model):
	name = models.CharField(max_length=120, unique=True)
	code = models.CharField(max_length=20, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return f'{self.code} - {self.name}'


class ClassSection(models.Model):
	department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='sections')
	year = models.PositiveSmallIntegerField()
	semester = models.PositiveSmallIntegerField()
	section_name = models.CharField(max_length=20)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['department', 'year', 'semester', 'section_name'], name='unique_class_section')]
		ordering = ['department__code', 'year', 'semester', 'section_name']

	def __str__(self):
		return f'{self.department.code} Y{self.year} S{self.semester}-{self.section_name}'


class Faculty(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='faculty_profile')
	employee_id = models.CharField(max_length=30, unique=True)
	department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='faculty')
	designation = models.CharField(max_length=80, default='Faculty')
	phone = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return f'{self.employee_id} - {self.user.get_full_name() or self.user.username}'


class Student(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
	roll_no = models.CharField(max_length=30, unique=True)
	department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='students')
	current_section = models.ForeignKey(ClassSection, on_delete=models.PROTECT, related_name='current_students')
	admission_year = models.PositiveSmallIntegerField()
	enrollment_date = models.DateField()

	def __str__(self):
		return f'{self.roll_no} - {self.user.get_full_name() or self.user.username}'


class Subject(models.Model):
	name = models.CharField(max_length=150)
	code = models.CharField(max_length=30, unique=True)
	department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='subjects')
	credits = models.PositiveSmallIntegerField(default=3)
	semester = models.PositiveSmallIntegerField()

	class Meta:
		ordering = ['code']

	def __str__(self):
		return f'{self.code} - {self.name}'


class SubjectFacultyMapping(models.Model):
	subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='faculty_mappings')
	faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='subject_mappings')
	section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='subject_mappings')

	class Meta:
		constraints = [models.UniqueConstraint(fields=['subject', 'faculty', 'section'], name='unique_subject_faculty_section')]

	def clean(self):
		errors = {}
		if self.subject_id and self.section_id and self.subject.department_id != self.section.department_id:
			errors['section'] = 'Subject and section must belong to the same department.'
		if self.faculty_id and self.section_id and self.faculty.department_id != self.section.department_id:
			errors['faculty'] = 'Faculty and section must belong to the same department.'
		if errors:
			raise ValidationError(errors)


class AttendanceSession(models.Model):
	class Status(models.TextChoices):
		SCHEDULED = 'Scheduled', 'Scheduled'
		COMPLETED = 'Completed', 'Completed'
		CANCELLED = 'Cancelled', 'Cancelled'

	subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='sessions')
	faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='sessions')
	section = models.ForeignKey(ClassSection, on_delete=models.PROTECT, related_name='sessions')
	date = models.DateField()
	period_number = models.PositiveSmallIntegerField()
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['subject', 'faculty', 'section', 'date', 'period_number'], name='unique_attendance_session')]
		ordering = ['-date', '-period_number']

	def clean(self):
		if self.date > timezone.localdate():
			raise ValidationError({'date': 'Attendance cannot be recorded for a future date.'})
		if not SubjectFacultyMapping.objects.filter(subject=self.subject, faculty=self.faculty, section=self.section).exists():
			raise ValidationError('Faculty is not mapped to this subject and section.')

	def __str__(self):
		return f'{self.subject.code} {self.section} on {self.date} P{self.period_number}'


class AttendanceRecord(models.Model):
	class Status(models.TextChoices):
		PRESENT = 'Present', 'Present'
		ABSENT = 'Absent', 'Absent'
		LATE = 'Late', 'Late'
		EXCUSED = 'Excused', 'Excused'

	session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
	student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
	status = models.CharField(max_length=20, choices=Status.choices)
	marked_by = models.ForeignKey(Faculty, on_delete=models.PROTECT, related_name='marked_records')
	marked_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=['session', 'student'], name='unique_session_student_record')]
		ordering = ['student__roll_no']

	def clean(self):
		if self.session.section_id != self.student.current_section_id:
			# The session keeps the historical section; transfers should be handled by an enrollment history extension.
			# We allow the record here so historical attendance remains immutable to a current-section change.
			pass


class AttendanceRecordChangeLog(models.Model):
	record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='change_logs')
	changed_by = models.ForeignKey(Faculty, on_delete=models.PROTECT, null=True, blank=True)
	old_status = models.CharField(max_length=20, blank=True)
	new_status = models.CharField(max_length=20)
	changed_at = models.DateTimeField(auto_now_add=True)


class AttendanceCorrectionRequest(models.Model):
	class ApprovalStatus(models.TextChoices):
		PENDING = 'Pending', 'Pending'
		APPROVED = 'Approved', 'Approved'
		REJECTED = 'Rejected', 'Rejected'

	record = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name='correction_requests')
	requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='correction_requests')
	reason = models.TextField()
	old_status = models.CharField(max_length=20, choices=AttendanceRecord.Status.choices)
	new_status = models.CharField(max_length=20, choices=AttendanceRecord.Status.choices)
	approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
	approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='approved_corrections', null=True, blank=True)
	requested_at = models.DateTimeField(auto_now_add=True)
	resolved_at = models.DateTimeField(null=True, blank=True)

	def clean(self):
		if not self.reason.strip():
			raise ValidationError({'reason': 'A reason is required.'})
		if self.requested_by and not (self.requested_by.is_staff or self.requested_by.is_superuser):
			window_hours = getattr(settings, 'CORRECTION_WINDOW_HOURS', 48)
			cutoff = timezone.now() - timedelta(hours=window_hours)
			session_date = self.record.session.date
			if session_date < cutoff.date():
				raise ValidationError(f'Faculty corrections are limited to {window_hours} hours.')

	def __str__(self):
		return f'{self.record} - {self.approval_status}'
