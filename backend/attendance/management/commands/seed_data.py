import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import (
    AttendanceRecord,
    AttendanceRecordChangeLog,
    AttendanceCorrectionRequest,
    AttendanceSession,
    ClassSection,
    Department,
    Faculty,
    Student,
    Subject,
    SubjectFacultyMapping,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a repeatable demo dataset for Smart Attendance.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-demo', action='store_true', help='Remove existing demo users and attendance before seeding.')

    def handle(self, *args, **options):
        random.seed(42)
        if options['reset_demo']:
            demo_user_ids = list(User.objects.filter(username__startswith='faculty').values_list('id', flat=True))
            demo_user_ids += list(User.objects.filter(username__startswith='student').values_list('id', flat=True))
            # Clear dependent records first because marked_by and correction approver use protected relations.
            AttendanceCorrectionRequest.objects.all().delete()
            AttendanceRecordChangeLog.objects.all().delete()
            AttendanceRecord.objects.all().delete()
            AttendanceSession.objects.all().delete()
            SubjectFacultyMapping.objects.all().delete()
            Faculty.objects.filter(user_id__in=demo_user_ids).delete()
            Student.objects.filter(user_id__in=demo_user_ids).delete()
            User.objects.filter(id__in=demo_user_ids).delete()
        departments = []
        for index in range(5):
            departments.append(Department.objects.get_or_create(code=f'DEPT{index + 1}', defaults={'name': f'Department {index + 1}'})[0])
        sections = []
        for department in departments:
            for year in range(1, 4):
                for section_name in ('A', 'B'):
                    sections.append(ClassSection.objects.get_or_create(department=department, year=year, semester=year * 2, section_name=section_name)[0])
        subjects = []
        for index in range(45):
            department = departments[index % len(departments)]
            subjects.append(Subject.objects.get_or_create(code=f'SUB{index + 1:03}', defaults={'name': f'Core Subject {index + 1}', 'department': department, 'credits': 3, 'semester': (index % 6) + 1})[0])

        admin, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@college.test', 'is_staff': True, 'is_superuser': True})
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password('Admin@123')
        admin.save()

        faculty_profiles = []
        for index in range(10):
            user, _ = User.objects.get_or_create(username=f'faculty{index + 1}', defaults={'first_name': 'Faculty', 'last_name': str(index + 1)})
            user.set_password('Faculty@123')
            user.save()
            faculty_profiles.append(Faculty.objects.get_or_create(user=user, defaults={'employee_id': f'EMP{index + 1:03}', 'department': departments[index % 5], 'designation': 'Assistant Professor'})[0])

        student_profiles = []
        enrollment_date = timezone.localdate() - timedelta(days=120)
        for index in range(50):
            user, _ = User.objects.get_or_create(username=f'student{index + 1}', defaults={'first_name': 'Student', 'last_name': str(index + 1)})
            user.set_password('Student@123')
            user.save()
            section = sections[index % len(sections)]
            student_profiles.append(Student.objects.get_or_create(user=user, defaults={'roll_no': f'ROLL{index + 1:04}', 'department': section.department, 'current_section': section, 'admission_year': timezone.localdate().year - section.year + 1, 'enrollment_date': enrollment_date})[0])

        for index, subject in enumerate(subjects):
            faculty = faculty_profiles[index % len(faculty_profiles)]
            section = sections[index % len(sections)]
            SubjectFacultyMapping.objects.get_or_create(subject=subject, faculty=faculty, section=section)

        today = timezone.localdate()
        for day_offset in range(1, 22):
            session_date = today - timedelta(days=day_offset)
            if session_date.weekday() >= 5:
                continue
            for index, mapping in enumerate(SubjectFacultyMapping.objects.select_related('subject', 'faculty', 'section').all()[:24]):
                session, _ = AttendanceSession.objects.get_or_create(subject=mapping.subject, faculty=mapping.faculty, section=mapping.section, date=session_date, period_number=(index % 5) + 1, defaults={'status': AttendanceSession.Status.COMPLETED})
                if index % 17 == 0:
                    session.status = AttendanceSession.Status.CANCELLED
                    session.save(update_fields=['status'])
                    continue
                for student in Student.objects.filter(current_section=mapping.section):
                    status = random.choices(['Present', 'Absent', 'Late', 'Excused'], weights=[78, 14, 6, 2])[0]
                    AttendanceRecord.objects.get_or_create(session=session, student=student, defaults={'status': status, 'marked_by': mapping.faculty})
        self.stdout.write(self.style.SUCCESS('Seed complete.'))
        self.stdout.write('Admin: admin / Admin@123')
        self.stdout.write('Faculty: faculty1 / Faculty@123')
        self.stdout.write('Student: student1 / Student@123')
