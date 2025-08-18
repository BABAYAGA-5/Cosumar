from django.urls import path
from . import views

urlpatterns = [
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('domaines/', views.domaines, name='domaines'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('scan_cin/', views.scan_cin, name='scan_cin'),
    path('enregistrer_stagiaire/', views.enregistrer_stagiaire, name='enregistrer_stagiaire'),
    path('chercher_stagiaires/', views.chercher_stagiaires, name='chercher_stagiaires'),
    path('chercher_stages/', views.chercher_stages, name='chercher_stages'),
    path('chercher_sujets/', views.chercher_sujets, name='chercher_sujets'),
]
