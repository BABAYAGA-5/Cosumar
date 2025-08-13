from django.urls import path
from . import views

urlpatterns = [
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('domaines/', views.domaines, name='domaines'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('creation_stage/', views.creation_stage, name='creation_stage'),
    ]
