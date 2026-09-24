from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceCorrectionRequestViewSet,
    AttendanceRecordViewSet,
    AttendanceSessionViewSet,
    ClassSectionViewSet,
    DepartmentViewSet,
    FacultyViewSet,
    StudentViewSet,
    SubjectFacultyMappingViewSet,
    SubjectViewSet,
    class_summary,
    export_csv,
    low_attendance,
    student_percentage,
)

router = DefaultRouter()
router.register('departments', DepartmentViewSet)
router.register('faculty', FacultyViewSet)
router.register('students', StudentViewSet)
router.register('sections', ClassSectionViewSet)
router.register('subjects', SubjectViewSet)
router.register('subject-mappings', SubjectFacultyMappingViewSet)
router.register('sessions', AttendanceSessionViewSet)
router.register('records', AttendanceRecordViewSet)
router.register('corrections', AttendanceCorrectionRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('reports/low-attendance/', low_attendance),
    path('reports/class-summary/', class_summary),
    path('reports/student-percentage/<int:student_id>/', student_percentage),
    path('reports/export-csv/', export_csv),
]