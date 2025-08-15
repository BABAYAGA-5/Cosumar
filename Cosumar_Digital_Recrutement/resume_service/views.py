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
def scan_cin(request):
    try:
        cin_file = request.FILES.get('cin')

        if not cin_file:
            return Response({"error": "Fichier CIN manquant."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate extension
        allowed_extensions = ['jpg', 'jpeg', 'png']
        ext = os.path.splitext(cin_file.name)[1].lower().lstrip('.')
        if ext not in allowed_extensions:
            return Response({
                "error": "Type de fichier non autorisé. Veuillez télécharger JPG, JPEG ou PNG.",
                "type": ext
            }, status=status.HTTP_400_BAD_REQUEST)

        # Read file bytes
        cin_bytes = cin_file.read()

        # Extract data
        data = extract_cin_data(cin_bytes)
        print(f"Extracted data: {data}")

        if not data or not data.get('cin') or data.get('cin') == 'unknown':
            return Response({
                "error": "CIN scan échoué - aucune donnée valide extraite",
                "extracted_data": data
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "CIN scannée avec succès",
            "data": data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"CIN processing error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enregistrer_utilisateur(request):
    """Save user with CIN data and file"""
    try:
        nom = request.data.get('nom')
        prenom = request.data.get('prenom')
        cin = request.data.get('cin')
        date_naissance = request.data.get('date_naissance')
        cin_file = request.FILES.get('cin_file')

        if not all([nom, prenom, cin]):
            return Response({
                "error": "Nom, prénom et numéro CIN sont requis."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Read CIN file bytes if provided
        cin_bytes = None
        if cin_file:
            cin_bytes = cin_file.read()

        # Parse date if provided
        parsed_date = None
        if date_naissance:
            try:
                parsed_date = datetime.strptime(date_naissance, "%Y-%m-%d").date()
            except ValueError:
                return Response({
                    "error": "Format de date invalide. Utilisez YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        stagiaire = Stagiaire.objects.filter(matricule=cin).first()
        if stagiaire:
            # Update existing user
            stagiaire.nom = nom
            stagiaire.prenom = prenom
            stagiaire.date_naissance = parsed_date
            if cin_bytes:
                stagiaire.cin = cin_bytes
                stagiaire.save()
        else:
            # Create new Stagiaire
            stagiaire = Stagiaire.objects.create(
            nom=nom,
            prenom=prenom,
            matricule=cin,
            date_naissance=parsed_date,
            cin=cin_bytes
            )

        return Response({
            "message": "Utilisateur enregistré avec succès!",
            "matricule": stagiaire.matricule
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "error": f"Erreur lors de l'enregistrement: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
