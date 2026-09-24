from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import (
    AttendanceCorrectionRequest,
    AttendanceRecord,
    AttendanceSession,
    ClassSection,
    Department,
    Faculty,
    Student,
    Subject,
    SubjectFacultyMapping,
)

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class ClassSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSection
        fields = '__all__'


class FacultySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Faculty
        fields = ['id', 'user', 'username', 'name', 'employee_id', 'department', 'designation', 'phone']


class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'username', 'name', 'roll_no', 'department', 'current_section', 'admission_year', 'enrollment_date']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class SubjectFacultyMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectFacultyMapping
        fields = '__all__'


class AttendanceSessionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    section_name = serializers.CharField(source='section.section_name', read_only=True)

    class Meta:
        model = AttendanceSession
        fields = '__all__'
        read_only_fields = ['created_at']
        extra_kwargs = {'faculty': {'required': False}}

    def validate(self, attrs):
        instance = self.instance or AttendanceSession()
        if 'faculty' not in attrs and self.context.get('request') and hasattr(self.context['request'].user, 'faculty_profile'):
            attrs['faculty'] = self.context['request'].user.faculty_profile
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict if hasattr(error, 'message_dict') else error.messages)
        return attrs


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    roll_no = serializers.CharField(source='student.roll_no', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ['marked_by', 'marked_at']

    def validate(self, attrs):
        session = attrs.get('session', self.instance.session if self.instance else None)
        student = attrs.get('student', self.instance.student if self.instance else None)
        if session and session.status == AttendanceSession.Status.CANCELLED:
            raise serializers.ValidationError({'session': 'Attendance cannot be marked for a cancelled session.'})
        if session and student and session.section_id != student.current_section_id:
            raise serializers.ValidationError({'student': 'Student must belong to the session section.'})
        return attrs


class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceCorrectionRequest
        fields = '__all__'
        read_only_fields = ['requested_by', 'approval_status', 'approved_by', 'requested_at', 'resolved_at', 'old_status']

    def validate(self, attrs):
        record = attrs['record']
        if not attrs.get('reason', '').strip():
            raise serializers.ValidationError({'reason': 'A reason is required.'})
        attrs['old_status'] = record.status
        if attrs['new_status'] == record.status:
            raise serializers.ValidationError({'new_status': 'Choose a different attendance status.'})
        return attrs


class BulkAttendanceSerializer(serializers.Serializer):
    records = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_records(self, records):
        allowed = {choice[0] for choice in AttendanceRecord.Status.choices}
        for row in records:
            if 'student_id' not in row or row.get('status') not in allowed:
                raise serializers.ValidationError('Each row requires student_id and a valid status.')
        return records