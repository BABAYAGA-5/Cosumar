from django.urls import path
from . import views

urlpatterns = [
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('test/', views.test, name='test'),
    path('domaines/', views.domaines, name='domaines'),
]
