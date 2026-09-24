import django_filters

from .models import AttendanceRecord, AttendanceSession, Student


class SessionFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = AttendanceSession
        fields = ['subject', 'section', 'faculty', 'status', 'date_from', 'date_to']


class RecordFilter(django_filters.FilterSet):
    class Meta:
        model = AttendanceRecord
        fields = ['session', 'student', 'status']


class StudentFilter(django_filters.FilterSet):
    class Meta:
        model = Student
        fields = ['department', 'current_section', 'admission_year']