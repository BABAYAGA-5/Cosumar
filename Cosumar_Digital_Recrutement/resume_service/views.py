from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FileUploadParser
from django.shortcuts import render
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
import os
import filetype

# Handle CIN module import with fallback
try:
    from .CIN import extract_cin_data
except ImportError:
    try:
        from CIN import extract_cin_data
    except ImportError:
        def extract_cin_data(image_bytes):
            """Fallback function when CIN module is not available"""
            return {}

from resume_service.models import Stage, Stagiaire, Sujet
from auth_service.models import Utilisateur
from django.db.models import Count, Q
from datetime import datetime, timedelta

def get_public_key():
    try:
        with open(settings.BASE_DIR / 'keys' / 'public.pem') as f:
            return f.read()
    except FileNotFoundError:
        return settings.SECRET_KEY

@csrf_exempt
@api_view(['POST'])  # ← ✅ This is the annotation you meant
def upload_pdf(request):
    pdf_file = request.FILES['file']
    pdf_bytes = pdf_file.read()
    return Response({"message": "PDF received", "size": len(pdf_bytes)})

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def domaines(request):
    token = request.headers.get('Authorization')

    return Response({'message': 'Domaines endpoint is working'}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    pass

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creation_stage(request):
    """Upload and scan Moroccan CIN (ID card) image"""
    try:
        stagiaire_id = request.data.get('stagiaire_id')
        sujet = request.data.get('sujet')
        nature = request.data.get('nature')
        cin_file = request.FILES['cin']
        
        if sujet is None or nature is None:
            return Response({
                "error": "Sujet et nature sont requis."
            }, status=status.HTTP_400_BAD_REQUEST)

        allowed_extensions = ['jpg', 'jpeg', 'png']

        ext = os.path.splitext(request.FILES['cin'].name)[1].lower().lstrip('.') 

        if ext not in allowed_extensions:
            return Response({
                "error": "Type de fichier non autorisé. Veuillez télécharger une image aux formats JPG, JPEG ou PNG.",
                "type": ext
            }, status=status.HTTP_400_BAD_REQUEST)

        cin_bytes = cin_file.read()
        data = extract_cin_data(cin_bytes)
        
        print(f"Extracted data: {data}")  # Debug logging
        
        # Check if we have valid CIN data
        if data and data.get('cin') and data.get('cin') != 'unknown':
            stagiaire = Stagiaire.objects.create(
                matricule=data.get('cin'), 
                prenom=data.get('prenom', 'unknown'), 
                nom=data.get('nom', 'unknown'), 
                date_naissance=data.get('date_naissance'), 
                cin=cin_bytes
            )
            stagiaire.save()
            stage = Stage.objects.create(stagiaire=stagiaire, nature=nature, sujet=sujet)
            stage.save()
            return Response({
                "message": "CIN scannée avec succès",
                "data": data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "CIN scan échoué - aucune donnée valide extraite",
                "extracted_data": data
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            "error": f"CIN processing error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)