from django.contrib import admin

from .models import (
	AttendanceCorrectionRequest,
	AttendanceRecord,
	AttendanceRecordChangeLog,
	AttendanceSession,
	ClassSection,
	Department,
	Faculty,
	Student,
	Subject,
	SubjectFacultyMapping,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'created_at')
	search_fields = ('code', 'name')


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
	list_display = ('employee_id', 'user', 'department', 'designation')
	list_filter = ('department', 'designation')
	search_fields = ('employee_id', 'user__username', 'user__last_name')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
	list_display = ('roll_no', 'user', 'department', 'current_section', 'admission_year')
	list_filter = ('department', 'current_section', 'admission_year')
	search_fields = ('roll_no', 'user__username', 'user__last_name')


admin.site.register([ClassSection, Subject, SubjectFacultyMapping, AttendanceSession, AttendanceRecord, AttendanceRecordChangeLog, AttendanceCorrectionRequest])
