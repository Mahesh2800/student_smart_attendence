from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CollegeTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = 'admin' if user.is_staff or user.is_superuser else 'faculty' if hasattr(user, 'faculty_profile') else 'student'
        if hasattr(user, 'student_profile'):
            token['student_id'] = user.student_profile.id
        if hasattr(user, 'faculty_profile'):
            token['faculty_id'] = user.faculty_profile.id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = 'admin' if self.user.is_staff or self.user.is_superuser else 'faculty' if hasattr(self.user, 'faculty_profile') else 'student'
        data['username'] = self.user.username
        if hasattr(self.user, 'student_profile'):
            data['student_id'] = self.user.student_profile.id
        if hasattr(self.user, 'faculty_profile'):
            data['faculty_id'] = self.user.faculty_profile.id
        return data