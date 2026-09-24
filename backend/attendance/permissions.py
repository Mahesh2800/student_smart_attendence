from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_faculty(user):
    return user.is_authenticated and hasattr(user, 'faculty_profile')


def is_student(user):
    return user.is_authenticated and hasattr(user, 'student_profile')


class AttendancePermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        if is_student(request.user):
            return request.method in SAFE_METHODS and getattr(obj, 'student_id', None) == request.user.student_profile.id
        if is_faculty(request.user):
            faculty_id = request.user.faculty_profile.id
            owner = getattr(obj, 'faculty_id', None) == faculty_id
            if hasattr(obj, 'session'):
                owner = obj.session.faculty_id == faculty_id
            return owner
        return False


class AdminWritePermission(AttendancePermission):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return is_admin(request.user) or (is_faculty(request.user) and request.method in SAFE_METHODS)


class CorrectionPermission(AttendancePermission):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return is_admin(request.user) or is_faculty(request.user)