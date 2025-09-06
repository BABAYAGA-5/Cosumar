from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_obtain_pair'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('utilisateurs/', views.get_all_utilisateurs, name='get_all_utilisateurs'),
    path('users/', views.get_all_utilisateurs, name='get_users'),
    path('users/<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('users/<int:user_id>/update-activity/', views.update_user_activity, name='update_user_activity'),
    path('users/<int:user_id>/update-role/', views.update_user_role, name='update_user_role'),
]
