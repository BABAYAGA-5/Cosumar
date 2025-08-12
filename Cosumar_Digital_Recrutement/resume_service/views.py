from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
import os

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
def upload_cin(request):
    """Upload and scan Moroccan CIN (ID card) image"""
    try:
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        cin_file = request.FILES['file']
        
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        file_extension = os.path.splitext(cin_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return Response({
                "error": "Invalid file type. Please upload an image file"
            }, status=status.HTTP_400_BAD_REQUEST)

        stage_id = request.data.get('stage_id')

        if not stage_id:
            return Response({"error": "stage_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        image_bytes = cin_file.read()
        
        try:
            stage = Stage.objects.get(id=stage_id)
            stage.cin = image_bytes
            stage.save()
        except Stage.DoesNotExist:
            return Response({"error": "Stage not found"}, status=status.HTTP_404_NOT_FOUND)

        from .CIN import extract_cin_data
        data = extract_cin_data(image_bytes)

        if data is not {}:
            return Response({
                "message": "CIN scanned successfully",
                "stage_id": stage_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "CIN scan failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            "error": f"CIN processing error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

