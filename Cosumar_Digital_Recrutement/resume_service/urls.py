from django.urls import path
from . import views

urlpatterns = [
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('domaines/', views.domaines, name='domaines'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('scan_cin/', views.scan_cin, name='scan_cin'),
    path('enregistrer_stagiaire/', views.enregistrer_stagiaire, name='enregistrer_stagiaire'),
    path('creer_stage/', views.creer_stage, name='creer_stage'),
    path('chercher_stagiaires/', views.chercher_stagiaires, name='chercher_stagiaires'),
    path('chercher_stages/', views.chercher_stages, name='chercher_stages'),
    path('chercher_sujets/', views.chercher_sujets, name='chercher_sujets'),
    path('process_cv/', views.process_cv, name='process_cv'),
    path('get_candidate_documents/<str:matricule>/', views.get_candidate_documents, name='get_candidate_documents'),
    path('recuperer_stage/<str:stage_id>/', views.recuperer_stage, name='recuperer_stage'),
    path('update_stage/<str:stage_id>/', views.update_stage, name='update_stage'),
    path('get_cin/<str:matricule>/', views.get_cin, name='get_cin'),
    path('get_stage_document/<str:stage_id>/<str:document_type>/', views.get_stage_document, name='get_stage_document'),
    path('upload_stage_document/<str:stage_id>/', views.upload_stage_document, name='upload_stage_document'),
]
