from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('test/', views.test, name='test'),  # New endpoint for testing
]
