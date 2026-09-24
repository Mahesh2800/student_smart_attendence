import csv
import math
from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecordFilter, SessionFilter, StudentFilter
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
from .permissions import AdminWritePermission, AttendancePermission, CorrectionPermission, is_admin, is_faculty, is_student
from .serializers import (
    AttendanceCorrectionRequestSerializer,
    AttendanceRecordSerializer,
    AttendanceSessionSerializer,
    BulkAttendanceSerializer,
    ClassSectionSerializer,
    DepartmentSerializer,
    FacultySerializer,
    StudentSerializer,
    SubjectFacultyMappingSerializer,
    SubjectSerializer,
)

User = get_user_model()


class ScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminWritePermission]
    filter_backends = [DjangoFilterBackend]


class DepartmentViewSet(ScopedModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class FacultyViewSet(ScopedModelViewSet):
    queryset = Faculty.objects.select_related('user', 'department')
    serializer_class = FacultySerializer


class StudentViewSet(ScopedModelViewSet):
    queryset = Student.objects.select_related('user', 'department', 'current_section')
    serializer_class = StudentSerializer
    filterset_class = StudentFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_student(self.request.user):
            return queryset.filter(id=self.request.user.student_profile.id)
        return queryset


class ClassSectionViewSet(ScopedModelViewSet):
    queryset = ClassSection.objects.select_related('department')
    serializer_class = ClassSectionSerializer


class SubjectViewSet(ScopedModelViewSet):
    queryset = Subject.objects.select_related('department')
    serializer_class = SubjectSerializer


class SubjectFacultyMappingViewSet(ScopedModelViewSet):
    queryset = SubjectFacultyMapping.objects.select_related('subject', 'faculty', 'section')
    serializer_class = SubjectFacultyMappingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_faculty(self.request.user):
            return queryset.filter(faculty=self.request.user.faculty_profile)
        return queryset


class AttendanceSessionViewSet(ScopedModelViewSet):
    queryset = AttendanceSession.objects.select_related('subject', 'faculty', 'section')
    serializer_class = AttendanceSessionSerializer
    permission_classes = [AttendancePermission]
    filterset_class = SessionFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_faculty(self.request.user):
            return queryset.filter(faculty=self.request.user.faculty_profile)
        if is_student(self.request.user):
            return queryset.filter(section=self.request.user.student_profile.current_section)
        return queryset

    def perform_create(self, serializer):
        if not (is_admin(self.request.user) or is_faculty(self.request.user)):
            raise PermissionDenied('Only admins and faculty can create sessions.')
        if is_faculty(self.request.user):
            serializer.save(faculty=self.request.user.faculty_profile)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='mark-bulk')
    def mark_bulk(self, request, pk=None):
        session = self.get_object()
        if not is_admin(request.user) and session.faculty_id != request.user.faculty_profile.id:
            raise PermissionDenied('You can only mark your own mapped sessions.')
        if session.status == AttendanceSession.Status.CANCELLED:
            raise ValidationError('Attendance cannot be marked for a cancelled session.')
        payload = BulkAttendanceSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        student_ids = [row['student_id'] for row in payload.validated_data['records']]
        students = {student.id: student for student in Student.objects.filter(id__in=student_ids, current_section=session.section)}
        if len(students) != len(student_ids):
            raise ValidationError('Every student must belong to the session section.')
        marker = request.user.faculty_profile if is_faculty(request.user) else session.faculty
        with transaction.atomic():
            for row in payload.validated_data['records']:
                record, created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student_id=row['student_id'],
                    defaults={'status': row['status'], 'marked_by': marker},
                )
                if not created:
                    old_status = record.status
                    record.status = row['status']
                    record.marked_by = marker
                    record.save()
                    AttendanceRecordChangeLog.objects.create(record=record, changed_by=marker, old_status=old_status, new_status=record.status)
        session.status = AttendanceSession.Status.COMPLETED
        session.save(update_fields=['status'])
        return Response({'updated': len(student_ids)})


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related('session', 'student__user', 'marked_by')
    serializer_class = AttendanceRecordSerializer
    permission_classes = [AttendancePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecordFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_student(self.request.user):
            return queryset.filter(student=self.request.user.student_profile)
        if is_faculty(self.request.user):
            return queryset.filter(session__faculty=self.request.user.faculty_profile)
        return queryset

    def perform_create(self, serializer):
        if not (is_admin(self.request.user) or is_faculty(self.request.user)):
            raise PermissionDenied('Only admins and faculty can mark attendance.')
        if not is_admin(self.request.user) and serializer.validated_data['session'].faculty_id != self.request.user.faculty_profile.id:
            raise PermissionDenied('You cannot mark this session.')
        marker = self.request.user.faculty_profile if is_faculty(self.request.user) else serializer.validated_data['session'].faculty
        serializer.save(marked_by=marker)


class AttendanceCorrectionRequestViewSet(viewsets.ModelViewSet):
    queryset = AttendanceCorrectionRequest.objects.select_related('record__session', 'record__student', 'requested_by')
    serializer_class = AttendanceCorrectionRequestSerializer
    permission_classes = [CorrectionPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_faculty(self.request.user):
            return queryset.filter(requested_by=self.request.user)
        if is_student(self.request.user):
            return queryset.none()
        return queryset

    def perform_create(self, serializer):
        record = serializer.validated_data['record']
        if not is_admin(self.request.user) and record.session.faculty_id != self.request.user.faculty_profile.id:
            raise PermissionDenied('You can only correct your own records.')
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self._resolve(request, self.get_object(), AttendanceCorrectionRequest.ApprovalStatus.APPROVED)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._resolve(request, self.get_object(), AttendanceCorrectionRequest.ApprovalStatus.REJECTED)

    def _resolve(self, request, correction, decision):
        if not is_admin(request.user):
            raise PermissionDenied('Only admins can resolve correction requests.')
        if correction.approval_status != AttendanceCorrectionRequest.ApprovalStatus.PENDING:
            raise ValidationError('This correction has already been resolved.')
        with transaction.atomic():
            correction.approval_status = decision
            correction.approved_by = request.user
            correction.resolved_at = timezone.now()
            correction.save(update_fields=['approval_status', 'approved_by', 'resolved_at'])
            if decision == AttendanceCorrectionRequest.ApprovalStatus.APPROVED:
                record = correction.record
                if record.status != correction.old_status:
                    raise ValidationError('This correction is stale because the record has changed.')
                old_status = record.status
                record.status = correction.new_status
                record.save(update_fields=['status', 'marked_at'])
                AttendanceRecordChangeLog.objects.create(record=record, old_status=old_status, new_status=record.status)
        return Response(self.get_serializer(correction).data)


def _percentage(records):
    eligible = [record for record in records if record.session.status != AttendanceSession.Status.CANCELLED]
    if not eligible:
        return 0
    present = sum(record.status in [AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE] for record in eligible)
    return round((present / len(eligible)) * 100, 2)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def low_attendance(request):
    try:
        threshold = float(request.query_params.get('threshold', 75))
    except (TypeError, ValueError):
        raise ValidationError({'threshold': 'Threshold must be a number between 0 and 100.'})
    if not math.isfinite(threshold) or not 0 <= threshold <= 100:
        raise ValidationError({'threshold': 'Threshold must be between 0 and 100.'})
    students = Student.objects.select_related('user', 'department')
    if is_faculty(request.user):
        students = students.filter(attendance_records__session__faculty=request.user.faculty_profile).distinct()
    elif is_student(request.user):
        students = students.filter(id=request.user.student_profile.id)
    result = []
    for student in students:
        records_query = student.attendance_records.select_related('session__subject', 'session').filter(session__date__gte=student.enrollment_date)
        if is_faculty(request.user):
            records_query = records_query.filter(session__faculty=request.user.faculty_profile)
        records = list(records_query)
        percentage = _percentage(records)
        if percentage < threshold:
            by_subject = {}
            for record in records:
                by_subject.setdefault(record.session.subject.code, []).append(record)
            result.append({'student_id': student.id, 'roll_no': student.roll_no, 'name': student.user.get_full_name(), 'percentage': percentage, 'subjects': {code: _percentage(rows) for code, rows in by_subject.items()}})
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_percentage(request, student_id):
    if is_student(request.user) and request.user.student_profile.id != student_id:
        raise PermissionDenied('You can only view your own attendance.')
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        raise ValidationError({'student_id': 'Student not found.'})
    records = student.attendance_records.select_related('session__subject', 'session')
    if is_faculty(request.user):
        records = records.filter(session__faculty=request.user.faculty_profile)
        if not records.exists():
            raise PermissionDenied('You can only view students from your sessions.')
    by_subject = {}
    for record in records:
        # Enrollment dates exclude sessions before a student joined; cancelled sessions have no denominator.
        if record.session.date >= student.enrollment_date:
            by_subject.setdefault(record.session.subject.code, []).append(record)
    return Response({'student_id': student.id, 'overall': _percentage([r for rows in by_subject.values() for r in rows]), 'subjects': {code: _percentage(rows) for code, rows in by_subject.items()}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_summary(request):
    section_id = request.query_params.get('section_id')
    if not section_id:
        raise ValidationError({'section_id': 'section_id is required.'})
    try:
        section_id = int(section_id)
    except ValueError:
        raise ValidationError({'section_id': 'section_id must be an integer.'})
    records = AttendanceRecord.objects.select_related('session', 'student').filter(session__section_id=section_id).exclude(session__status=AttendanceSession.Status.CANCELLED)
    for parameter, lookup in [('date_from', 'gte'), ('date_to', 'lte')]:
        value = request.query_params.get(parameter)
        if value:
            try:
                records = records.filter(**{f'session__date__{lookup}': date.fromisoformat(value)})
            except ValueError:
                raise ValidationError({parameter: 'Use YYYY-MM-DD.'})
    if is_faculty(request.user):
        records = records.filter(session__faculty=request.user.faculty_profile)
    return Response({'section_id': section_id, 'total_records': records.count(), 'present': records.filter(status__in=['Present', 'Late']).count(), 'absent': records.filter(status='Absent').count()})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request):
    if not is_admin(request.user) and not is_faculty(request.user):
        raise PermissionDenied('Only admins and faculty can export reports.')
    records = AttendanceRecord.objects.select_related('student', 'session__subject', 'session__section')
    if is_faculty(request.user):
        records = records.filter(session__faculty=request.user.faculty_profile)
    def rows():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['roll_no', 'subject', 'date', 'status'])
        yield output.getvalue()
        for record in records.iterator():
            output.seek(0)
            output.truncate(0)
            writer.writerow([record.student.roll_no, record.session.subject.code, record.session.date, record.status])
            yield output.getvalue()

    response = StreamingHttpResponse(rows(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance-report.csv"'
    return response
