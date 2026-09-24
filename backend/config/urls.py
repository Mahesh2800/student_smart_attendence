from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from attendance.auth import CollegeTokenObtainPairSerializer


class CollegeTokenObtainPairView(TokenObtainPairView):
    serializer_class = CollegeTokenObtainPairSerializer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/attendance/', include('attendance.urls')),
    path('api/v1/auth/login/', CollegeTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
