from django.urls import path
from . import views

urlpatterns = [
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('domaines/', views.domaines, name='domaines'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('scan_cin/', views.scan_cin, name='scan_cin'),
    path('enregistrer_utilisateur/', views.enregistrer_utilisateur, name='enregistrer_utilisateur'),
    ]
