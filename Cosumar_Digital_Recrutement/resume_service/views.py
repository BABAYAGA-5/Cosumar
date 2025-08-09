from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status

from resume_service.models import Domaine
from auth_service.models import Utilisateur
import jwt

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
@api_view(['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
@permission_classes([IsAuthenticated])
def test(request):
    return Response({'message': 'Test endpoint is working'}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def domaines(request):
    token = request.headers.get('Authorization')

    return Response({'message': 'Domaines endpoint is working'}, status=status.HTTP_200_OK)
